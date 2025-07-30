#!/usr/bin/env python3
"""
Test script to demonstrate debug visuals for Trio migration.
"""

import trio
import time
from src.tunacode.debug.trio_debug import trio_debug, debug_trio_function
from src.tunacode.core.abort_controller import AbortController, AppContext

@debug_trio_function("TestRunner")
async def simulate_agent_processing():
    """Simulate agent processing with streaming."""
    trio_debug.streaming_started("test-stream-001")
    
    try:
        for i in range(10):
            trio_debug.log_event("AGENT_CHUNK", "Agent", f"Processing chunk {i+1}/10", "INFO")
            await trio.sleep(0.5)
            
        trio_debug.streaming_stopped("test-stream-001", "completed")
        
    except trio.Cancelled:
        trio_debug.streaming_stopped("test-stream-001", "cancelled")
        raise

@debug_trio_function("TestRunner")
async def simulate_user_input():
    """Simulate user interactions."""
    await trio.sleep(2)
    trio_debug.key_pressed("test-input", "user_typing")
    
    await trio.sleep(3)
    trio_debug.key_pressed("Esc", "abort_operation")
    
    # Simulate abort
    abort_controller = AbortController()
    abort_controller.abort(trigger="Test Esc")

@debug_trio_function("TestRunner")
async def simulate_tool_execution():
    """Simulate tool execution."""
    tools = ["read_file", "grep", "update_file", "bash"]
    
    for tool in tools:
        trio_debug.log_event("TOOL_START", "ToolHandler", f"Executing {tool}", "INFO")
        await trio.sleep(1)
        trio_debug.log_event("TOOL_COMPLETE", "ToolHandler", f"{tool} completed", "SUCCESS")

async def main():
    """Main test function."""
    print("🚀 Starting Trio Debug Visual Test")
    print("This will demonstrate the debug visualization system")
    print("Watch for nurseries, tasks, cancellation, and events!\n")
    
    # Start debug display
    trio_debug.start_live_display()
    trio_debug.log_event("TEST_START", "TestRunner", "Debug visual test started", "SUCCESS")
    
    try:
        async with trio.open_nursery() as nursery:
            # Log nursery creation
            nursery_id = f"test-nursery-{id(nursery)}"
            trio_debug.nursery_created(nursery_id)
            
            # Spawn various test tasks
            trio_debug.task_spawned(nursery_id, "agent_processing", "task-001")
            nursery.start_soon(simulate_agent_processing)
            
            trio_debug.task_spawned(nursery_id, "user_input", "task-002") 
            nursery.start_soon(simulate_user_input)
            
            trio_debug.task_spawned(nursery_id, "tool_execution", "task-003")
            nursery.start_soon(simulate_tool_execution)
            
            # Create some cancel scopes for testing
            with trio.CancelScope(deadline=trio.current_time() + 8) as timeout_scope:
                scope_id = f"timeout-scope-{id(timeout_scope)}"
                trio_debug.cancel_scope_created(scope_id, timeout=8.0)
                
                await trio.sleep(10)  # This should be cancelled by timeout
                
    except trio.Cancelled:
        trio_debug.log_event("TEST_CANCELLED", "TestRunner", "Test cancelled by timeout", "WARNING")
    
    # Show final summary
    await trio.sleep(1)
    trio_debug.log_event("TEST_COMPLETE", "TestRunner", "Debug visual test completed", "SUCCESS")
    
    print("\n" + "="*60)
    print("🎯 Test completed! Debug summary:")
    trio_debug.show_summary()
    
    print("\n✨ Debug visual test finished successfully!")
    print("You can see how the system tracks:")
    print("  • Nursery lifecycle")
    print("  • Task spawning and management") 
    print("  • AbortController operations")
    print("  • CancelScope creation and cancellation")
    print("  • Key press events")
    print("  • Streaming operations")
    print("  • Tool execution")

if __name__ == "__main__":
    trio.run(main)