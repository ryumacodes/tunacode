"""File update tool for agent operations."""

import difflib
import os
from pathlib import Path

from tunacode.exceptions import ToolRetryError

from tunacode.tools.decorators import file_tool
from tunacode.tools.lsp.diagnostics import maybe_prepend_lsp_diagnostics
from tunacode.tools.utils.text_match import replace


@file_tool
async def update_file(filepath: str, old_text: str, new_text: str) -> str:
    """Update an existing file by replacing old_text with new_text.

    Args:
        filepath: The path to the file to update.
        old_text: The entire, exact block of text to be replaced.
        new_text: The new block of text to insert.

    Returns:
        A message indicating success and the diff of changes.
    """
    if not os.path.exists(filepath):
        raise ToolRetryError(
            f"File '{filepath}' not found. Cannot update. "
            "Verify the filepath or use `write_file` if it's a new file."
        )

    with open(filepath, encoding="utf-8") as f:
        original = f.read()

    try:
        new_content = replace(original, old_text, new_text, replace_all=False)
    except ValueError as e:
        lines = original.splitlines()
        preview_lines = min(20, len(lines))
        snippet = "\n".join(lines[:preview_lines])
        raise ToolRetryError(
            f"{e}\n\nFile '{filepath}' preview ({preview_lines} lines):\n---\n{snippet}\n---"
        ) from e

    if original == new_content:
        raise ToolRetryError(
            f"Update old_text found, but replacement resulted in no changes to '{filepath}'. "
            "Was the `old_text` identical to the `new_text`? Please check the file content."
        )

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(new_content)

    diff_lines = list(
        difflib.unified_diff(
            original.splitlines(keepends=True),
            new_content.splitlines(keepends=True),
            fromfile=f"a/{filepath}",
            tofile=f"b/{filepath}",
        )
    )
    diff_text = "".join(diff_lines)

    result = f"File '{filepath}' updated successfully.\n\n{diff_text}"

    result = await maybe_prepend_lsp_diagnostics(result, Path(filepath))
    return result
