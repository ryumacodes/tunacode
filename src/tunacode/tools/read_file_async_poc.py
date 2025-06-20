"""
Proof of Concept: Async-optimized read_file tool

This demonstrates how we can make the read_file tool truly async
by using asyncio.to_thread (Python 3.9+) or run_in_executor.
"""

import asyncio
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

from tunacode.constants import (ERROR_FILE_DECODE, ERROR_FILE_DECODE_DETAILS, ERROR_FILE_NOT_FOUND,
                                ERROR_FILE_TOO_LARGE, MAX_FILE_SIZE, MSG_FILE_SIZE_LIMIT)
from tunacode.exceptions import ToolExecutionError
from tunacode.tools.base import FileBasedTool
from tunacode.types import ToolResult

# Shared thread pool for I/O operations
# This avoids creating multiple thread pools
_IO_THREAD_POOL: Optional[ThreadPoolExecutor] = None


def get_io_thread_pool() -> ThreadPoolExecutor:
    """Get or create the shared I/O thread pool."""
    global _IO_THREAD_POOL
    if _IO_THREAD_POOL is None:
        max_workers = min(32, (os.cpu_count() or 1) * 4)
        _IO_THREAD_POOL = ThreadPoolExecutor(
            max_workers=max_workers, thread_name_prefix="tunacode-io"
        )
    return _IO_THREAD_POOL


class AsyncReadFileTool(FileBasedTool):
    """Async-optimized tool for reading file contents."""

    @property
    def tool_name(self) -> str:
        return "Read"

    async def _execute(self, filepath: str) -> ToolResult:
        """Read the contents of a file asynchronously.

        Args:
            filepath: The path to the file to read.

        Returns:
            ToolResult: The contents of the file or an error message.

        Raises:
            Exception: Any file reading errors
        """
        # Check file size first (this is fast)
        try:
            file_size = os.path.getsize(filepath)
        except FileNotFoundError:
            raise FileNotFoundError(f"File not found: {filepath}")

        if file_size > MAX_FILE_SIZE:
            err_msg = ERROR_FILE_TOO_LARGE.format(filepath=filepath) + MSG_FILE_SIZE_LIMIT
            if self.ui:
                await self.ui.error(err_msg)
            raise ToolExecutionError(tool_name=self.tool_name, message=err_msg, original_error=None)

        # Read file asynchronously
        content = await self._read_file_async(filepath)
        return content

    async def _read_file_async(self, filepath: str) -> str:
        """Read file contents without blocking the event loop."""

        # Method 1: Using asyncio.to_thread (Python 3.9+)
        if sys.version_info >= (3, 9):

            def _read_sync():
                with open(filepath, "r", encoding="utf-8") as file:
                    return file.read()

            try:
                return await asyncio.to_thread(_read_sync)
            except Exception:
                # Re-raise to be handled by _handle_error
                raise

        # Method 2: Using run_in_executor (older Python versions)
        else:

            def _read_sync(path):
                with open(path, "r", encoding="utf-8") as file:
                    return file.read()

            loop = asyncio.get_event_loop()
            executor = get_io_thread_pool()

            try:
                return await loop.run_in_executor(executor, _read_sync, filepath)
            except Exception:
                # Re-raise to be handled by _handle_error
                raise

    async def _handle_error(self, error: Exception, filepath: str = None) -> ToolResult:
        """Handle errors with specific messages for common cases.

        Raises:
            ToolExecutionError: Always raised with structured error information
        """
        if isinstance(error, FileNotFoundError):
            err_msg = ERROR_FILE_NOT_FOUND.format(filepath=filepath)
        elif isinstance(error, UnicodeDecodeError):
            err_msg = (
                ERROR_FILE_DECODE.format(filepath=filepath)
                + " "
                + ERROR_FILE_DECODE_DETAILS.format(error=error)
            )
        else:
            # Use parent class handling for other errors
            await super()._handle_error(error, filepath)
            return  # super() will raise, this is unreachable

        if self.ui:
            await self.ui.error(err_msg)

        raise ToolExecutionError(tool_name=self.tool_name, message=err_msg, original_error=error)


# Create the async function that maintains the existing interface
async def read_file_async(filepath: str) -> str:
    """
    Read the contents of a file asynchronously without blocking the event loop.

    This implementation uses thread pool execution to avoid blocking during file I/O,
    allowing true parallel execution of multiple file reads.

    Args:
        filepath: The path to the file to read.

    Returns:
        str: The contents of the file or an error message.
    """
    tool = AsyncReadFileTool(None)  # No UI for pydantic-ai compatibility
    try:
        return await tool.execute(filepath)
    except ToolExecutionError as e:
        # Return error message for pydantic-ai compatibility
        return str(e)


# Benchmarking utilities for testing
async def benchmark_read_performance():
    """Benchmark the performance difference between sync and async reads."""
    import time

    from tunacode.tools.read_file import read_file as read_file_sync

    # Create some test files
    test_files = []
    for i in range(10):
        filepath = f"/tmp/test_file_{i}.txt"
        with open(filepath, "w") as f:
            f.write("x" * 10000)  # 10KB file
        test_files.append(filepath)

    # Test synchronous reads (sequential)
    start_time = time.time()
    for filepath in test_files:
        await read_file_sync(filepath)
    sync_time = time.time() - start_time

    # Test async reads (parallel)
    start_time = time.time()
    tasks = [read_file_async(filepath) for filepath in test_files]
    await asyncio.gather(*tasks)
    async_time = time.time() - start_time

    # Cleanup
    for filepath in test_files:
        os.unlink(filepath)

    print(f"Synchronous reads: {sync_time:.3f}s")
    print(f"Async reads: {async_time:.3f}s")
    print(f"Speedup: {sync_time / async_time:.2f}x")


if __name__ == "__main__":
    # Run benchmark when executed directly
    asyncio.run(benchmark_read_performance())
