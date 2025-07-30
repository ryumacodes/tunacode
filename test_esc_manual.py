#!/usr/bin/env python3
"""
Manual test for ESC interrupt functionality.
Run this and press ESC to test if it works properly.
"""

import trio
import trio_asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from tunacode.core.abort_controller import AbortController
from tunacode.tools.bash import BashTool
from tunacode.ui.keybindings import create_key_bindings
from tunacode.core.state import StateManager


async def test_manual_esc():
    """Test ESC interrupt with manual key press detection."""
    print("🧪 Manual ESC interrupt test")
    print("🔧 Run: sleep 10 && echo 'Done'")
    print("⌨️  Press ESC to cancel the command")
    print("⏰ Command will auto-complete in 10 seconds if not cancelled")
    print("")
    
    # Create state manager and abort controller
    state_manager = StateManager()
    abort_controller = AbortController()
    
    # Create app context
    async with trio.open_nursery() as nursery:
        from tunacode.core.abort_controller import AppContext
        app_context = AppContext(nursery, abort_controller)
        state_manager.app_context = app_context
        
        # Set up cancel scope
        with trio.CancelScope() as scope:
            abort_controller.set_cancel_scope(scope)
            
            try:
                # Run the command
                tool = BashTool()
                print("🏃 Starting command...")
                result = await tool.execute("sleep 10 && echo 'Command completed!'", timeout=15)
                print(f"✅ Command completed: {result}")
                
            except trio.Cancelled:
                print("🛑 Command was cancelled by ESC!")
                return True
        
        # Check if scope was cancelled
        if scope.cancelled_caught:
            print("✅ Command was successfully cancelled!")
            return True
            
    print("❌ Command was not cancelled")
    return False


if __name__ == "__main__":
    print("🚀 Starting manual ESC test...")
    print("⚠️  This test requires manual ESC press during command execution")
    
    async def main():
        async with trio_asyncio.open_loop():
            return await test_manual_esc()
    
    try:
        result = trio.run(main)
        if result:
            print("\n🎉 ESC interrupt is working!")
        else:
            print("\n❌ ESC interrupt failed")
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by Ctrl+C")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()