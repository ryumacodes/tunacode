"""Tool decorators providing error handling and logging.

This module provides decorators that wrap tool functions with:
- Consistent error handling (converts exceptions to ToolExecutionError)
- Logging of tool invocations
- File-specific error handling for file operations
"""

import logging
from functools import wraps
from typing import Callable, TypeVar

from pydantic_ai.exceptions import ModelRetry

from tunacode.exceptions import FileOperationError, ToolExecutionError

T = TypeVar("T")
logger = logging.getLogger(__name__)


def base_tool(func: Callable[..., T]) -> Callable[..., T]:
    """Wrap tool with error handling.

    Converts uncaught exceptions to ToolExecutionError while preserving
    ModelRetry and ToolExecutionError pass-through.

    Args:
        func: Async tool function to wrap

    Returns:
        Wrapped function with error handling
    """

    @wraps(func)
    async def wrapper(*args, **kwargs) -> T:
        try:
            logger.info(f"{func.__name__}({args}, {kwargs})")
            return await func(*args, **kwargs)
        except ModelRetry:
            raise  # Let pydantic-ai handle retries
        except ToolExecutionError:
            raise  # Already formatted
        except FileOperationError:
            raise  # Already formatted
        except Exception as e:
            logger.exception(f"{func.__name__} failed")
            raise ToolExecutionError(
                tool_name=func.__name__, message=str(e), original_error=e
            )

    return wrapper


def file_tool(func: Callable[..., T]) -> Callable[..., T]:
    """Wrap file tool with path-specific error handling.

    Provides specialized handling for common file operation errors:
    - FileNotFoundError -> ModelRetry (allows LLM to correct path)
    - PermissionError -> FileOperationError
    - UnicodeDecodeError -> FileOperationError
    - IOError/OSError -> FileOperationError

    Args:
        func: Async file tool function to wrap. First argument must be filepath.

    Returns:
        Wrapped function with file-specific error handling
    """

    @wraps(func)
    async def wrapper(filepath: str, *args, **kwargs) -> T:
        try:
            return await func(filepath, *args, **kwargs)
        except FileNotFoundError:
            raise ModelRetry(f"File not found: {filepath}. Check the path.")
        except PermissionError as e:
            raise FileOperationError(
                filepath=filepath, operation="access", original_error=e
            )
        except UnicodeDecodeError as e:
            raise FileOperationError(
                filepath=filepath, operation="decode", original_error=e
            )
        except (IOError, OSError) as e:
            raise FileOperationError(
                filepath=filepath, operation="read/write", original_error=e
            )

    return base_tool(wrapper)
