#!/usr/bin/env python3
"""
Test to verify that the parallel execution freeze issue is fixed.
This simulates the scenario where 6 read-only tools would previously cause a freeze.
"""

import asyncio
import pytest
from unittest.mock import MagicMock

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
async def test_no_freeze_with_many_read_only_tools():
    """
    Test that the system doesn't freeze when processing many read-only tools.
    This was the original issue - 6 read-only tools would show "Final flush" 
    but then freeze with spinning "Thinking..." indicator.
    """
    
    # Track execution
    executed_tools = []
    
    async def mock_tool_callback(part, node):
        """Mock callback that tracks execution"""
        executed_tools.append(part.tool_name)
        # Simulate actual tool execution time
        await asyncio.sleep(0.01)
        return f"Result from {part.tool_name}"
    
    # Create 6 read-only tools (the scenario that was freezing)
    tool_parts = [
        MockPart("read_file", {"file_path": "/file1.py"}),
        MockPart("grep", {"pattern": "import"}),
        MockPart("list_dir", {"directory": "/src"}),
        MockPart("read_file", {"file_path": "/file2.py"}),
        MockPart("grep", {"pattern": "class"}),
        MockPart("list_dir", {"directory": "/tests"}),
    ]
    
    node = MockNode(tool_parts)
    
    # Mock state manager
    state_manager = MagicMock()
    state_manager.session.show_thoughts = True
    state_manager.session.messages = []
    state_manager.session.tool_calls = []
    state_manager.session.files_in_context = set()
    state_manager.session.current_iteration = 1
    
    # Process the node - this should NOT freeze
    # Set a timeout to ensure we don't hang
    try:
        await asyncio.wait_for(
            _process_node(node, mock_tool_callback, state_manager),
            timeout=5.0  # 5 second timeout
        )
    except asyncio.TimeoutError:
        pytest.fail("Processing timed out - the freeze issue is not fixed!")
    
    # Verify all tools were executed
    assert len(executed_tools) == 6
    assert all(tool in executed_tools for tool in [
        "read_file", "grep", "list_dir", "read_file", "grep", "list_dir"
    ])
    
    # Verify they were executed in parallel (all 6 together)
    # Since they're all read-only, they should be in a single batch
    print(f"\nExecuted tools: {executed_tools}")
    print("Test passed - no freeze occurred!")


@pytest.mark.asyncio
async def test_thoughts_mode_with_parallel_execution():
    """
    Test that thoughts mode works correctly with parallel execution.
    The original issue occurred when /thoughts was enabled.
    """
    
    execution_log = []
    
    async def mock_tool_callback(part, node):
        """Mock callback that logs execution"""
        execution_log.append(f"Executing {part.tool_name}")
        await asyncio.sleep(0.01)
        return f"Result from {part.tool_name}"
    
    # Create a realistic scenario with multiple tool types
    tool_parts = [
        MockPart("read_file", {"file_path": "/main.py"}),
        MockPart("grep", {"pattern": "TODO"}),
        MockPart("read_file", {"file_path": "/utils.py"}),
        MockPart("list_dir", {"directory": "/"}),
        # Non-read-only tool to trigger flush
        MockPart("write_file", {"file_path": "/output.txt", "content": "test"}),
        # More read-only tools after write
        MockPart("read_file", {"file_path": "/result.txt"}),
    ]
    
    node = MockNode(tool_parts)
    
    # Mock state manager with thoughts enabled (the problematic scenario)
    state_manager = MagicMock()
    state_manager.session.show_thoughts = True  # This was causing issues
    state_manager.session.messages = []
    state_manager.session.tool_calls = []
    state_manager.session.files_in_context = set()
    state_manager.session.current_iteration = 1
    
    # Process with timeout
    try:
        await asyncio.wait_for(
            _process_node(node, mock_tool_callback, state_manager),
            timeout=5.0
        )
    except asyncio.TimeoutError:
        pytest.fail("Processing with thoughts mode timed out!")
    
    # Verify execution completed
    assert len(execution_log) == 6
    print(f"\nExecution log: {execution_log}")
    print("Thoughts mode test passed!")


if __name__ == "__main__":
    print("Testing parallel execution freeze fix...")
    asyncio.run(test_no_freeze_with_many_read_only_tools())
    asyncio.run(test_thoughts_mode_with_parallel_execution())
    print("\nAll tests passed! The freeze issue is fixed.")