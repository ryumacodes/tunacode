#!/usr/bin/env python3
"""
Demo test to show parallel tool execution performance improvement.
This test demonstrates the 3x improvement from parallel read-only tool execution.
"""

import asyncio
import time
import pytest
import sys
import os

# Add the src directory to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tunacode.core.agents.main import execute_tools_parallel
from tunacode.constants import READ_ONLY_TOOLS


class MockPart:
    """Mock tool part for testing"""
    def __init__(self, tool_name):
        self.tool_name = tool_name


class MockNode:
    """Mock node for testing"""
    pass


async def mock_slow_tool_callback(part, node):
    """Simulate a slow read-only tool (like file reading or search)"""
    await asyncio.sleep(0.1)  # 100ms delay per tool
    return f"Result from {part.tool_name}"


@pytest.mark.asyncio
async def test_parallel_execution_performance_improvement():
    """Test that demonstrates the 3x performance improvement from parallel execution"""
    
    # Create 3 mock read-only tool calls
    tool_calls = [
        (MockPart("read_file"), MockNode()),
        (MockPart("grep"), MockNode()),
        (MockPart("list_dir"), MockNode()),
    ]
    
    # Test sequential execution (simulated)
    start_time = time.time()
    sequential_results = []
    for part, node in tool_calls:
        result = await mock_slow_tool_callback(part, node)
        sequential_results.append(result)
    sequential_time = time.time() - start_time
    
    # Test parallel execution using TunaCode's parallel function
    start_time = time.time()
    parallel_results = await execute_tools_parallel(tool_calls, mock_slow_tool_callback)
    parallel_time = time.time() - start_time
    
    # Verify results are equivalent
    assert len(sequential_results) == len(parallel_results)
    assert len(parallel_results) == 3
    
    # Verify performance improvement (should be close to 3x faster)
    improvement_ratio = sequential_time / parallel_time
    
    # Allow some tolerance for timing variations in tests
    assert improvement_ratio > 2.5, f"Expected >2.5x improvement, got {improvement_ratio:.2f}x"
    assert improvement_ratio < 4.0, f"Improvement ratio seems too high: {improvement_ratio:.2f}x"
    
    # Verify all tools completed
    for result in parallel_results:
        if isinstance(result, Exception):
            pytest.fail(f"Tool execution failed: {result}")
        assert isinstance(result, str)
        assert "Result from" in result


@pytest.mark.asyncio 
async def test_parallel_execution_with_different_tool_counts():
    """Test parallel execution scales with different numbers of tools"""
    
    test_cases = [1, 2, 3, 5]
    
    for tool_count in test_cases:
        # Create mock tool calls
        tool_calls = [
            (MockPart(f"read_file_{i}"), MockNode())
            for i in range(tool_count)
        ]
        
        # Execute in parallel
        start_time = time.time()
        results = await execute_tools_parallel(tool_calls, mock_slow_tool_callback)
        execution_time = time.time() - start_time
        
        # Verify results
        assert len(results) == tool_count
        
        # Execution time should be roughly the same regardless of tool count
        # (since they run in parallel)
        expected_time = 0.1  # Each tool takes 0.1s, but they run in parallel
        assert execution_time < expected_time + 0.05, f"Expected ~{expected_time}s, got {execution_time:.3f}s for {tool_count} tools"


def print_demo_results():
    """Utility function to print demo results (not a test)"""
    async def demo():
        tool_calls = [
            (MockPart("read_file"), MockNode()),
            (MockPart("grep"), MockNode()), 
            (MockPart("list_dir"), MockNode()),
        ]
        
        print("\n🚀 TunaCode Parallel Tool Execution Demo")
        print("=" * 50)
        
        # Sequential
        print("\n📍 Sequential Execution:")
        start_time = time.time()
        for part, node in tool_calls:
            await mock_slow_tool_callback(part, node)
            print(f"  ✓ {part.tool_name} completed")
        sequential_time = time.time() - start_time
        print(f"⏱️  Sequential time: {sequential_time:.2f}s")
        
        # Parallel  
        print("\n⚡ Parallel Execution:")
        start_time = time.time()
        await execute_tools_parallel(tool_calls, mock_slow_tool_callback)
        parallel_time = time.time() - start_time
        print(f"  ✓ All 3 tools completed simultaneously")
        print(f"⏱️  Parallel time: {parallel_time:.2f}s")
        
        # Results
        improvement = sequential_time / parallel_time
        print(f"\n🎯 Performance Improvement: {improvement:.1f}x faster!")
        print(f"   Sequential: {sequential_time:.2f}s")
        print(f"   Parallel:   {parallel_time:.2f}s")
        print(f"   Saved:      {sequential_time - parallel_time:.2f}s")
    
    if __name__ == "__main__":
        asyncio.run(demo())


# Allow running as script for demo
if __name__ == "__main__":
    print_demo_results() 