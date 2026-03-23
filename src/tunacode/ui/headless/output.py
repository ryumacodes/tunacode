"""Output extraction for headless mode."""

from __future__ import annotations

from collections.abc import Sequence

from tinyagent.agent_types import AgentMessage, AssistantMessage

from tunacode.core.ui_api.messaging import get_content

TEXT_ATTRIBUTES: tuple[str, ...] = ("output", "text", "content", "message")


def _normalize_text(value: object) -> str | None:
    """Return stripped text for string values, else None."""
    if not isinstance(value, str):
        return None

    stripped = value.strip()
    return stripped or None


def _extract_from_attributes(obj: object) -> str | None:
    """Extract text from common result attributes."""
    for attr in TEXT_ATTRIBUTES:
        normalized = _normalize_text(getattr(obj, attr, None))
        if normalized is not None:
            return normalized
    return None


def _extract_from_result(agent_run: object) -> str | None:
    """Extract text from agent_run.result."""
    result = getattr(agent_run, "result", None)
    if result is None:
        return None

    normalized = _normalize_text(result)
    if normalized is not None:
        return normalized
    if isinstance(result, str):
        return None
    return _extract_from_attributes(result)


def _extract_from_messages(messages: Sequence[AgentMessage]) -> str | None:
    """Extract text from the latest assistant message in messages."""
    for message in reversed(messages):
        if not isinstance(message, AssistantMessage):
            continue

        content = get_content(message)
        normalized = _normalize_text(content)
        if normalized is not None:
            return normalized

    return None


def resolve_output(agent_run: object, messages: Sequence[AgentMessage]) -> str | None:
    """Resolve headless output from agent run or messages.

    Priority:
    1. agent_run.result (direct result)
    2. Latest assistant message content (fallback)

    Returns:
        Extracted text or None if no output found.
    """
    result = _extract_from_result(agent_run)
    if result is not None:
        return result

    return _extract_from_messages(messages)
