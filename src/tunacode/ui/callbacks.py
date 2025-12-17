"""Callback factory functions for TextualReplApp."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from tunacode.constants import MAX_CALLBACK_CONTENT
from tunacode.tools.authorization.handler import ToolHandler
from tunacode.ui.widgets import ToolResultDisplay

if TYPE_CHECKING:
    from tunacode.types import StateManager

    from .app import TextualReplApp

FILE_EDIT_TOOLS = frozenset({"write_file", "update_file"})


def _truncate_for_safety(content: str | None) -> str | None:
    """Emergency truncation - prevents UI freeze on massive outputs."""
    if content is None:
        return None
    if len(content) <= MAX_CALLBACK_CONTENT:
        return content
    return content[:MAX_CALLBACK_CONTENT] + "\n... [truncated for safety]"


def build_textual_tool_callback(app: TextualReplApp, state_manager: StateManager):
    async def _callback(part: Any, _node: Any = None) -> None:
        tool_handler = state_manager.tool_handler or ToolHandler(state_manager)
        state_manager.set_tool_handler(tool_handler)

        if not tool_handler.should_confirm(part.tool_name):
            return

        from tunacode.exceptions import UserAbortError
        from tunacode.utils.parsing.command_parser import parse_args

        args = parse_args(part.args)
        request = tool_handler.create_confirmation_request(part.tool_name, args)
        response = await app.request_tool_confirmation(request)
        if not tool_handler.process_confirmation(response, part.tool_name):
            raise UserAbortError("User aborted tool execution")

    return _callback


def build_tool_result_callback(app: TextualReplApp):
    def _callback(
        tool_name: str,
        status: str,
        args: dict,
        result: str | None = None,
        duration_ms: float | None = None,
    ) -> None:
        if tool_name in FILE_EDIT_TOOLS and status == "completed":
            filepath = args.get("filepath")
            if filepath:
                app.status_bar.add_edited_file(filepath)

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


def build_tool_start_callback(app: TextualReplApp) -> Callable[[str], None]:
    """Build callback for tool start notifications."""

    def _callback(tool_name: str) -> None:
        app.status_bar.update_running_action(tool_name)

    return _callback


def build_tool_progress_callback(app: TextualReplApp) -> Callable[[str, str, int, int], None]:
    """Build callback for subagent tool progress notifications."""

    def _callback(subagent: str, operation: str, current: int, total: int) -> None:
        app.status_bar.update_subagent_progress(subagent, operation, current, total)

    return _callback
