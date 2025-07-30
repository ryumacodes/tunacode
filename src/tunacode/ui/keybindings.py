"""Key binding handlers for TunaCode UI."""

from prompt_toolkit.key_binding import KeyBindings
from typing import Optional
from tunacode.core.state import StateManager


def create_key_bindings(state_manager: Optional[StateManager] = None) -> KeyBindings:
    """Create and configure key bindings for the UI."""
    kb = KeyBindings()

    @kb.add("enter")
    def _submit(event):
        """Submit the current buffer."""
        event.current_buffer.validate_and_handle()

    @kb.add("c-o")  # ctrl+o
    def _newline(event):
        """Insert a newline character."""
        event.current_buffer.insert_text("\n")

    @kb.add("escape", "enter")
    def _escape_enter(event):
        """Insert a newline when escape then enter is pressed."""
        event.current_buffer.insert_text("\n")

    @kb.add("escape")
    def _escape(event):
        """Handle Esc key to cancel running agent tasks."""
        # Note: This only works when prompt_toolkit is actively waiting for input,
        # not during background agent processing. For that, we use SimpleEscMonitor.
        from tunacode.core.interrupt_controller import trigger_global_interrupt
        
        if state_manager and hasattr(state_manager.session, 'current_task'):
            current_task = state_manager.session.current_task
            if current_task and not current_task.done():
                # Trigger global interrupt
                trigger_global_interrupt()
                # Cancel the running task
                current_task.cancel()
                # Set a flag to indicate interruption
                state_manager.session.task_interrupted = True

    return kb
