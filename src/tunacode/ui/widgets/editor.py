"""Editor widget for TunaCode REPL."""

from __future__ import annotations

from textual import events
from textual.binding import Binding
from textual.widgets import Input

from .messages import EditorSubmitRequested
from .status_bar import StatusBar


class Editor(Input):
    """Single-line editor with Enter to submit."""

    BINDINGS = [
        Binding("enter", "submit", "Submit", show=False),
    ]

    def __init__(self) -> None:
        super().__init__(placeholder="we await...")

    def on_key(self, event: events.Key) -> None:
        """Let confirmation keys pass through when confirmation is pending."""
        if event.key not in ("1", "2", "3"):
            return
        app = self.app
        if not hasattr(app, "pending_confirmation"):
            return
        if app.pending_confirmation is None:
            return
        if app.pending_confirmation.future.done():
            return
        # Pending confirmation active - prevent Input from consuming this key
        event.prevent_default()

    def action_submit(self) -> None:
        text = self.value.strip()
        if not text:
            return

        self.post_message(EditorSubmitRequested(text=text, raw_text=self.value))
        self.value = ""

    def watch_value(self, value: str) -> None:
        """Toggle bash-mode class based on input prefix."""
        self.remove_class("bash-mode")
        try:
            status_bar = self.app.query_one(StatusBar)
        except Exception:
            return
        if value.startswith("!"):
            self.add_class("bash-mode")
            status_bar.set_mode("bash mode")
            # Auto-insert space: "!x" -> "! x"
            if len(value) == 2 and value[1] != " ":
                self.value = f"! {value[1]}"
                self.cursor_position = len(self.value)
        else:
            status_bar.set_mode(None)
