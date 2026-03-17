"""Debug logging helpers for message history sanitization."""

from __future__ import annotations

from tunacode.types import ToolCallId

from tunacode.core.agents.resume.sanitize import (
    AssistantResumeMessage,
    ImageContentItem,
    ResumeMessage,
    SystemResumeMessage,
    TextContentItem,
    ThinkingContentItem,
    ToolCallContentItem,
    ToolResultResumeMessage,
    UserResumeMessage,
    _parse_messages,
)
from tunacode.core.logging import get_logger

DEBUG_PREVIEW_SUFFIX = "..."
DEBUG_NEWLINE_REPLACEMENT = "\\n"
DEBUG_HISTORY_MESSAGE_PREVIEW_LEN = 160
DEBUG_HISTORY_CONTENT_ITEM_PREVIEW_LEN = 140


def _format_debug_preview(value: object, max_len: int) -> tuple[str, int]:
    if value is None:
        return "", 0

    value_text = value if isinstance(value, str) else str(value)
    value_len = len(value_text)
    preview_len = min(max_len, value_len)
    preview_text = value_text[:preview_len]
    if value_len > preview_len:
        preview_text = f"{preview_text}{DEBUG_PREVIEW_SUFFIX}"
    return preview_text.replace("\n", DEBUG_NEWLINE_REPLACEMENT), value_len


def _format_content_item(item: object) -> str:
    if isinstance(item, TextContentItem):
        preview, _ = _format_debug_preview(item.text, DEBUG_HISTORY_CONTENT_ITEM_PREVIEW_LEN)
        return f"type='text' {preview}"
    if isinstance(item, ThinkingContentItem):
        preview, _ = _format_debug_preview(item.thinking, DEBUG_HISTORY_CONTENT_ITEM_PREVIEW_LEN)
        return f"type='thinking' {preview}"
    if isinstance(item, ImageContentItem):
        preview, _ = _format_debug_preview(
            item.url or "[image]", DEBUG_HISTORY_CONTENT_ITEM_PREVIEW_LEN
        )
        return f"type='image' {preview}"
    if isinstance(item, ToolCallContentItem):
        preview, _ = _format_debug_preview(item.arguments, DEBUG_HISTORY_CONTENT_ITEM_PREVIEW_LEN)
        return f"type='tool_call' id={item.tool_call_id!r} name={item.tool_name!r} {preview}"
    return f"<{type(item).__name__}>"


def _content_items_text(items: list[object]) -> str:
    chunks: list[str] = []
    for item in items:
        if isinstance(item, TextContentItem):
            chunks.append(item.text)
        elif isinstance(item, ThinkingContentItem):
            chunks.append(item.thinking)
        elif isinstance(item, ImageContentItem):
            chunks.append(item.url or "[image]")
    return " ".join(chunks)


def _message_text(message: ResumeMessage) -> str:
    if isinstance(message, AssistantResumeMessage):
        return _content_items_text(list(message.content or []))
    if isinstance(message, ToolResultResumeMessage):
        return _content_items_text(list(message.content))
    request_message: UserResumeMessage | SystemResumeMessage = message
    return _content_items_text(list(request_message.content or []))


def _tool_call_ids(message: ResumeMessage) -> set[ToolCallId]:
    if not isinstance(message, AssistantResumeMessage):
        return set()
    return {
        item.tool_call_id for item in message.content or [] if isinstance(item, ToolCallContentItem)
    }


def _tool_return_ids(message: ResumeMessage) -> set[ToolCallId]:
    if not isinstance(message, ToolResultResumeMessage):
        return set()
    return {message.tool_call_id}


def log_message_history_debug(
    messages: list[object],
    user_message: str,
    dangling_tool_call_ids: set[ToolCallId],
) -> None:
    logger = get_logger()
    typed_messages = _parse_messages(messages)

    logger.debug(
        "History dump: "
        f"messages={len(typed_messages)} dangling_tool_calls={len(dangling_tool_call_ids)}"
    )
    if dangling_tool_call_ids:
        logger.debug(f"Dangling tool_call_ids: {sorted(dangling_tool_call_ids)}")

    if user_message:
        preview, message_len = _format_debug_preview(
            user_message, DEBUG_HISTORY_MESSAGE_PREVIEW_LEN
        )
        logger.debug(f"Outgoing user message: {preview} ({message_len} chars)")

    for index, message in enumerate(typed_messages):
        content_preview, content_len = _format_debug_preview(
            _message_text(message),
            DEBUG_HISTORY_MESSAGE_PREVIEW_LEN,
        )
        logger.debug(
            f"history[{index}] role={message.role!r} content={content_preview} "
            f"({content_len} chars) tool_calls={sorted(_tool_call_ids(message))} "
            f"tool_returns={sorted(_tool_return_ids(message))}"
        )

        for item_index, item in enumerate(message.content or []):
            logger.debug(f"history[{index}].content[{item_index}] {_format_content_item(item)}")
