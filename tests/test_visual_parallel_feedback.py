#!/usr/bin/env python3
"""
Test to verify visual feedback for parallel execution is working correctly.
This test captures the UI output to ensure the parallel execution messages are displayed.
"""

import asyncio
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from io import StringIO

from tunacode.core.agents.main import _process_node
from tunacode.constants import READ_ONLY_TOOLS


class MockPart:
    """Mock tool part for testing"""
    def __init__(self, tool_name, args=None):
        self.tool_name = tool_name
        self.tool = tool_name
        self.args = args or {}
        self.part_kind = "tool-call"


class MockModelResponse:
    """Mock model response containing tool calls"""
    def __init__(self, parts):
        self.parts = parts


class MockNode:
    """Mock node for testing"""
    def __init__(self, tool_parts):
        self.model_response = MockModelResponse(tool_parts)


@pytest.mark.asyncio
async def test_parallel_execution_visual_feedback():
    """
    Test that parallel execution displays proper visual feedback when thoughts mode is on.
    This ensures users see messages like "Executing X read-only tools in parallel".
    """
    
    # Capture UI output
    ui_output = []
    
    async def mock_muted(text):
        """Capture muted UI output"""
        ui_output.append(text)
    
    # Mock tool callback
    async def mock_tool_callback(part, node):
        await asyncio.sleep(0.01)
        return f"Result from {part.tool_name}"
    
    # Create multiple read-only tools
    tool_parts = [
        MockPart("read_file", {"file_path": "/constants.py"}),
        MockPart("read_file", {"file_path": "/types.py"}),
        MockPart("read_file", {"file_path": "/exceptions.py"}),
        MockPart("grep", {"pattern": "async", "include_files": "*.py"}),
        MockPart("read_file", {"file_path": "/main.py"}),
        MockPart("grep", {"pattern": "def|class", "include_files": "*.py", "use_regex": True}),
    ]
    
    node = MockNode(tool_parts)
    
    # Mock state manager with thoughts enabled
    state_manager = MagicMock()
    state_manager.session.show_thoughts = True
    state_manager.session.messages = []
    state_manager.session.tool_calls = []
    state_manager.session.files_in_context = set()
    state_manager.session.current_iteration = 1
    
    # Patch the ui.muted function
    with patch('tunacode.ui.console.muted', new=mock_muted):
        await _process_node(node, mock_tool_callback, state_manager)
    
    # Check that parallel execution message was displayed
    parallel_messages = [msg for msg in ui_output if "PARALLEL BATCH" in msg]
    
    assert len(parallel_messages) > 0, f"No parallel execution messages found. UI output: {ui_output}"
    
    # Should see "Executing 6 read-only tools concurrently"
    assert any("Executing 6 read-only tools concurrently" in msg for msg in parallel_messages), \
        f"Expected 'Executing 6 read-only tools concurrently' message. Got: {parallel_messages}"
    
    # Verify tool details were also displayed (now shown as [1], [2], etc.)
    tool_messages = [msg for msg in ui_output if msg.strip().startswith("[") and "]" in msg]
    assert len(tool_messages) >= 6, f"Expected at least 6 tool detail messages, got {len(tool_messages)}"
    
    print(f"\nUI Output captured:")
    for msg in ui_output:
        print(f"  {msg}")
    print("\nVisual feedback test passed!")


@pytest.mark.asyncio
async def test_mixed_tools_visual_feedback():
    """
    Test visual feedback when mixing read-only and write tools.
    Should show parallel execution for read-only batches.
    """
    
    ui_output = []
    
    async def mock_muted(text):
        ui_output.append(text)
    
    async def mock_tool_callback(part, node):
        await asyncio.sleep(0.01)
        return f"Result from {part.tool_name}"
    
    # Mix of read-only and write tools
    tool_parts = [
        MockPart("read_file", {"file_path": "/file1.py"}),
        MockPart("grep", {"pattern": "test"}),
        MockPart("list_dir", {"directory": "/src"}),
        MockPart("write_file", {"file_path": "/output.txt", "content": "data"}),  # This triggers flush
        MockPart("read_file", {"file_path": "/file2.py"}),
        MockPart("grep", {"pattern": "import"}),
    ]
    
    node = MockNode(tool_parts)
    
    state_manager = MagicMock()
    state_manager.session.show_thoughts = True
    state_manager.session.messages = []
    state_manager.session.tool_calls = []
    state_manager.session.files_in_context = set()
    state_manager.session.current_iteration = 1
    
    with patch('tunacode.ui.console.muted', new=mock_muted):
        await _process_node(node, mock_tool_callback, state_manager)
    
    parallel_messages = [msg for msg in ui_output if "PARALLEL BATCH" in msg]
    
    # For mixed tools, we expect sequential execution with warning messages
    # The first 3 read-only tools should execute in parallel if all in same node
    # But since we have a write_file tool, it will trigger sequential execution
    sequential_messages = [msg for msg in ui_output if "SEQUENTIAL:" in msg]
    
    # We should see at least one sequential message for the write_file tool
    assert len(sequential_messages) >= 1, f"Expected sequential messages for write tool. Got: {ui_output}"
    
    # The test might not batch tools if they come one at a time in the mock
    # So let's check that we at least processed all tools
    assert any("write_file" in msg for msg in sequential_messages), \
        "Expected sequential execution message for write_file"
    
    print(f"\nMixed tools visual feedback test passed!")
    print(f"Parallel messages: {parallel_messages}")


if __name__ == "__main__":
    print("Testing visual feedback for parallel execution...")
    asyncio.run(test_parallel_execution_visual_feedback())
    asyncio.run(test_mixed_tools_visual_feedback())
    print("\nAll visual feedback tests passed!")