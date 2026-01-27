"""File update tool for agent operations."""

import asyncio
import difflib
import os
from pathlib import Path

from pydantic_ai.exceptions import ModelRetry

from tunacode.configuration.user_config import load_config
from tunacode.tools.decorators import file_tool
from tunacode.tools.lsp import format_diagnostics, get_diagnostics
from tunacode.tools.utils.text_match import replace

LSP_ORCHESTRATION_OVERHEAD_SECONDS = 1.0


def _is_lsp_enabled() -> bool:
    """Check if LSP is enabled in user config."""
    try:
        config = load_config()
        if config is None:
            return False
        settings = config.get("settings", {})
        lsp_config = settings.get("lsp", {})
        return bool(lsp_config.get("enabled", False))
    except Exception:
        return False


def _get_lsp_timeout() -> float:
    """Get LSP timeout from user config."""
    try:
        config = load_config()
        if config is None:
            return 5.0
        settings = config.get("settings", {})
        lsp_config = settings.get("lsp", {})
        return float(lsp_config.get("timeout", 5.0))
    except Exception:
        return 5.0


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
        raise ModelRetry(
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
        raise ModelRetry(
            f"{e}\n\nFile '{filepath}' preview ({preview_lines} lines):\n---\n{snippet}\n---"
        ) from e

    if original == new_content:
        raise ModelRetry(
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

    # Get LSP diagnostics if enabled
    if _is_lsp_enabled():
        try:
            timeout = _get_lsp_timeout()
            diagnostics = await asyncio.wait_for(
                get_diagnostics(Path(filepath), timeout=timeout),
                timeout=timeout + LSP_ORCHESTRATION_OVERHEAD_SECONDS,
            )
            diagnostics_output = format_diagnostics(diagnostics)
            if diagnostics_output:
                result = f"{diagnostics_output}\n\n{result}"
        except asyncio.TimeoutError:
            pass  # Silently ignore timeout
        except Exception:
            pass  # Silently ignore other errors

    return result
