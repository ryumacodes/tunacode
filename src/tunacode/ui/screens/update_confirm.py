"""Update confirmation screen for TunaCode."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Static

# Modal layout constants
MODAL_WIDTH = 50
MODAL_PADDING_VERTICAL = 1
MODAL_PADDING_HORIZONTAL = 2
SECTION_MARGIN_BOTTOM = 1


class UpdateConfirmScreen(Screen[bool]):
    """Modal screen to confirm update installation."""

    CSS = f"""
    UpdateConfirmScreen {{
        align: center middle;
    }}

    #update-container {{
        width: {MODAL_WIDTH};
        height: auto;
        border: solid $primary;
        background: $surface;
        padding: {MODAL_PADDING_VERTICAL} {MODAL_PADDING_HORIZONTAL};
    }}

    #update-title {{
        text-style: bold;
        color: $accent;
        text-align: center;
        margin-bottom: {SECTION_MARGIN_BOTTOM};
    }}

    #update-info {{
        margin-bottom: {SECTION_MARGIN_BOTTOM};
    }}
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
