"""
Module: tunacode.tools.write_file

File writing tool for agent operations in the TunaCode application.
Provides safe file creation with conflict detection and encoding handling.
"""

import os

from pydantic import BaseModel, Field
from pydantic_ai import tool
from pydantic_ai.exceptions import ModelRetry

from tunacode.exceptions import ToolExecutionError
from tunacode.tools.base import FileBasedTool
from tunacode.types import FileContent, FilePath, ToolResult
from tunacode.ui import console as default_ui


class Args(BaseModel, extra="forbid"):
    path: str = Field(..., description="Absolute or relative file path")
    content: str


class WriteFileTool(FileBasedTool):
    """Tool for writing content to new files."""

    @property
    def tool_name(self) -> str:
        return "Write"

    async def _execute(self, filepath: FilePath, content: FileContent) -> ToolResult:
        """Write content to a new file. Fails if the file already exists.

        Args:
            filepath: The path to the file to write to.
            content: The content to write to the file.

        Returns:
            ToolResult: A message indicating success.

        Raises:
            ModelRetry: If the file already exists
            Exception: Any file writing errors
        """
        # Prevent overwriting existing files with this tool.
        if os.path.exists(filepath):
            # Use ModelRetry to guide the LLM
            raise ModelRetry(
                f"File '{filepath}' already exists. "
                "Use the `update_file` tool to modify it, or choose a different filepath."
            )

        # Create directories if they don't exist
        dirpath = os.path.dirname(filepath)
        if dirpath and not os.path.exists(dirpath):
            os.makedirs(dirpath, exist_ok=True)

        with open(filepath, "w", encoding="utf-8") as file:
            file.write(content)

        return f"Successfully wrote to new file: {filepath}"

    def _format_args(self, filepath: FilePath, content: FileContent = None) -> str:
        """Format arguments, truncating content for display."""
        if content is not None and len(content) > 50:
            return f"{repr(filepath)}, content='{content[:47]}...'"
        return super()._format_args(filepath, content)


# Create the function that maintains the existing interface
@tool(name="write_file", args_schema=Args, description="Write new file to disk")
async def write_file(path: FilePath, content: FileContent) -> ToolResult:
    """
    Write content to a new file. Fails if the file already exists.
    Requires confirmation before writing.

    Args:
        filepath (FilePath): The path to the file to write to.
        content (FileContent): The content to write to the file.

    Returns:
        ToolResult: A message indicating the success or failure of the operation.
    """
    tool = WriteFileTool(default_ui)
    try:
        return await tool.execute(path, content)
    except ToolExecutionError as e:
        # Return error message for pydantic-ai compatibility
        return str(e)
