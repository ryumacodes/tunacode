#!/usr/bin/env python3
"""
Test the keyboard monitoring solution for Esc detection.
"""
import sys
sys.path.insert(0, 'src')

import trio
from rich.console import Console
from src.tunacode.core.abort_controller import AbortController, AppContext
from src.tunacode.core.state import StateManager
from src.tunacode.utils.keyboard_monitor import monitor_esc_during_operation

try:
    from src.tunacode.debug.trio_debug import trio_debug
    DEBUG_AVAILABLE = True
except ImportError:
    DEBUG_AVAILABLE = False

console = Console()

async def test_keyboard_monitoring():
    """Test the keyboard monitoring solution."""
    
    console.print("🧪 Testing Keyboard Monitoring for Esc Detection")
    console.print("=" * 60)
    console.print()
    console.print("Instructions:")
    console.print("1. You'll see a 'Working...' message for 15 seconds")
    console.print("2. Press [bold red]ESC[/bold red] at any time to test cancellation")
    console.print("3. The operation should cancel [bold green]immediately[/bold green]")
    console.print("4. Press Ctrl+C to force exit if needed")
    console.print()
    
    # Set up state manager and abort controller
    state_manager = StateManager()
    abort_controller = AbortController()
    
    # Enable debug if available
    if DEBUG_AVAILABLE:
        trio_debug.start_live_display(minimal_mode=True)
        trio_debug.log_event("KEYBOARD_TEST", "Test", "Starting keyboard monitoring test", "SUCCESS")
    
    async with trio.open_nursery() as nursery:
        app_context = AppContext(nursery, abort_controller)
        state_manager.app_context = app_context
        
        async def long_operation():
            """Simulate agent processing with spinner."""
            console.print("[bold cyan]● Working...[/bold cyan]")
            console.print("[dim]Press ESC to cancel this operation[/dim]")
            console.print()
            
            if DEBUG_AVAILABLE:
                trio_debug.log_event("OPERATION_START", "Test", "Long operation started", "INFO")
            
            # Simulate 15 seconds of work
            for i in range(15):
                await trio.sleep(1)
                console.print(f"[dim]Working... {i+1}/15 seconds[/dim]")
                
                if DEBUG_AVAILABLE:
                    trio_debug.log_event("OPERATION_TICK", "Test", f"Work tick {i+1}/15", "INFO")
                
                # Check if aborted
                if abort_controller.is_aborted():
                    console.print("\n[bold green]✅ Operation cancelled by AbortController![/bold green]")
                    if DEBUG_AVAILABLE:
                        trio_debug.log_event("OPERATION_CANCELLED", "Test", "Operation cancelled via AbortController", "SUCCESS")
                    return "cancelled"
            
            console.print("\n[yellow]⚠️  Operation completed without cancellation[/yellow]")
            if DEBUG_AVAILABLE:
                trio_debug.log_event("OPERATION_COMPLETED", "Test", "Operation completed without cancellation", "WARNING")
            return "completed"
        
        try:
            with trio.CancelScope() as cancel_scope:
                abort_controller.set_cancel_scope(cancel_scope)
                
                console.print("🚀 Starting operation with keyboard monitoring...")
                console.print()
                
                result = await monitor_esc_during_operation(abort_controller, long_operation)
                
                if result == "cancelled":
                    console.print("[bold green]🎉 SUCCESS: Esc cancellation works perfectly![/bold green]")
                else:
                    console.print("[yellow]📝 No cancellation detected - operation completed normally[/yellow]")
                    
        except trio.Cancelled:
            console.print("\n[bold green]✅ SUCCESS: Trio cancellation triggered![/bold green]")
            if DEBUG_AVAILABLE:
                trio_debug.log_event("TRIO_CANCELLED", "Test", "Operation cancelled by Trio", "SUCCESS")
        
        # Show debug summary
        if DEBUG_AVAILABLE:
            console.print("\n" + "=" * 60)
            console.print("🎯 Debug Summary:")
            trio_debug.show_summary()

if __name__ == "__main__":
    try:
        trio.run(test_keyboard_monitoring)
    except KeyboardInterrupt:
        print("\n👋 Test ended by user (Ctrl+C)")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()