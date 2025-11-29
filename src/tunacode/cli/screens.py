"""Textual screens for TunaCode REPL.

Contains modal screens:
- ToolConfirmationModal: Confirm tool execution with optional skip-future toggle
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.message import Message
from textual.screen import ModalScreen
from textual.widgets import Button, Checkbox, Label

if TYPE_CHECKING:
    from tunacode.types import ToolConfirmationRequest, ToolConfirmationResponse


class ToolConfirmationResult(Message):
    """Result of a tool confirmation modal."""

    def __init__(self, *, response: "ToolConfirmationResponse") -> None:
        super().__init__()
        self.response = response


class ToolConfirmationModal(ModalScreen[None]):
    """Modal that gathers tool confirmation asynchronously."""

    def __init__(self, request: "ToolConfirmationRequest") -> None:
        super().__init__()
        self.request = request
        self.skip_future = Checkbox(label="Skip future confirmations for this tool", value=False)

    def compose(self) -> ComposeResult:
        yield Vertical(
            Label(f"Confirm tool: {self.request.tool_name}", id="tool-title"),
            Label(f"Args: {self.request.args}"),
            self.skip_future,
            Horizontal(
                Button("Yes", id="yes", variant="success"),
                Button("No", id="no", variant="error"),
                id="actions",
            ),
            id="modal-body",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        from tunacode.types import ToolConfirmationResponse

        approved = event.button.id == "yes"
        response = ToolConfirmationResponse(
            approved=approved,
            skip_future=self.skip_future.value,
            abort=not approved,
        )
        self.app.post_message(ToolConfirmationResult(response=response))
        self.app.pop_screen()
