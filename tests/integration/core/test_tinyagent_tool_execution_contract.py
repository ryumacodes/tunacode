from __future__ import annotations

import pytest
from tinyagent.agent_tool_execution import execute_tool_calls
from tinyagent.agent_types import (
    AgentEvent,
    AgentToolResult,
    AssistantMessage,
    MessageEndEvent,
    MessageStartEvent,
    TextContent,
    ToolCallContent,
    ToolExecutionEndEvent,
    ToolExecutionStartEvent,
    ToolResultMessage,
)

from tunacode.tools.decorators import base_tool, to_tinyagent_tool


class _CollectingStream:
    def __init__(self) -> None:
        self.events: list[AgentEvent] = []

    def push(self, event: AgentEvent) -> None:
        self.events.append(event)


@pytest.mark.asyncio
async def test_execute_tool_calls_emits_typed_events_and_tool_result_message(
    mock_no_xml_prompt,
) -> None:
    @base_tool
    async def echo(text: str) -> str:
        return f"echo: {text}"

    tool = to_tinyagent_tool(echo)
    assistant_message = AssistantMessage(
        content=[
            ToolCallContent(
                id="tc-1",
                name=tool.name,
                arguments={"text": "hi"},
            )
        ],
        stop_reason="tool_calls",
        timestamp=None,
    )

    stream = _CollectingStream()
    result = await execute_tool_calls([tool], assistant_message, None, stream)

    assert len(result.tool_results) == 1

    tool_result_message = result.tool_results[0]
    assert isinstance(tool_result_message, ToolResultMessage)
    assert tool_result_message.tool_call_id == "tc-1"
    assert tool_result_message.tool_name == tool.name
    assert tool_result_message.is_error is False

    assert len(tool_result_message.content) == 1
    content_item = tool_result_message.content[0]
    assert isinstance(content_item, TextContent)
    assert content_item.type == "text"
    assert content_item.text == "echo: hi"

    assert len(stream.events) == 4
    start_event, end_event, message_start, message_end = stream.events

    assert isinstance(start_event, ToolExecutionStartEvent)
    assert start_event.tool_call_id == "tc-1"
    assert start_event.tool_name == tool.name
    assert start_event.args == {"text": "hi"}

    assert isinstance(end_event, ToolExecutionEndEvent)
    assert end_event.tool_call_id == "tc-1"
    assert end_event.tool_name == tool.name
    assert end_event.is_error is False

    assert isinstance(end_event.result, AgentToolResult)
    assert len(end_event.result.content) == 1
    end_item = end_event.result.content[0]
    assert isinstance(end_item, TextContent)
    assert end_item.text == "echo: hi"

    assert isinstance(message_start, MessageStartEvent)
    assert isinstance(message_start.message, ToolResultMessage)

    assert isinstance(message_end, MessageEndEvent)
    assert isinstance(message_end.message, ToolResultMessage)


@pytest.mark.asyncio
async def test_execute_tool_calls_surfaces_tool_retry_error_as_is_error(
    mock_no_xml_prompt,
) -> None:
    @base_tool
    async def needs_two(a: int, b: int) -> str:
        return str(a + b)

    tool = to_tinyagent_tool(needs_two)
    assistant_message = AssistantMessage(
        content=[
            ToolCallContent(
                id="tc-1",
                name=tool.name,
                arguments={"a": 1},
            )
        ],
        stop_reason="tool_calls",
        timestamp=None,
    )

    stream = _CollectingStream()
    result = await execute_tool_calls([tool], assistant_message, None, stream)

    assert len(result.tool_results) == 1
    tool_result_message = result.tool_results[0]

    assert tool_result_message.is_error is True
    assert len(tool_result_message.content) == 1

    content_item = tool_result_message.content[0]
    assert isinstance(content_item, TextContent)
    assert isinstance(content_item.text, str)
    assert "Invalid arguments for tool" in content_item.text

    end_event = next(event for event in stream.events if isinstance(event, ToolExecutionEndEvent))
    assert end_event.is_error is True

    assert isinstance(end_event.result, AgentToolResult)
    end_text_item = end_event.result.content[0]
    assert isinstance(end_text_item, TextContent)
    assert isinstance(end_text_item.text, str)
