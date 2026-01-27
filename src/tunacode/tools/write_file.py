"""File writing tool for agent operations."""

import asyncio
import os
from pathlib import Path

from pydantic_ai.exceptions import ModelRetry

from tunacode.configuration.user_config import load_config
from tunacode.tools.decorators import file_tool
from tunacode.tools.lsp import format_diagnostics, get_diagnostics

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
async def write_file(filepath: str, content: str) -> str:
    """Write content to a new file. Fails if the file already exists.

    Args:
        filepath: The absolute path to the file to write.
        content: The content to write to the file.

    Returns:
        A message indicating success, with LSP diagnostics if enabled.
    """
    if os.path.exists(filepath):
        raise ModelRetry(
            f"File '{filepath}' already exists. "
            "Use the `update_file` tool to modify it, or choose a different filepath."
        )

    dirpath = os.path.dirname(filepath)
    if dirpath and not os.path.exists(dirpath):
        os.makedirs(dirpath, exist_ok=True)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    result = f"Successfully wrote to new file: {filepath}"

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
