"""Editor widget for TunaCode REPL."""

from __future__ import annotations

from textual.binding import Binding
from textual.widgets import Input

from .messages import EditorSubmitRequested


class Editor(Input):
    """Single-line editor with Enter to submit."""

    BINDINGS = [
        Binding("enter", "submit", "Submit", show=False),
    ]

    def __init__(self) -> None:
        super().__init__(placeholder="we await...")

    def action_submit(self) -> None:
        text = self.value.strip()
        if not text:
            return

        self.post_message(EditorSubmitRequested(text=text, raw_text=self.value))
        self.value = ""
