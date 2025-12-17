"""Update confirmation screen for TunaCode."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Static


class UpdateConfirmScreen(Screen[bool]):
    """Modal screen to confirm update installation."""

    CSS = """
    UpdateConfirmScreen {
        align: center middle;
    }

    #update-container {
        width: 50;
        height: auto;
        border: solid $primary;
        background: $surface;
        padding: 1 2;
    }

    #update-title {
        text-style: bold;
        color: $accent;
        text-align: center;
        margin-bottom: 1;
    }

    #update-info {
        margin-bottom: 1;
    }
    """

    BINDINGS = [
        ("escape", "cancel", "Cancel"),
        ("y", "confirm", "Yes"),
        ("n", "cancel", "No"),
    ]

    def __init__(self, current_version: str, latest_version: str) -> None:
        super().__init__()
        self._current = current_version
        self._latest = latest_version

    def compose(self) -> ComposeResult:
        with Vertical(id="update-container"):
            yield Static("Update Available", id="update-title")
            yield Static(
                f"Current: {self._current}\nLatest:  {self._latest}",
                id="update-info",
            )
            yield Static("Install update? (y/n)")

    def action_confirm(self) -> None:
        self.dismiss(True)

    def action_cancel(self) -> None:
        self.dismiss(False)
