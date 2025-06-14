#!/usr/bin/env python3
"""Demo script to test the enhanced /thoughts command functionality."""

import asyncio
from tunacode.core.state import StateManager
from tunacode.cli.commands import ThoughtsCommand, CommandContext

async def test_thoughts_command():
    """Test the enhanced thoughts command."""
    # Create state manager
    state_manager = StateManager()
    
    # Create command and context
    thoughts_cmd = ThoughtsCommand()
    context = CommandContext(state_manager=state_manager)
    
    print("Initial state:")
    print(f"show_thoughts: {state_manager.session.show_thoughts}")
    print(f"files_in_context: {state_manager.session.files_in_context}")
    print(f"tool_calls: {state_manager.session.tool_calls}")
    print(f"iteration_count: {state_manager.session.iteration_count}")
    
    # Turn on thoughts
    print("\nTurning thoughts ON...")
    await thoughts_cmd.execute(["on"], context)
    print(f"show_thoughts: {state_manager.session.show_thoughts}")
    
    # Simulate some tracking
    state_manager.session.files_in_context.add("/home/user/test.py")
    state_manager.session.files_in_context.add("/home/user/config.json")
    state_manager.session.tool_calls.append({
        "tool": "read_file",
        "args": {"file_path": "/home/user/test.py"},
        "iteration": 1
    })
    state_manager.session.tool_calls.append({
        "tool": "write_file",
        "args": {"file_path": "/home/user/output.txt", "content": "test"},
        "iteration": 2
    })
    state_manager.session.iteration_count = 2
    
    print("\nAfter simulated activity:")
    print(f"files_in_context: {state_manager.session.files_in_context}")
    print(f"tool_calls: {len(state_manager.session.tool_calls)} calls")
    print(f"iteration_count: {state_manager.session.iteration_count}")
    
    # Turn off thoughts
    print("\nTurning thoughts OFF...")
    await thoughts_cmd.execute(["off"], context)
    print(f"show_thoughts: {state_manager.session.show_thoughts}")

if __name__ == "__main__":
    asyncio.run(test_thoughts_command())