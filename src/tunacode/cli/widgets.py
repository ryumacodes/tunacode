"""Textual widgets for TunaCode REPL.

Contains reusable UI widgets:
- ResourceBar: Top status bar showing model, tokens, cost
- Editor: Multiline input with Tab completions and Esc+Enter newlines
"""

from __future__ import annotations

from typing import Iterable, Optional

from rich.text import Text
from textual.binding import Binding
from textual.events import Key
from textual.message import Message
from textual.widgets import Static, TextArea

from tunacode.constants import (
    APP_NAME,
    RESOURCE_BAR_COST_FORMAT,
    RESOURCE_BAR_SEPARATOR,
)
from tunacode.utils.ui import replace_token, textual_complete_paths


class EditorCompletionsAvailable(Message):
    """Notify the app when multiple completions are available."""

    def __init__(self, *, candidates: Iterable[str]) -> None:
        super().__init__()
        self.candidates = list(candidates)


class EditorSubmitRequested(Message):
    """Submit event for the current editor content."""

    def __init__(self, *, text: str, raw_text: str) -> None:
        super().__init__()
        self.text = text
        self.raw_text = raw_text


class ToolResultDisplay(Message):
    """Request to display a tool result panel in the RichLog."""

    def __init__(
        self,
        *,
        tool_name: str,
        status: str,
        args: dict,
        result: str | None = None,
        duration_ms: float | None = None,
    ) -> None:
        super().__init__()
        self.tool_name = tool_name
        self.status = status
        self.args = args
        self.result = result
        self.duration_ms = duration_ms


class ResourceBar(Static):
    """Top bar showing resources: tokens, model, cost.

    NeXTSTEP Persistent Status Zone: "Glanceable, rarely changes"
    """

    def __init__(self) -> None:
        super().__init__("Loading...")  # Initial content to ensure rendering
        self._tokens: int = 0
        self._max_tokens: int = 200000
        self._model: str = "---"
        self._cost: float = 0.0
        self._session_cost: float = 0.0

    def on_mount(self) -> None:
        self._refresh_display()

    def update_stats(
        self,
        *,
        tokens: int | None = None,
        max_tokens: int | None = None,
        model: str | None = None,
        cost: float | None = None,
        session_cost: float | None = None,
    ) -> None:
        if tokens is not None:
            self._tokens = tokens
        if max_tokens is not None:
            self._max_tokens = max_tokens
        if model is not None:
            self._model = model
        if cost is not None:
            self._cost = cost
        if session_cost is not None:
            self._session_cost = session_cost
        self._refresh_display()

    def _format_tokens(self) -> str:
        """Format token count with K suffix for readability."""
        if self._tokens >= 1000:
            return f"{self._tokens / 1000:.1f}k"
        return str(self._tokens)

    def _format_max_tokens(self) -> str:
        """Format max tokens with K suffix."""
        if self._max_tokens >= 1000:
            return f"{self._max_tokens // 1000}k"
        return str(self._max_tokens)

    def _refresh_display(self) -> None:
        """Compact single-line status: ◇ tokens: 1.2k ◇ model ◇ $0.00 ◇ tunacode"""
        sep = RESOURCE_BAR_SEPARATOR
        session_cost_str = RESOURCE_BAR_COST_FORMAT.format(cost=self._session_cost)

        content = Text.assemble(
            ("◇ ", "dim"),
            ("tokens: ", ""),  # Default text (light gray)
            (self._format_tokens(), "cyan"),
            (sep, "dim"),
            (self._model, "cyan"),
            (sep, "dim"),
            (session_cost_str, "green"),
            (sep, "dim"),
            (APP_NAME.lower(), "magenta bold"),
        )
        self.update(content)


class Editor(TextArea):
    """Multiline editor with Esc+Enter newline binding, Tab completions, and submit on Enter."""

    BINDINGS = [
        Binding("tab", "complete", "Complete", show=False),
        Binding("enter", "submit", "Submit", show=False),
    ]

    def __init__(self, *, language: Optional[str] = None) -> None:
        super().__init__(language=language)
        self._awaiting_escape_enter: bool = False

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
        self.text = replace_token(self.text, start, end, replacement)
        cursor_row, _ = self.cursor_location
        self.move_cursor((cursor_row, start + len(replacement)))

        if len(candidates) > 1:
            # Surface alternatives in the log for now; future UI will show a popover.
            self.post_message(EditorCompletionsAvailable(candidates=candidates))

    def action_submit(self) -> None:
        text = self.text.strip()
        if not text:
            return

        self.post_message(EditorSubmitRequested(text=text, raw_text=self.text))
        self.text = ""

    def _current_token(self) -> tuple[Optional[str], int, int]:
        cursor_row, cursor_col = self.cursor_location
        lines = self.text.splitlines()
        if cursor_row >= len(lines):
            return None, cursor_col, cursor_col
        line = lines[cursor_row]
        left = line.rfind(" ", 0, cursor_col) + 1
        token = line[left:cursor_col]
        if not token:
            return None, left, left
        return token, left, left + len(token)

    async def on_key(self, event: Key) -> None:
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
        await self._on_key(event)
