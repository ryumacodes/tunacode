"""
Cancellable processing utilities that allow Esc key cancellation during operations.

This provides a simple approach: show a brief "Press Esc to cancel" prompt
before starting agent processing, giving users a chance to cancel.
"""

import asyncio
from typing import Optional, Callable, Any
from tunacode.core.state import StateManager
from tunacode.ui import console as ui

# Import debug system
try:
    from tunacode.debug.trio_debug import trio_debug
    DEBUG_AVAILABLE = True
except ImportError:
    DEBUG_AVAILABLE = False


async def process_with_esc_option(
    state_manager: StateManager,
    operation_func: Callable,
    operation_name: str = "operation",
    cancel_timeout: float = 2.0,
    *args, **kwargs
) -> Any:
    """
    Run an operation with an initial Esc cancellation window.
    
    This shows a brief message allowing the user to press Esc to cancel
    before the operation starts. If no Esc is pressed within the timeout,
    the operation proceeds normally.
    
    Args:
        state_manager: The state manager
        operation_func: The async function to run
        operation_name: Name of the operation for display
        cancel_timeout: Seconds to wait for Esc before proceeding
        *args, **kwargs: Arguments to pass to operation_func
    
    Returns:
        The result of operation_func, or raises asyncio.CancelledError if cancelled
    """
    
    abort_controller = state_manager.app_context.abort_controller if state_manager.app_context else None
    
    if not abort_controller:
        # No abort controller available, run operation directly
        return await operation_func(*args, **kwargs)
    
    if DEBUG_AVAILABLE:
        trio_debug.log_event("CANCELLABLE_START", "CancellableProcessing", f"Starting cancellable {operation_name}", "INFO")
    
    # Show cancellation prompt
    from tunacode.ui.input import input as ui_input
    from tunacode.ui.keybindings import create_key_bindings
    from prompt_toolkit.formatted_text import HTML
    
    kb = create_key_bindings(state_manager)
    
    # Create a custom prompt that shows for a limited time
    cancel_prompt = HTML(
        f'<b>Starting {operation_name}...</b> '
        f'Press <b>ESC</b> to cancel (auto-start in {cancel_timeout}s)'
    )
    
    try:
        # Show the prompt with a timeout
        async def prompt_with_timeout():
            """Show prompt that auto-submits after timeout."""
            await asyncio.sleep(cancel_timeout)
            # If we reach here, no Esc was pressed - proceed with operation
            return "proceed"
        
        async def check_abort():
            """Check for abort periodically."""
            while True:
                await asyncio.sleep(0.1)
                if abort_controller.is_aborted():
                    if DEBUG_AVAILABLE:
                        trio_debug.log_event("OPERATION_CANCELLED", "CancellableProcessing", f"{operation_name} cancelled by user", "SUCCESS")
                    await ui.warning(f"{operation_name} cancelled")
                    raise asyncio.CancelledError("Operation cancelled by user")
        
        # Create tasks for timeout and abort checking
        timeout_task = asyncio.create_task(prompt_with_timeout())
        abort_task = asyncio.create_task(check_abort())
        
        if abort_controller:
            abort_controller.add_task(timeout_task)
            abort_controller.add_task(abort_task)
        
        # Wait for either timeout or abort
        done, pending = await asyncio.wait([timeout_task, abort_task], return_when=asyncio.FIRST_COMPLETED)
        
        # Cancel pending tasks
        for task in pending:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        
        # If timeout completed, proceed with operation
        if timeout_task in done:
            if DEBUG_AVAILABLE:
                trio_debug.log_event("OPERATION_PROCEEDING", "CancellableProcessing", f"Proceeding with {operation_name}", "INFO")
            
            # Run the actual operation
            operation_task = asyncio.create_task(operation_func(*args, **kwargs))
            if abort_controller:
                abort_controller.add_task(operation_task)
            return await operation_task
        else:
            # Abort task completed - cancellation was requested
            raise asyncio.CancelledError("Operation cancelled by user")
                
    except asyncio.CancelledError:
        if DEBUG_AVAILABLE:
            trio_debug.log_event("TRIO_CANCELLED", "CancellableProcessing", f"{operation_name} cancelled by asyncio", "SUCCESS")
        raise


async def show_thinking_with_esc(state_manager: StateManager, operation_func: Callable, *args, **kwargs):
    """
    Show "Thinking..." message while running operation, with Esc cancellation.
    
    This is a simpler version that just shows the thinking message and
    relies on the existing Esc key bindings in the REPL loop.
    """
    
    abort_controller = state_manager.app_context.abort_controller if state_manager.app_context else None
    
    if DEBUG_AVAILABLE:
        trio_debug.log_event("THINKING_START", "CancellableProcessing", "Starting thinking with Esc support", "INFO")
    
    # Show spinner
    spinner = await ui.spinner(True, None, state_manager)
    
    try:
        # Run the operation
        operation_task = asyncio.create_task(operation_func(*args, **kwargs))
        if abort_controller:
            abort_controller.add_task(operation_task)
        
        result = await operation_task
        
        if DEBUG_AVAILABLE:
            trio_debug.log_event("THINKING_COMPLETE", "CancellableProcessing", "Thinking completed successfully", "SUCCESS")
        
        return result
        
    except asyncio.CancelledError:
        if DEBUG_AVAILABLE:
            trio_debug.log_event("THINKING_CANCELLED", "CancellableProcessing", "Thinking cancelled", "SUCCESS")
        raise
    finally:
        await ui.spinner(False, spinner, state_manager)