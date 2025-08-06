"""Key binding handlers for TunaCode UI."""

import logging

from prompt_toolkit.key_binding import KeyBindings

from ..core.state import StateManager

logger = logging.getLogger(__name__)


def create_key_bindings(state_manager: StateManager = None) -> KeyBindings:
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
        """Handle ESC key - raises KeyboardInterrupt for unified abort handling."""
        logger.debug("ESC key pressed - raising KeyboardInterrupt")

        # Cancel any active task if present
        if state_manager and hasattr(state_manager.session, "current_task"):
            current_task = state_manager.session.current_task
            if current_task and not current_task.done():
                logger.debug(f"Cancelling current task: {current_task}")
                try:
                    current_task.cancel()
                    logger.debug("Task cancellation initiated successfully")
                except Exception as e:
                    logger.debug(f"Failed to cancel task: {e}")

        # Raise KeyboardInterrupt to trigger unified abort handling in REPL
        raise KeyboardInterrupt()

    return kb
