"""Resource and status bar widgets for TunaCode REPL."""

from __future__ import annotations

import os
import subprocess

from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Static

from tunacode.constants import RESOURCE_BAR_COST_FORMAT, RESOURCE_BAR_SEPARATOR


class ResourceBar(Static):
    """Top bar showing resources: tokens, model, cost."""

    def __init__(self) -> None:
        super().__init__("Loading...")
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
        if self._max_tokens == 0:
            return 0.0
        return (self._max_tokens - self._tokens) / self._max_tokens * 100

    def _get_circle_color(self, remaining_pct: float) -> str:
        if remaining_pct > 60:
            return "green"
        if remaining_pct > 30:
            return "yellow"
        return "red"

    def _get_circle_char(self, remaining_pct: float) -> str:
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


class StatusBar(Horizontal):
    """Bottom status bar - 3 zones."""

    def compose(self) -> ComposeResult:
        yield Static("main ● ~/proj", id="status-left")
        yield Static("bg: idle", id="status-mid")
        yield Static("last: -", id="status-right")

    def on_mount(self) -> None:
        self._refresh_location()

    def _refresh_location(self) -> None:
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
        self.query_one("#status-right", Static).update(f"last: {tool_name}")

    def update_bg_status(self, tool_name: str) -> None:
        text = f"bg: {tool_name}..." if tool_name else "bg: idle"
        self.query_one("#status-mid", Static).update(text)
