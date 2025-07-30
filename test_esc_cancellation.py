#!/usr/bin/env python3
"""
Direct test of Esc key cancellation without agent processing.
This bypasses all the agent complexity and tests just the core cancellation mechanism.
"""
import sys
sys.path.insert(0, 'src')

import trio
from rich.console import Console
from rich.panel import Panel
from src.tunacode.core.abort_controller import AbortController
from src.tunacode.core.state import StateManager
from src.tunacode.ui.keybindings import create_key_bindings

try:
    from src.tunacode.debug.trio_debug import trio_debug
    DEBUG_AVAILABLE = True
except ImportError:
    DEBUG_AVAILABLE = False

console = Console()

async def simulate_thinking_with_cancellation():
    """Simulate a long-running 'Thinking...' operation that can be cancelled with Esc."""
    
    # Set up state manager and abort controller
    state_manager = StateManager()
    abort_controller = AbortController()
    
    # Create app context
    from src.tunacode.core.abort_controller import AppContext
    async with trio.open_nursery() as nursery:
        app_context = AppContext(nursery, abort_controller)
        state_manager.app_context = app_context
        
        # Enable debug if available
        if DEBUG_AVAILABLE:
            trio_debug.start_live_display(minimal_mode=True)
            trio_debug.log_event("ESC_TEST", "Test", "Starting Esc cancellation test", "SUCCESS")
        
        print("\n🚀 Esc Cancellation Test")
        print("=" * 50)
        print("Instructions:")
        print("1. You'll see a 'Thinking...' message")
        print("2. Press ESC while it's showing to test cancellation")
        print("3. Press Ctrl+C to exit if needed")
        print("4. The operation should cancel immediately when you press Esc")
        print("")
        
        # Auto-start the test after a brief delay
        print("Starting test in 2 seconds...")
        await trio.sleep(2)
        
        try:
            with trio.CancelScope() as cancel_scope:
                # Register the cancel scope with abort controller
                abort_controller.set_cancel_scope(cancel_scope)
                
                # Show "Thinking..." message
                thinking_panel = Panel(
                    "[bold cyan]Thinking...[/bold cyan]\n\n"
                    "This is a test of Esc key cancellation.\n"
                    "Press [bold red]ESC[/bold red] to cancel this operation immediately.\n"
                    "The operation will run for 30 seconds unless cancelled.",
                    title="● TunaCode Test",
                    border_style="blue"
                )
                
                console.print(thinking_panel)
                
                if DEBUG_AVAILABLE:
                    trio_debug.log_event("THINKING_START", "Test", "Thinking simulation started", "INFO")
                
                # Simulate long-running operation
                for i in range(30):
                    await trio.sleep(1)
                    if DEBUG_AVAILABLE:
                        trio_debug.log_event("THINKING_TICK", "Test", f"Thinking tick {i+1}/30", "INFO")
                    
                    # Check if we've been aborted
                    if abort_controller.is_aborted():
                        console.print("\n[bold green]✅ SUCCESS: Operation was cancelled by AbortController![/bold green]")
                        if DEBUG_AVAILABLE:
                            trio_debug.log_event("CANCEL_SUCCESS", "Test", "Operation cancelled successfully", "SUCCESS")
                        return
                
                # If we got here, the operation completed without cancellation
                console.print("\n[yellow]⚠️  Operation completed without cancellation[/yellow]")
                if DEBUG_AVAILABLE:
                    trio_debug.log_event("NO_CANCEL", "Test", "Operation completed without cancellation", "WARNING")
                    
        except trio.Cancelled:
            console.print("\n[bold green]✅ SUCCESS: Operation was cancelled by Trio CancelScope![/bold green]")
            if DEBUG_AVAILABLE:
                trio_debug.log_event("TRIO_CANCEL", "Test", "Operation cancelled by Trio", "SUCCESS")
        
        # Show debug summary
        if DEBUG_AVAILABLE:
            print("\n" + "=" * 50)
            print("🎯 Debug Summary:")
            trio_debug.show_summary()
            
            print("\nLook for these events to confirm Esc cancellation:")
            print("- KEY_PRESS: Esc -> abort_operation")
            print("- ABORT_SIGNAL: triggered by Esc key")
            print("- CANCEL_SCOPE_CANCEL: scope cancellation")

if __name__ == "__main__":
    try:
        trio.run(simulate_thinking_with_cancellation)
    except KeyboardInterrupt:
        print("\n👋 Test ended by user (Ctrl+C)")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()