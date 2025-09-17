from kosong.base.message import ContentPart, Message, TextPart
from kosong.tooling import ToolError, ToolOk, ToolResult


def tool_result_to_messages(tool_result: ToolResult) -> list[Message]:
    """Convert a tool result to a list of messages."""
    if isinstance(tool_result.result, ToolError):
        assert tool_result.result.message, "ToolError should have a message"
        return [
            Message(
                role="tool",
                content=tool_result.result.message,
                tool_call_id=tool_result.tool_call_id,
            )
        ]

    content = tool_ok_to_message_content(tool_result.result)
    text_only = True
    for part in content:
        if not isinstance(part, TextPart):
            text_only = False
            break
    if text_only:
        return [
            Message(
                role="tool",
                content=content or "(empty)",
                tool_call_id=tool_result.tool_call_id,
            )
        ]

    return [
        Message(
            role="tool",
            content="Tool called successfully. Result is sent as a user message below.",
            tool_call_id=tool_result.tool_call_id,
        ),
        Message(role="user", content=content),
    ]


def tool_ok_to_message_content(result: ToolOk) -> list[ContentPart]:
    """Convert a tool return value to a list of message content parts."""
    match value := result.value:
        case str():
            return [TextPart(text=value)]
        case ContentPart():
            return [value]
        case _:
            return list(value)


def message_extract_text(message: Message) -> str:
    """Extract text from a message."""
    if isinstance(message.content, str):
        return message.content
    return "\n".join(part.text for part in message.content if isinstance(part, TextPart))
