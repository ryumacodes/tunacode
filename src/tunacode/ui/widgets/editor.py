"""Editor widget for TunaCode REPL."""

from __future__ import annotations

from typing import Optional

from rich.text import Text
from textual.binding import Binding
from textual.events import Key
from textual.widgets import TextArea

from tunacode.utils.ui import replace_token, textual_complete_paths

from .messages import EditorCompletionsAvailable, EditorSubmitRequested


class Editor(TextArea):
    """Multiline editor with Esc+Enter newline binding, Tab completions, and submit on Enter."""

    BINDINGS = [
        Binding("tab", "complete", "Complete", show=False),
        Binding("enter", "submit", "Submit", show=False),
        Binding("ctrl+o", "insert_newline", "Newline", show=False),
    ]

    def __init__(self, *, language: Optional[str] = None) -> None:
        super().__init__(language=language)
        self.placeholder = "we await..."
        self._awaiting_escape_enter: bool = False

    def get_line(self, line_index: int) -> Text:
        text_value: str = self.text  # type: ignore[has-type]
        if not text_value.strip() and line_index == 0 and self.placeholder:
            return Text(self.placeholder, end="", no_wrap=True, style="dim")
        return super().get_line(line_index)

    def action_complete(self) -> None:
        prefix, start, end = self._current_token()
        if prefix is None:
            return
        if prefix.startswith("@"):
            candidates = [f"@{c}" for c in textual_complete_paths(prefix[1:])]
        else:
            candidates = []

        if not candidates:
            return

        replacement = candidates[0]
        text_value: str = self.text  # type: ignore[has-type]
        self.text = replace_token(text_value, start, end, replacement)
        cursor_row, _ = self.cursor_location
        self.move_cursor((cursor_row, start + len(replacement)))

        if len(candidates) > 1:
            self.post_message(EditorCompletionsAvailable(candidates=candidates))

    def action_submit(self) -> None:
        text_value: str = self.text  # type: ignore[has-type]
        text = text_value.strip()
        if not text:
            return

        self.post_message(EditorSubmitRequested(text=text, raw_text=text_value))
        self.text = ""

    def action_insert_newline(self) -> None:
        self.insert("\n")

    def _current_token(self) -> tuple[Optional[str], int, int]:
        """Get the current token under cursor with absolute buffer offsets.

        Returns (token, start_offset, end_offset) where offsets are absolute
        character positions in the full text buffer.
        """
        cursor_row, cursor_col = self.cursor_location
        text_value: str = self.text  # type: ignore[has-type]
        lines = text_value.splitlines(keepends=True)

        if cursor_row >= len(lines):
            end = len(text_value)
            return None, end, end

        line = lines[cursor_row]
        # Compute absolute start-of-line index in the full text
        line_start = sum(len(ln) for ln in lines[:cursor_row])

        # Find token bounds within the line, then convert to absolute offsets
        left_in_line = line.rfind(" ", 0, cursor_col) + 1
        token = line[left_in_line:cursor_col]
        if not token:
            abs_pos = line_start + left_in_line
            return None, abs_pos, abs_pos

        start = line_start + left_in_line
        end = start + len(token)
        return token, start, end

    def on_key(self, event: Key) -> None:
        if event.key == "escape":
            self._awaiting_escape_enter = True
            event.stop()
            return
        if event.key == "enter" and self._awaiting_escape_enter:
            self._awaiting_escape_enter = False
            event.stop()
            self.insert("\n")
            return
        if event.key == "enter":
            self._awaiting_escape_enter = False
            event.stop()
            self.action_submit()
            return

        self._awaiting_escape_enter = False
        # Let event propagate to TextArea's default handling
