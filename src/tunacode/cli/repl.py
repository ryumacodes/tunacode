"""Deprecated legacy REPL shim.

The prompt_toolkit + Rich REPL has been replaced by the Textual shell.
This module now provides a thin forwarding wrapper to keep imports stable
while removing prompt_toolkit dependencies. All legacy handlers fail fast.
"""

from __future__ import annotations

from tunacode.cli.textual_repl import run_textual_repl
from tunacode.types import StateManager


async def repl(state_manager: StateManager) -> None:
    """Launch the Textual REPL."""
    await run_textual_repl(state_manager)


async def _tool_handler(*_: object, **__: object) -> None:
    """Legacy tool handler is not supported in the Textual shell."""
    raise RuntimeError("Legacy REPL tool handler is removed; use the Textual tool flow.")


async def process_request(*_: object, **__: object) -> None:
    """Legacy process_request is removed in favor of Textual orchestration."""
    raise RuntimeError("Legacy REPL process_request is removed; use the Textual shell.")
