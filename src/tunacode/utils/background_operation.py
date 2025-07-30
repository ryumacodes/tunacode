"""
Background operation management with Esc key cancellation.

This module provides a way to run background operations (like agent processing)
while keeping a prompt_toolkit session active to capture Esc key presses.
"""

import asyncio
from prompt_toolkit.application import Application
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout.containers import VSplit, HSplit, Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.formatted_text import HTML
from rich.console import Console

# Import debug system
try:
    from tunacode.debug.trio_debug import trio_debug
    DEBUG_AVAILABLE = True
except ImportError:
    DEBUG_AVAILABLE = False


async def run_with_esc_cancellation(abort_controller, operation_func, *args, **kwargs):
    """
    Run a background operation with Esc key cancellation.
    
    This creates a minimal prompt_toolkit application that shows "Thinking..."
    and captures Esc key presses to cancel the background operation.
    
    Args:
        abort_controller: The AbortController to trigger on Esc
        operation_func: The async function to run in background
        *args, **kwargs: Arguments to pass to operation_func
    
    Returns:
        The result of operation_func, or raises asyncio.CancelledError if Esc was pressed
    """
    if DEBUG_AVAILABLE:
        trio_debug.log_event("BACKGROUND_OP", "BackgroundOperation", "Starting operation with Esc monitoring", "INFO")
    
    # Create key bindings for Esc cancellation
    kb = KeyBindings()
    
    @kb.add('escape')
    def _(event):
        """Handle Esc key press to cancel operation."""
        if DEBUG_AVAILABLE:
            trio_debug.log_event("ESC_PRESSED", "BackgroundOperation", "Esc key pressed - triggering abort", "SUCCESS")
        
        # Trigger the abort controller
        abort_controller.abort(trigger="Esc key (background operation)")
        
        # Exit the prompt application
        event.app.exit()
    
    @kb.add('c-c')
    def _(event):
        """Handle Ctrl+C to force exit."""
        if DEBUG_AVAILABLE:
            trio_debug.log_event("CTRL_C", "BackgroundOperation", "Ctrl+C pressed", "INFO")
        event.app.exit()
    
    # Create the UI layout
    def get_status_text():
        return HTML(
            '<b>● Thinking...</b>\n\n'
            'Processing your request...\n'
            'Press <b>ESC</b> to cancel\n'
            'Press <b>Ctrl+C</b> to force exit'
        )
    
    # Create layout
    layout = Layout(
        HSplit([
            Window(
                FormattedTextControl(get_status_text),
                height=6,
                style="class:thinking"
            )
        ])
    )
    
    # Create the application
    app = Application(
        layout=layout,
        key_bindings=kb,
        full_screen=False,
        mouse_support=False,
    )
    
    operation_result = None
    operation_error = None
    
    async def run_operation():
        """Run the actual operation in the background."""
        nonlocal operation_result, operation_error
        try:
            if DEBUG_AVAILABLE:
                trio_debug.log_event("OPERATION_START", "BackgroundOperation", "Background operation started", "INFO")
            
            operation_result = await operation_func(*args, **kwargs)
            
            if DEBUG_AVAILABLE:
                trio_debug.log_event("OPERATION_COMPLETE", "BackgroundOperation", "Background operation completed", "SUCCESS")
            
            # Operation completed - exit the app
            app.exit()
            
        except asyncio.CancelledError:
            if DEBUG_AVAILABLE:
                trio_debug.log_event("OPERATION_CANCELLED", "BackgroundOperation", "Background operation cancelled", "INFO")
            app.exit()
            raise
        except Exception as e:
            if DEBUG_AVAILABLE:
                trio_debug.log_event("OPERATION_ERROR", "BackgroundOperation", f"Background operation error: {e}", "ERROR")
            operation_error = e
            app.exit()
    
    try:
        # Start background operation
        operation_task = asyncio.create_task(run_operation())
        if abort_controller:
            abort_controller.add_task(operation_task)
        
        # Run the prompt application in a thread
        app_task = asyncio.create_task(asyncio.to_thread(app.run))
        
        # Wait for either to complete
        done, pending = await asyncio.wait([operation_task, app_task], return_when=asyncio.FIRST_COMPLETED)
        
        # Cancel any pending tasks
        for task in pending:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        
        # Check results
        if operation_error:
            raise operation_error
        
        return operation_result
        
    except asyncio.CancelledError:
        if DEBUG_AVAILABLE:
            trio_debug.log_event("TRIO_CANCELLED", "BackgroundOperation", "Operation cancelled by asyncio", "SUCCESS")
        raise


async def simple_esc_test(abort_controller):
    """
    Simple test function for Esc cancellation.
    
    This simulates a long-running operation that can be cancelled with Esc.
    """
    console = Console()
    
    try:
        for i in range(30):  # 30 second test
            await asyncio.sleep(1)
            
            if DEBUG_AVAILABLE:
                trio_debug.log_event("TEST_TICK", "SimpleTest", f"Test tick {i+1}/30", "INFO")
            
            # Check if aborted
            if abort_controller.is_aborted():
                if DEBUG_AVAILABLE:
                    trio_debug.log_event("TEST_ABORTED", "SimpleTest", "Test aborted via AbortController", "SUCCESS")
                return "aborted"
        
        if DEBUG_AVAILABLE:
            trio_debug.log_event("TEST_COMPLETED", "SimpleTest", "Test completed without abortion", "WARNING")
        return "completed"
        
    except asyncio.CancelledError:
        if DEBUG_AVAILABLE:
            trio_debug.log_event("TEST_TRIO_CANCELLED", "SimpleTest", "Test cancelled by asyncio", "SUCCESS")
        raise