#!/usr/bin/env python3
"""
Test both BashTool and RunCommandTool for ESC interrupt functionality.
"""

import trio
import trio_asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from tunacode.core.abort_controller import AbortController, AppContext
from tunacode.tools.bash import BashTool
from tunacode.tools.run_command import RunCommandTool


async def test_tool_esc_interrupt(tool_class, tool_name):
    """Test ESC interrupt for a specific tool."""
    print(f"🧪 Testing {tool_name} ESC interrupt...")
    
    # Create abort controller
    abort_controller = AbortController()
    
    # Create a long-running command that we can interrupt
    long_command = "sleep 5 && echo 'Command completed'"
    
    try:
        # Set up the abort controller with the nursery scope
        with trio.CancelScope() as scope:
            abort_controller.set_cancel_scope(scope)
            
            async with trio.open_nursery() as nursery:
                # Simulate ESC key being pressed after 1 seconds
                async def simulate_esc():
                    await trio.sleep(1)
                    print(f"🔑 {tool_name}: Simulating ESC key press...")
                    abort_controller.abort(trigger="Test ESC")
                
                nursery.start_soon(simulate_esc)
                
                # Try to run the long command
                tool = tool_class()
                print(f"🏃 {tool_name}: Starting command: {long_command}")
                
                if tool_name == "BashTool":
                    result = await tool.execute(long_command, timeout=10)
                else:  # RunCommandTool
                    result = await tool.execute(long_command)
                    
                print(f"❌ {tool_name}: Command completed (should have been cancelled): {result}")
                
        # If we get here and scope was cancelled, that's success
        if scope.cancelled_caught:
            print(f"✅ {tool_name}: Command was successfully cancelled by ESC!")
            return True
            
    except trio.Cancelled:
        print(f"✅ {tool_name}: Command was successfully cancelled by ESC (via exception)!")
        return True
    except Exception as e:
        print(f"❌ {tool_name}: Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print(f"❌ {tool_name}: Command was NOT cancelled by ESC")
    return False


async def test_both_tools():
    """Test both tools for ESC interrupt functionality."""
    print("🚀 Testing ESC interrupt for both tools...")
    
    # Test BashTool
    bash_success = await test_tool_esc_interrupt(BashTool, "BashTool")
    
    print("\n" + "="*50)
    
    # Test RunCommandTool  
    run_cmd_success = await test_tool_esc_interrupt(RunCommandTool, "RunCommandTool")
    
    return bash_success and run_cmd_success


if __name__ == "__main__":
    print("🚀 Starting comprehensive ESC interrupt test...")
    
    async def main():
        # Initialize trio_asyncio
        async with trio_asyncio.open_loop():
            return await test_both_tools()
    
    result = trio.run(main)
    
    if result:
        print("\n🎉 All tests passed! ESC interrupt works for both tools!")
    else:
        print("\n❌ Some tests failed. ESC interrupt is not working properly.")
    
    sys.exit(0 if result else 1)