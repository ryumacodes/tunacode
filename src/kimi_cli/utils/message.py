from kosong.base.message import ContentPart, Message, TextPart
from kosong.tooling import ToolResult, ToolReturnType
from kosong.tooling.error import ToolError


def tool_result_to_messages(tool_result: ToolResult) -> list[Message]:
    """Convert a tool result to a list of messages."""
    if isinstance(tool_result.result, ToolError):
        assert tool_result.result.message
        return [
            Message(
                role="tool",
                content=tool_result.result.message,
                tool_call_id=tool_result.tool_call_id,
            )
        ]

    content = tool_ret_value_to_message_content(tool_result.result)
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


def tool_ret_value_to_message_content(result: ToolReturnType) -> list[ContentPart]:
    """Convert a tool return value to a list of message content parts."""
    match result:
        case str():
            return [TextPart(text=result)]
        case ContentPart():
            return [result]
        case _:
            return list(result)
