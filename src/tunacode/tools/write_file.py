"""File writing tool for agent operations."""

import os
from pathlib import Path

from tunacode.exceptions import ToolRetryError

from tunacode.tools.decorators import file_tool
from tunacode.tools.lsp.diagnostics import maybe_prepend_lsp_diagnostics


@file_tool
async def write_file(filepath: str, content: str) -> str:
    """Write content to a new file. Fails if the file already exists.

    Args:
        filepath: The absolute path to the file to write.
        content: The content to write to the file.

    Returns:
        A message indicating success, with LSP diagnostics if enabled.
    """
    if os.path.exists(filepath):
        raise ToolRetryError(
            f"File '{filepath}' already exists. "
            "Use the `update_file` tool to modify it, or choose a different filepath."
        )

    dirpath = os.path.dirname(filepath)
    if dirpath and not os.path.exists(dirpath):
        os.makedirs(dirpath, exist_ok=True)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    result = f"Successfully wrote to new file: {filepath}"

    result = await maybe_prepend_lsp_diagnostics(result, Path(filepath))
    return result
