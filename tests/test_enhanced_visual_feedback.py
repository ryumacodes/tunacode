#!/usr/bin/env python3
"""
Test enhanced visual feedback for parallel execution.
"""

import asyncio
import pytest
from unittest.mock import MagicMock, patch
from tunacode.core.agents.main import _process_node


class MockPart:
    """Mock tool part for testing"""
    def __init__(self, tool_name, args=None):
        self.tool_name = tool_name
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
async def test_enhanced_parallel_visual_feedback():
    """Test that enhanced visual feedback shows clear batch information."""
    
    ui_output = []
    
    async def mock_muted(text):
        """Capture muted UI output"""
        ui_output.append(text)
    
    async def mock_tool_callback(part, node):
        await asyncio.sleep(0.01)
        return f"Result from {part.tool_name}"
    
    # Create only read-only tools to test parallel batching
    # (When ANY write tool is present, ALL tools execute sequentially)
    tool_parts = [
        # Batch of read-only tools
        MockPart("read_file", {"file_path": "/src/main.py"}),
        MockPart("grep", {"pattern": "async", "include_files": "*.py"}),
        MockPart("list_dir", {"directory": "/tests"}),
        MockPart("read_file", {"file_path": "/src/utils.py"}),
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
    
    # Verify enhanced output format
    output_text = "\n".join(ui_output)
    
    # Check for parallel batch header (without emoji in the header line)
    assert "PARALLEL BATCH: Executing 4 read-only tools concurrently" in output_text
    
    # Check for tool details in batch
    assert "[1] read_file" in output_text
    assert "[2] grep" in output_text
    assert "[3] list_dir" in output_text
    assert "[4] read_file" in output_text
    
    # Check for completion message
    assert "Parallel batch completed in" in output_text
    assert "faster than sequential" in output_text
    
    print("\nEnhanced visual feedback test output:")
    print(output_text)
    print("\nTest passed! Visual feedback is now clearer.")


if __name__ == "__main__":
    asyncio.run(test_enhanced_parallel_visual_feedback())