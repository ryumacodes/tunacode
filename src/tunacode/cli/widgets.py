"""Textual widgets for TunaCode REPL.

Contains reusable UI widgets:
- ResourceBar: Top status bar showing model, tokens, cost
- Editor: Multiline input with Tab completions and Esc+Enter newlines
"""

from __future__ import annotations

from typing import Iterable, Optional

from rich.text import Text
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
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

    def _calculate_remaining_pct(self) -> float:
        """Calculate percentage of context window remaining."""
        if self._max_tokens == 0:
            return 0.0
        return (self._max_tokens - self._tokens) / self._max_tokens * 100

    def _get_circle_color(self, remaining_pct: float) -> str:
        """Return color based on remaining context percentage."""
        if remaining_pct > 60:
            return "green"
        if remaining_pct > 30:
            return "yellow"
        return "red"

    def _get_circle_char(self, remaining_pct: float) -> str:
        """Pick circle character based on fill level."""
        if remaining_pct > 87.5:
            return "●"
        if remaining_pct > 62.5:
            return "◕"
        if remaining_pct > 37.5:
            return "◑"
        if remaining_pct > 12.5:
            return "◔"
        return "○"

    def _refresh_display(self) -> None:
        """Compact single-line status: model ◇ ● 100% ◇ $0.00"""
        sep = RESOURCE_BAR_SEPARATOR
        session_cost_str = RESOURCE_BAR_COST_FORMAT.format(cost=self._session_cost)

        remaining_pct = self._calculate_remaining_pct()
        circle_char = self._get_circle_char(remaining_pct)
        circle_color = self._get_circle_color(remaining_pct)

        content = Text.assemble(
            (self._model, "cyan"),
            (sep, "dim"),
            (circle_char, circle_color),
            (f" {remaining_pct:.0f}%", circle_color),
            (sep, "dim"),
            (session_cost_str, "green"),
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
        self.placeholder = "we await..."
        self._awaiting_escape_enter: bool = False

    def get_line(self, line_index: int) -> Text:
        # If document is empty and we're rendering the first line, show placeholder
        if not self.text.strip() and line_index == 0 and self.placeholder:
            return Text(self.placeholder, end="", no_wrap=True, style="dim")
        
        # Otherwise, use the normal implementation
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


class TestBar(Horizontal):
    """Simple test bar to debug text visibility."""

    def compose(self) -> ComposeResult:
        yield Static("TEST LEFT", id="test-left")
        yield Static("TEST MID", id="test-mid") 
        yield Static("TEST RIGHT", id="test-right")


class StatusBar(Horizontal):
    """Bottom status bar - 3 zones, no borders.

    ┌───────────────┬─────────────┬───────────────────┐
    │ branch ● dir  │  bg: idle   │   last: tool      │
    └───────────────┴─────────────┴───────────────────┘
    """

    def compose(self) -> ComposeResult:
        yield Static("main ● ~/proj", id="status-left")
        yield Static("bg: idle", id="status-mid")
        yield Static("last: -", id="status-right")

    def on_mount(self) -> None:
        self._refresh_location()

    def _refresh_location(self) -> None:
        """Get git branch and pwd."""
        import os
        import subprocess

        try:
            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                capture_output=True,
                text=True,
                timeout=1,
            )
            branch = result.stdout.strip() or "main"
        except Exception:
            branch = "main"

        dirname = os.path.basename(os.getcwd()) or "~"
        self.query_one("#status-left", Static).update(f"{branch} ● {dirname}")

    def update_last_action(self, tool_name: str) -> None:
        """Update the last action zone with tool name."""
        self.query_one("#status-right", Static).update(f"last: {tool_name}")
