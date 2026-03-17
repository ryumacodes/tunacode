"""Helper functions for agent operations to reduce code duplication."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Protocol, cast

from tunacode.types.canonical import CanonicalToolCall

from tunacode.core.types.state import StateManagerProtocol

RECENT_TOOL_LIMIT = 3

ToolArgsView = Mapping[str, object]


class EmptyResponseStateView(Protocol):
    sm: StateManagerProtocol
    show_thoughts: bool


def _describe_read_file(tool_args: ToolArgsView) -> str:
    path_value = tool_args.get("file_path", tool_args.get("filepath", ""))
    path = path_value if isinstance(path_value, str) else ""
    return f"Reading `{path}`" if path else "Reading file"


def _coerce_tool_args(value: object) -> ToolArgsView:
    if not isinstance(value, dict):
        return {}
    return {key: raw_value for key, raw_value in value.items() if isinstance(key, str)}


def get_tool_description(tool_name: str, tool_args: ToolArgsView) -> str:
    """Get a descriptive string for a tool call."""
    if tool_name != "read_file":
        return tool_name
    path_value = tool_args.get("file_path", tool_args.get("filepath", ""))
    path = path_value if isinstance(path_value, str) else ""
    return f"{tool_name}('{path}')"


def get_readable_tool_description(tool_name: str, tool_args: ToolArgsView) -> str:
    """Get a human-readable description of a tool operation for batch panel display."""
    if tool_name == "read_file":
        return _describe_read_file(tool_args)
    return f"Executing `{tool_name}`"


def get_recent_tools_context(
    tool_calls: list[CanonicalToolCall], limit: int = RECENT_TOOL_LIMIT
) -> str:
    """Get a context string describing recent tool usage."""
    if not tool_calls:
        return "No tools used yet"

    recent_descriptions = [
        get_tool_description(tool_call.tool_name, _coerce_tool_args(cast(object, tool_call.args)))
        for tool_call in tool_calls[-limit:]
    ]
    return f"Recent tools: {', '.join(recent_descriptions)}"


def create_empty_response_message(
    message: str,
    empty_reason: str,
    tool_calls: list[CanonicalToolCall],
    iteration: int,
) -> str:
    """Create a constructive message for handling empty responses."""
    tools_context = get_recent_tools_context(tool_calls)
    reason = empty_reason if empty_reason != "empty" else "empty"
    return f"""Response appears {reason} or incomplete. Let's troubleshoot and try again.

Task: {message[:200]}...
{tools_context}
Attempt: {iteration}

Please take one of these specific actions:

1. **Search yielded no results?** -> Try alternative search terms or broader patterns
2. **Found what you need?** -> Call the submit tool to finalize
3. **Encountering a blocker?** -> Explain the specific issue preventing progress
4. **Need more context?** -> Use discover or expand your search scope

**Expected in your response:**
- Execute at least one tool OR provide substantial analysis
- If stuck, clearly describe what you've tried and what's blocking you
- Avoid empty responses - the system needs actionable output to proceed

Ready to continue with a complete response."""


async def handle_empty_response(
    message: str,
    reason: str,
    iter_index: int,
    state: EmptyResponseStateView,
) -> str:
    """Build a user-facing notice for empty responses."""
    recent_calls = state.sm.session.runtime.tool_registry.recent_calls(limit=RECENT_TOOL_LIMIT)
    return create_empty_response_message(message, reason, recent_calls, iter_index)
