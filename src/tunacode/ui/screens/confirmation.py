"""Tool confirmation modal screen."""

from __future__ import annotations

from typing import TYPE_CHECKING

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.message import Message
from textual.screen import ModalScreen
from textual.widgets import Button, Checkbox, Label

if TYPE_CHECKING:
    from tunacode.types import ToolConfirmationRequest, ToolConfirmationResponse

BUTTON_ID_YES = "yes"
BUTTON_ID_NO = "no"


class ToolConfirmationResult(Message):
    """Result of a tool confirmation modal."""

    def __init__(self, *, response: "ToolConfirmationResponse") -> None:
        super().__init__()
        self.response = response


class ToolConfirmationModal(ModalScreen[None]):
    """Modal that gathers tool confirmation asynchronously."""

    BINDINGS = [
        Binding("1", "approve", "Yes"),
        Binding("2", "approve_skip", "Yes + Skip"),
        Binding("3", "reject", "No"),
        Binding("escape", "reject", "Cancel", show=False),
    ]

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
                Button("Yes", id=BUTTON_ID_YES, variant="success"),
                Button("No", id=BUTTON_ID_NO, variant="error"),
                id="actions",
            ),
            id="modal-body",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        from tunacode.types import ToolConfirmationResponse

        approved = event.button.id == BUTTON_ID_YES
        response = ToolConfirmationResponse(
            approved=approved,
            skip_future=self.skip_future.value,
            abort=not approved,
        )
        self.app.post_message(ToolConfirmationResult(response=response))
        self.app.pop_screen()

    def action_approve(self) -> None:
        """Approve tool execution (key 1)."""
        from tunacode.types import ToolConfirmationResponse

        response = ToolConfirmationResponse(approved=True, skip_future=False, abort=False)
        self.app.post_message(ToolConfirmationResult(response=response))
        self.app.pop_screen()

    def action_approve_skip(self) -> None:
        """Approve and skip future confirmations (key 2)."""
        from tunacode.types import ToolConfirmationResponse

        response = ToolConfirmationResponse(approved=True, skip_future=True, abort=False)
        self.app.post_message(ToolConfirmationResult(response=response))
        self.app.pop_screen()

    def action_reject(self) -> None:
        """Reject tool execution (key 3 or Escape)."""
        from tunacode.types import ToolConfirmationResponse

        response = ToolConfirmationResponse(approved=False, skip_future=False, abort=True)
        self.app.post_message(ToolConfirmationResult(response=response))
        self.app.pop_screen()
