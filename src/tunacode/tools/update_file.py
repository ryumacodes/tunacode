"""File update tool for agent operations."""

import asyncio
import difflib
import os

from pydantic_ai.exceptions import ModelRetry

from tunacode.tools.decorators import file_tool
from tunacode.tools.utils.text_match import replace


class _FileNotFoundSignal(Exception):
    """Signal that file was not found during sync operation."""

    pass


class _NoChangesSignal(Exception):
    """Signal that replacement resulted in no changes."""

    pass


class _ReplaceError(Exception):
    """Signal that replace() raised ValueError with file preview."""

    pass


def _sync_update_file(filepath: str, old_text: str, new_text: str) -> tuple[str, str]:
    """Synchronous file update - runs in thread pool.

    Returns:
        Tuple of (filepath, diff_text) on success.

    Raises:
        _FileNotFoundSignal: If file does not exist.
        _NoChangesSignal: If replacement results in no changes.
        _ReplaceError: If replace() fails with error message and preview.
    """
    if not os.path.exists(filepath):
        raise _FileNotFoundSignal(filepath)

    with open(filepath, encoding="utf-8") as f:
        original = f.read()

    try:
        new_content = replace(original, old_text, new_text, replace_all=False)
    except ValueError as e:
        lines = original.splitlines()
        preview_lines = min(20, len(lines))
        snippet = "\n".join(lines[:preview_lines])
        raise _ReplaceError(
            f"{e}\n\nFile '{filepath}' preview ({preview_lines} lines):\n---\n{snippet}\n---"
        ) from e

    if original == new_content:
        raise _NoChangesSignal(filepath)

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

    return filepath, diff_text


@file_tool(writes=True)
async def update_file(filepath: str, old_text: str, new_text: str) -> str:
    """Update an existing file by replacing old_text with new_text.

    Args:
        filepath: The path to the file to update.
        old_text: The entire, exact block of text to be replaced.
        new_text: The new block of text to insert.

    Returns:
        A message indicating success and the diff of changes.
    """
    try:
        result_filepath, diff_text = await asyncio.to_thread(
            _sync_update_file, filepath, old_text, new_text
        )
    except _FileNotFoundSignal:
        raise ModelRetry(
            f"File '{filepath}' not found. Cannot update. "
            "Verify the filepath or use `write_file` if it's a new file."
        ) from None
    except _NoChangesSignal:
        raise ModelRetry(
            f"Update old_text found, but replacement resulted in no changes to '{filepath}'. "
            "Was the `old_text` identical to the `new_text`? Please check the file content."
        ) from None
    except _ReplaceError as e:
        raise ModelRetry(str(e)) from None

    return f"File '{result_filepath}' updated successfully.\n\n{diff_text}"
