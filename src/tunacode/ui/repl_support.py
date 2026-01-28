"""Support helpers for the Textual REPL app.

This module exists to keep `tunacode.ui.app` focused on UI composition and lifecycle
while hosting small, testable helpers and callback builders.
"""

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING, Protocol

from rich.console import Console
from rich.text import Text

from tunacode.core.constants import MAX_CALLBACK_CONTENT
from tunacode.core.shared_types import (
    ToolArgs,
    ToolCallback,
    ToolName,
    ToolResultCallback,
    ToolStartCallback,
)
from tunacode.core.state import StateManager

from tunacode.ui.widgets import ToolResultDisplay

COLLAPSE_THRESHOLD: int = 10

FILE_EDIT_TOOLS: frozenset[str] = frozenset({"write_file", "update_file"})

USER_MESSAGE_PREFIX: str = "│ "
DEFAULT_USER_MESSAGE_WIDTH: int = 80
DIAGNOSTICS_BLOCK_START: str = "<file_diagnostics>"
DIAGNOSTICS_BLOCK_END: str = "</file_diagnostics>"
DIAGNOSTICS_BLOCK_PATTERN: str = f"{DIAGNOSTICS_BLOCK_START}.*?{DIAGNOSTICS_BLOCK_END}"
DIAGNOSTICS_BLOCK_RE = re.compile(DIAGNOSTICS_BLOCK_PATTERN, re.DOTALL)
CALLBACK_TRUNCATION_NOTICE: str = "\n... [truncated for safety]"
CALLBACK_TRUNCATION_NOTICE_LEN: int = len(CALLBACK_TRUNCATION_NOTICE)

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from pydantic_ai.messages import ToolCallPart
    from pydantic_ai.result import StreamedRunResult


def _format_prefixed_wrapped_lines(
    lines: list[tuple[str, str]],
    *,
    width: int,
) -> Text:
    effective_width = width if width > 0 else DEFAULT_USER_MESSAGE_WIDTH
    content_width = max(1, effective_width - len(USER_MESSAGE_PREFIX))
    console = Console(width=content_width, color_system=None, force_terminal=False)

    block = Text()
    for line_text, line_style in lines:
        wrapped_lines = Text(line_text, style=line_style, overflow="fold").wrap(
            console, content_width
        )
        for wrapped in wrapped_lines:
            block.append(USER_MESSAGE_PREFIX, style=line_style)
            block.append_text(wrapped)
            block.append("\n")
    return block


def format_user_message(text: str, style: str, *, width: int) -> Text:
    """Format user text with left gutter prefix and hard-wrap for terminal width."""
    lines = text.splitlines() or [""]
    styled_lines = [(line, style) for line in lines]
    return _format_prefixed_wrapped_lines(styled_lines, width=width)


def format_collapsed_message(text: str, style: str, *, width: int) -> Text:
    """Format long pasted text with a collapsed middle section.

    Shows first 3 lines, collapse indicator, and last 2 lines.
    """
    lines = text.splitlines()
    line_count = max(1, len(lines))

    if line_count <= COLLAPSE_THRESHOLD:
        return format_user_message(text, style, width=width)

    collapsed = line_count - 5

    render_lines: list[tuple[str, str]] = [(line, style) for line in lines[:3]]
    render_lines.append((f"[[ {collapsed} more lines ]]", f"dim {style}"))
    render_lines.extend((line, style) for line in lines[-2:])
    return _format_prefixed_wrapped_lines(render_lines, width=width)


class StatusBarLike(Protocol):
    def add_edited_file(self, filepath: str) -> None: ...

    def update_last_action(self, tool_name: str) -> None: ...

    def update_running_action(self, tool_name: str) -> None: ...


class AppForCallbacks(Protocol):
    status_bar: StatusBarLike

    def post_message(self, message: ToolResultDisplay) -> bool: ...

    def update_lsp_for_file(self, filepath: str) -> None: ...


def build_textual_tool_callback() -> ToolCallback:
    async def _callback(
        _part: ToolCallPart,
        _node: StreamedRunResult[None, str],
    ) -> None:
        return None

    return _callback


def _truncate_for_safety(content: str | None) -> str | None:
    """Emergency truncation - prevents UI freeze on massive outputs."""
    if content is None:
        return None
    if len(content) <= MAX_CALLBACK_CONTENT:
        return content

    diagnostics_match = DIAGNOSTICS_BLOCK_RE.match(content)
    if diagnostics_match is None:
        if content.startswith(DIAGNOSTICS_BLOCK_START):
            logger.warning("Diagnostics block missing closing tag; truncating content.")
        truncation_limit = MAX_CALLBACK_CONTENT - CALLBACK_TRUNCATION_NOTICE_LEN
        return content[:truncation_limit] + CALLBACK_TRUNCATION_NOTICE

    diagnostics_block = diagnostics_match.group(0)
    remaining_content = content[len(diagnostics_block) :]
    diagnostics_len = len(diagnostics_block)
    remaining_budget = MAX_CALLBACK_CONTENT - diagnostics_len - CALLBACK_TRUNCATION_NOTICE_LEN

    if remaining_budget <= 0:
        logger.warning("Diagnostics block exceeds safety limit; truncating remainder.")
        return diagnostics_block + CALLBACK_TRUNCATION_NOTICE

    truncated_remainder = remaining_content[:remaining_budget]
    truncated_result = f"{diagnostics_block}{truncated_remainder}{CALLBACK_TRUNCATION_NOTICE}"
    return truncated_result


def build_tool_result_callback(app: AppForCallbacks) -> ToolResultCallback:
    def _callback(
        tool_name: ToolName,
        status: str,
        args: ToolArgs,
        result: str | None = None,
        duration_ms: float | None = None,
    ) -> None:
        if tool_name in FILE_EDIT_TOOLS and status == "completed":
            filepath = args.get("filepath")
            if filepath:
                app.status_bar.add_edited_file(filepath)
                app.update_lsp_for_file(filepath)

        app.status_bar.update_last_action(tool_name)

        safe_result = _truncate_for_safety(result)

        app.post_message(
            ToolResultDisplay(
                tool_name=tool_name,
                status=status,
                args=args,
                result=safe_result,
                duration_ms=duration_ms,
            )
        )

    return _callback


def build_tool_start_callback(app: AppForCallbacks) -> ToolStartCallback:
    """Build callback for tool start notifications."""

    def _callback(tool_name: ToolName) -> None:
        app.status_bar.update_running_action(tool_name)

    return _callback


async def run_textual_repl(state_manager: StateManager, show_setup: bool = False) -> None:
    from tunacode.ui.app import TextualReplApp

    app = TextualReplApp(state_manager=state_manager, show_setup=show_setup)
    await app.run_async()
