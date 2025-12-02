"""File reading tool for agent operations."""

import asyncio
import os

from tunacode.constants import (
    ERROR_FILE_TOO_LARGE,
    MAX_FILE_SIZE,
    MSG_FILE_SIZE_LIMIT,
)
from tunacode.exceptions import ToolExecutionError
from tunacode.tools.decorators import file_tool


@file_tool
async def read_file(filepath: str) -> str:
    """Read the contents of a file.

    Args:
        filepath: The absolute path to the file to read.

    Returns:
        The contents of the file.
    """
    if os.path.getsize(filepath) > MAX_FILE_SIZE:
        raise ToolExecutionError(
            tool_name="read_file",
            message=ERROR_FILE_TOO_LARGE.format(filepath=filepath) + MSG_FILE_SIZE_LIMIT,
        )

    def _read_sync(path: str) -> str:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    return await asyncio.to_thread(_read_sync, filepath)
