"""JSON tool call parsing utilities for fallback functionality."""

import json
from datetime import datetime
from typing import Any, Awaitable, Callable, Optional

from tunacode.core.logging.logger import get_logger
from tunacode.core.state import StateManager

logger = get_logger(__name__)

ToolCallback = Callable[[Any, Any], Awaitable[Any]]


async def parse_json_tool_calls(
    text: str, tool_callback: Optional[ToolCallback], state_manager: StateManager
) -> int:
    """
    Parse JSON tool calls from text when structured tool calling fails.
    Fallback for when API providers don't support proper tool calling.

    Returns:
        int: Number of tools successfully executed
    """
    if not tool_callback:
        return 0

    # Pattern for JSON tool calls: {"tool": "tool_name", "args": {...}}
    # Find potential JSON objects and parse them
    potential_jsons = []
    brace_count = 0
    start_pos = -1

    for i, char in enumerate(text):
        if char == "{":
            if brace_count == 0:
                start_pos = i
            brace_count += 1
        elif char == "}":
            brace_count -= 1
            if brace_count == 0 and start_pos != -1:
                potential_json = text[start_pos : i + 1]
                try:
                    parsed = json.loads(potential_json)
                    if isinstance(parsed, dict) and "tool" in parsed and "args" in parsed:
                        potential_jsons.append((parsed["tool"], parsed["args"]))
                except json.JSONDecodeError:
                    logger.debug(
                        f"Failed to parse potential JSON tool call: {potential_json[:50]}..."
                    )
                start_pos = -1

    matches = potential_jsons
    tools_executed = 0

    for tool_name, args in matches:
        try:
            # Create a mock tool call object
            class MockToolCall:
                def __init__(self, tool_name: str, args: dict):
                    self.tool_name = tool_name
                    self.args = args
                    self.tool_call_id = f"fallback_{datetime.now().timestamp()}"

            class MockNode:
                pass

            # Execute the tool through the callback
            mock_call = MockToolCall(tool_name, args)
            mock_node = MockNode()

            await tool_callback(mock_call, mock_node)
            tools_executed += 1

            if state_manager.session.show_thoughts:
                from tunacode.ui import console as ui

                await ui.muted(f"FALLBACK: Executed {tool_name} via JSON parsing")

        except Exception as e:
            if state_manager.session.show_thoughts:
                from tunacode.ui import console as ui

                await ui.error(f"Error executing fallback tool {tool_name}: {str(e)}")

    return tools_executed


async def extract_and_execute_tool_calls(
    text: str, tool_callback: Optional[ToolCallback], state_manager: StateManager
) -> int:
    """
    Extract tool calls from text content and execute them.
    Supports multiple formats for maximum compatibility.

    Returns:
        int: Number of tools successfully executed
    """
    if not tool_callback:
        return 0

    tools_executed = 0

    # First try JSON format
    tools_executed += await parse_json_tool_calls(text, tool_callback, state_manager)

    # Add more formats here if needed in the future

    return tools_executed
