#!/usr/bin/env python3
"""
Test script to reproduce and verify the ESC interrupt issue with command execution.
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


async def test_esc_interrupt_with_long_command():
    """Test that ESC can interrupt a long-running command."""
    print("🧪 Testing ESC interrupt with long commands...")
    
    # Create abort controller
    abort_controller = AbortController()
    
    # Create a long-running command that we can interrupt
    long_command = "sleep 10 && echo 'Command completed'"
    
    try:
        # Set up the abort controller with the nursery scope
        with trio.CancelScope() as scope:
            abort_controller.set_cancel_scope(scope)
            
            async with trio.open_nursery() as nursery:
                # Simulate ESC key being pressed after 2 seconds
                async def simulate_esc():
                    await trio.sleep(2)
                    print("\n🔑 Simulating ESC key press...")
                    abort_controller.abort(trigger="Test ESC")
                
                nursery.start_soon(simulate_esc)
                
                # Try to run the long command
                tool = BashTool()
                print(f"🏃 Starting command: {long_command}")
                result = await tool.execute(long_command, timeout=15)
                print(f"❌ Command completed (should have been cancelled): {result}")
                
        # If we get here and scope was cancelled, that's success
        if scope.cancelled_caught:
            print("✅ Command was successfully cancelled by ESC (via scope)!")
            return True
            
    except trio.Cancelled:
        print("✅ Command was successfully cancelled by ESC (via exception)!")
        return True
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("❌ Command was NOT cancelled by ESC")
    return False


async def test_current_behavior():
    """Test the current behavior to confirm the issue exists."""
    print("🔍 Testing current behavior...")
    
    success = await test_esc_interrupt_with_long_command()
    
    if success:
        print("✅ ESC interrupt is working!")
    else:
        print("❌ ESC interrupt is NOT working - need to fix this")
    
    return success


if __name__ == "__main__":
    print("🚀 Starting ESC interrupt test...")
    
    async def main():
        # Initialize trio_asyncio
        async with trio_asyncio.open_loop():
            return await test_current_behavior()
    
    result = trio.run(main)
    
    if result:
        print("\n✅ ESC interrupt is working properly!")
    else:
        print("\n🔧 ESC interrupt is not working.")
        print("   Commands cannot be interrupted with ESC key.")
    
    sys.exit(0 if result else 1)