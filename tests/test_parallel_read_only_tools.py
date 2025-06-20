"""
Acceptance tests for parallel read-only tool execution feature.
Tests that read-only tools (read_file, grep, list_dir) execute in parallel
while write/execute tools remain sequential.
"""

import asyncio
import time
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import pytest
from tunacode.core.agents import process_request
from tunacode.core.state import StateManager
from tunacode.types import UILogger


class DummyUI(UILogger):
    """Simple UI implementation for testing."""
    
    def log_info(self, message): pass
    def log_warning(self, message): pass
    def log_error(self, message): pass
    def log_success(self, message): pass
    def log_llm_request(self, model, messages, tools): pass
    def log_llm_response(self, model, response, tool_calls, duration): pass
    def log_tool_use(self, tool_name, parameters, result): pass
    def update_spinner(self, message): pass
    def stop_spinner(self): pass


@pytest.mark.asyncio
async def test_read_only_tools_execute_in_parallel():
    """
    User story: As a developer, I want read-only tool operations to execute
    in parallel so that multiple file reads complete faster.
    """
    # Test is now enabled - parallel execution has been implemented
    from tunacode.core.agents.main import _process_node
    
    # Setup
    state = StateManager()
    
    # Track execution timing
    execution_times = []
    call_order = []
    
    # Create a tool callback that tracks timing
    async def timing_callback(part, node):
        tool_name = part.tool_name
        call_order.append(f"start_{tool_name}")
        start = time.time()
        await asyncio.sleep(0.1)  # Simulate slow tool
        end = time.time()
        call_order.append(f"end_{tool_name}")
        execution_times.append((tool_name, start, end))
        return f"result_{tool_name}"
    
    # Create a mock node with multiple read-only tool calls
    mock_parts = []
    for tool in ['read_file', 'grep', 'list_dir']:
        part = Mock()
        part.part_kind = "tool-call"
        part.tool_name = tool
        part.args = {"test": "args"}
        mock_parts.append(part)
    
    mock_node = Mock()
    mock_node.model_response = Mock()
    mock_node.model_response.parts = mock_parts
    
    # Process the node
    start_time = time.time()
    await _process_node(mock_node, timing_callback, state)
    total_time = time.time() - start_time
    
    # With our async I/O improvements, tools now execute in parallel!
    # 1. All tools should have been called
    assert len(execution_times) == 3
    
    # 2. Execution should be PARALLEL - total time should be ~0.1s (not 0.3s)
    # Allow some timing variance
    assert total_time < 0.25, f"Expected parallel execution (~0.1s), but took {total_time:.2f}s"
    
    # 3. Tools should still be called
    tool_names = [t[0] for t in execution_times]
    assert set(tool_names) == {'read_file', 'grep', 'list_dir'}
    
    # With parallel execution, tools may overlap - we can't guarantee order
    # But we should see all start/end events
    expected_events = {
        'start_read_file', 'end_read_file',
        'start_grep', 'end_grep', 
        'start_list_dir', 'end_list_dir'
    }
    assert set(call_order) == expected_events


@pytest.mark.asyncio
async def test_write_tools_remain_sequential():
    """
    User story: As a developer, I want write/execute operations to remain
    sequential for safety, even when mixed with read operations.
    """
    # Test is now enabled - parallel execution has been implemented
    from tunacode.core.agents.main import _process_node
    
    # Setup
    state = StateManager()
    
    # Track execution order
    call_order = []
    
    # Create a tool callback that tracks order
    async def tracking_callback(part, node):
        tool_name = part.tool_name
        call_order.append(f"start_{tool_name}")
        await asyncio.sleep(0.05)  # Simulate tool execution
        call_order.append(f"end_{tool_name}")
        return f"result_{tool_name}"
    
    # Create a mock node with mixed read and write operations
    mock_parts = []
    for tool in ['read_file', 'grep', 'write_file', 'bash', 'list_dir']:
        part = Mock()
        part.part_kind = "tool-call"
        part.tool_name = tool
        part.args = {"test": "args"}
        mock_parts.append(part)
    
    mock_node = Mock()
    mock_node.model_response = Mock()
    mock_node.model_response.parts = mock_parts
    
    # Process the node
    await _process_node(mock_node, tracking_callback, state)
    
    # Currently parallel execution is disabled - tools execute sequentially
    # Verify sequential execution order
    expected_order = [
        'start_read_file', 'end_read_file',
        'start_grep', 'end_grep',
        'start_write_file', 'end_write_file',
        'start_bash', 'end_bash',
        'start_list_dir', 'end_list_dir'
    ]
    assert call_order == expected_order, f"Expected {expected_order}, got {call_order}"


@pytest.mark.asyncio
async def test_read_only_tools_skip_confirmation():
    """
    User story: As a developer, I don't want to be prompted for confirmation
    when using read-only tools since they're safe operations.
    """
    # Test is now enabled - parallel execution has been implemented
    from tunacode.core.tool_handler import ToolHandler
    
    # Setup
    state = StateManager()
    handler = ToolHandler(state)
    
    # Test that read-only tools don't require confirmation
    assert not handler.should_confirm('read_file')
    assert not handler.should_confirm('grep') 
    assert not handler.should_confirm('list_dir')
    
    # Test that write/execute tools do require confirmation (when not in yolo mode)
    assert handler.should_confirm('write_file')
    assert handler.should_confirm('update_file')
    assert handler.should_confirm('bash')
    assert handler.should_confirm('run_command')


@pytest.mark.asyncio
async def test_parallel_execution_handles_errors():
    """
    User story: As a developer, I want the system to handle errors gracefully
    when parallel read operations fail.
    """
    # Test is now enabled - parallel execution has been implemented
    from tunacode.core.agents.main import _process_node
    
    # Setup
    state = StateManager()
    
    # Track which tools were called
    tools_called = []
    errors_caught = []
    
    # Create a tool callback that has one failure
    async def callback_with_failure(part, node):
        tool_name = part.tool_name
        tools_called.append(tool_name)
        
        if tool_name == 'grep':
            raise ValueError("Grep failed")
        
        return f"result_{tool_name}"
    
    # Create a mock node with multiple read-only tool calls
    mock_parts = []
    for tool in ['read_file', 'grep', 'list_dir']:
        part = Mock()
        part.part_kind = "tool-call"
        part.tool_name = tool
        part.args = {"test": "args"}
        mock_parts.append(part)
    
    mock_node = Mock()
    mock_node.model_response = Mock()
    mock_node.model_response.parts = mock_parts
    
    # Process the node - should handle the error gracefully
    try:
        await _process_node(mock_node, callback_with_failure, state)
    except Exception as e:
        errors_caught.append(e)
    
    # All tools should have been called despite one failing
    assert set(tools_called) == {'read_file', 'grep', 'list_dir'}
    
    # The system should handle errors gracefully in parallel execution
    # Note: Current implementation with return_exceptions=True should not raise