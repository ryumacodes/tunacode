"""Shared exception translation for file-backed tools."""

from __future__ import annotations

from collections.abc import Awaitable
from typing import TypeVar

from tunacode.exceptions import FileOperationError, ToolExecutionError, ToolRetryError

_ResultT = TypeVar("_ResultT")


async def translate_file_tool_errors(
    *,
    tool_name: str,
    filepath: str,
    operation: Awaitable[_ResultT],
) -> _ResultT:
    """Normalize filesystem failures into TunaCode tool exceptions."""
    try:
        return await operation
    except FileNotFoundError as err:
        raise ToolRetryError(f"File not found: {filepath}. Check the path.") from err
    except PermissionError as exc:
        raise FileOperationError(
            operation="access",
            path=filepath,
            message=str(exc),
            original_error=exc,
        ) from exc
    except UnicodeDecodeError as exc:
        raise FileOperationError(
            operation="decode",
            path=filepath,
            message=str(exc),
            original_error=exc,
        ) from exc
    except OSError as exc:
        raise FileOperationError(
            operation="read/write",
            path=filepath,
            message=str(exc),
            original_error=exc,
        ) from exc
    except (ToolRetryError, ToolExecutionError, FileOperationError):
        raise
    except Exception as exc:  # noqa: BLE001
        raise ToolExecutionError(
            tool_name=tool_name,
            message=str(exc),
            original_error=exc,
        ) from exc
