"""
Unit tests for parallel tool execution logic.
"""

import asyncio
import time
from unittest.mock import AsyncMock, Mock, patch
import pytest
from tunacode.core.agents.main import execute_tools_parallel, batch_read_only_tools
from tunacode.constants import TOOL_READ_FILE, TOOL_GREP, TOOL_LIST_DIR, TOOL_WRITE_FILE


@pytest.mark.asyncio
async def test_execute_tools_parallel_runs_concurrently():
    """Test that execute_tools_parallel runs tools concurrently."""
    execution_order = []
    results_map = {}
    
    async def mock_callback(part, node):
        tool_name = part.tool_name
        execution_order.append(f"start_{tool_name}")
        await asyncio.sleep(0.1)
        execution_order.append(f"end_{tool_name}")
        result = f"result_{tool_name}"
        results_map[tool_name] = result
        return result
    
    # Create mock parts
    mock_parts = [
        Mock(tool_name="1", args={}),
        Mock(tool_name="2", args={}),
        Mock(tool_name="3", args={}),
    ]
    
    tool_calls = [(part, Mock()) for part in mock_parts]
    
    start_time = time.time()
    results = await execute_tools_parallel(tool_calls, mock_callback)
    elapsed = time.time() - start_time
    
    # Should complete in ~0.1s, not 0.3s
    assert elapsed < 0.15, f"Expected parallel execution, but took {elapsed:.2f}s"
    
    # All should start before any finish
    assert execution_order[:3] == ["start_1", "start_2", "start_3"]
    assert set(execution_order[3:]) == {"end_1", "end_2", "end_3"}
    
    # Results should be in order
    assert results == ["result_1", "result_2", "result_3"]


@pytest.mark.asyncio
async def test_execute_tools_parallel_handles_exceptions():
    """Test that execute_tools_parallel handles exceptions gracefully."""
    
    async def mock_callback(part, node):
        if part.tool_name == "failure":
            raise ValueError("Tool failed")
        return f"success_{part.tool_name}"
    
    # Create mock parts
    mock_parts = [
        Mock(tool_name="1", args={}),
        Mock(tool_name="failure", args={}),
        Mock(tool_name="3", args={}),
    ]
    
    tool_calls = [(part, Mock()) for part in mock_parts]
    
    results = await execute_tools_parallel(tool_calls, mock_callback)
    
    # Should return results with exceptions
    assert len(results) == 3
    assert results[0] == "success_1"
    assert isinstance(results[1], Exception)
    assert str(results[1]) == "Tool failed"
    assert results[2] == "success_3"


def test_batch_read_only_tools_separates_correctly():
    """Test that batch_read_only_tools correctly separates read-only from other tools."""
    
    tool_calls = [
        Mock(tool_name=TOOL_READ_FILE, args={"filepath": "file1.py"}),
        Mock(tool_name=TOOL_GREP, args={"pattern": "test"}),
        Mock(tool_name=TOOL_WRITE_FILE, args={"filepath": "out.txt"}),
        Mock(tool_name=TOOL_LIST_DIR, args={"path": "/tmp"}),
        Mock(tool_name=TOOL_READ_FILE, args={"filepath": "file2.py"}),
    ]
    
    batches = list(batch_read_only_tools(tool_calls))
    
    # Should create 3 batches
    assert len(batches) == 3
    
    # First batch: read-only tools
    assert len(batches[0]) == 2
    assert batches[0][0].tool_name == TOOL_READ_FILE
    assert batches[0][1].tool_name == TOOL_GREP
    
    # Second batch: write tool (alone)
    assert len(batches[1]) == 1
    assert batches[1][0].tool_name == TOOL_WRITE_FILE
    
    # Third batch: remaining read-only tools
    assert len(batches[2]) == 2
    assert batches[2][0].tool_name == TOOL_LIST_DIR
    assert batches[2][1].tool_name == TOOL_READ_FILE


def test_batch_read_only_tools_preserves_order_within_batches():
    """Test that tool order is preserved within each batch."""
    
    tool_calls = [
        Mock(tool_name=TOOL_READ_FILE, args={"filepath": "a.py"}),
        Mock(tool_name=TOOL_READ_FILE, args={"filepath": "b.py"}),
        Mock(tool_name=TOOL_READ_FILE, args={"filepath": "c.py"}),
    ]
    
    batches = list(batch_read_only_tools(tool_calls))
    
    assert len(batches) == 1
    assert len(batches[0]) == 3
    assert batches[0][0].args["filepath"] == "a.py"
    assert batches[0][1].args["filepath"] == "b.py"
    assert batches[0][2].args["filepath"] == "c.py"


def test_batch_read_only_tools_handles_no_tools():
    """Test that batch_read_only_tools handles empty input."""
    
    batches = list(batch_read_only_tools([]))
    assert batches == []


def test_batch_read_only_tools_handles_only_write_tools():
    """Test that batch_read_only_tools handles only write/execute tools."""
    
    tool_calls = [
        Mock(tool_name=TOOL_WRITE_FILE, args={"filepath": "out1.txt"}),
        Mock(tool_name=TOOL_WRITE_FILE, args={"filepath": "out2.txt"}),
    ]
    
    batches = list(batch_read_only_tools(tool_calls))
    
    # Each write tool should be in its own batch
    assert len(batches) == 2
    assert len(batches[0]) == 1
    assert len(batches[1]) == 1