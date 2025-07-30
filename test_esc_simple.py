#!/usr/bin/env python3
"""Simple test for ESC cancellation behavior."""

import asyncio
import sys
import os
sys.path.insert(0, 'src')

try:
    import trio
    import trio_asyncio
    from tunacode.core.state import StateManager
    from tunacode.core.abort_controller import AppContext, AbortController
    from tunacode.tools.bash import BashTool
    
    async def test_esc_cancel():
        print("Testing ESC cancellation with current implementation...")
        
        # Set up state manager like the real app
        state_manager = StateManager()
        abort_controller = AbortController()
        
        # Create bash tool
        bash_tool = BashTool()
        
        print("Testing cancellation behavior...")
        print("Running: sleep 3")
        
        async with trio.open_nursery() as nursery:
            # Set up app context with the nursery
            app_context = AppContext(nursery, abort_controller)
            state_manager.app_context = app_context
            
            try:
                with trio.CancelScope() as scope:
                    app_context.abort_controller.set_cancel_scope(scope)
                    
                    # Simulate the ESC key being pressed after 1 second
                    async def simulate_esc():
                        await trio.sleep(1)
                        print("\\n🔴 Simulating ESC key press...")
                        state_manager.signal_interrupt()
                        await trio.sleep(0.1)  # Give time for abort to propagate
                    
                    nursery.start_soon(simulate_esc)
                    result = await bash_tool._execute(
                        "sleep 3",
                        cwd=".",
                        env={},
                        timeout=5,
                        capture_output=True
                    )
                    print(f"Command completed: {result}")
                        
            except trio.Cancelled:
                print("✅ Command was successfully cancelled!")
            except Exception as e:
                print(f"❌ Error: {e}")
    
    # Run with trio-asyncio context like main.py
    async def main():
        async with trio_asyncio.open_loop():
            await test_esc_cancel()
    
    if __name__ == "__main__":
        trio.run(main)
        
except ImportError as e:
    print(f"Import error: {e}")
    print("Please run from TunaCode virtual environment")