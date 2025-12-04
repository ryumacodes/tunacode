"""Native Textual widget for error display."""

from __future__ import annotations

from typing import Any

from textual.app import ComposeResult
from textual.widgets import Collapsible, Label, Static


class ErrorDisplay(Static):
    """Native Textual widget for structured error display.

    Uses Collapsible for expandable context details.
    CSS classes for severity:
    - .error-panel.error
    - .error-panel.warning
    - .error-panel.info
    """

    DEFAULT_CSS = """
    ErrorDisplay {
        border: solid $error;
        background: $surface;
        padding: 0 1;
        margin: 0 0 1 0;
        height: auto;
    }

    ErrorDisplay.warning {
        border: solid $warning;
    }

    ErrorDisplay.info {
        border: solid $secondary;
    }

    ErrorDisplay .error-title {
        text-style: bold;
        color: $error;
    }

    ErrorDisplay.warning .error-title {
        color: $warning;
    }

    ErrorDisplay.info .error-title {
        color: $secondary;
    }

    ErrorDisplay .error-message {
        margin: 1 0;
    }

    ErrorDisplay .suggested-fix {
        color: $success;
        margin-top: 1;
    }

    ErrorDisplay .recovery-command {
        color: $primary;
        margin-left: 2;
    }
    """

    def __init__(
        self,
        error_type: str,
        message: str,
        suggested_fix: str | None = None,
        recovery_commands: list[str] | None = None,
        context: dict[str, Any] | None = None,
        severity: str = "error",
    ) -> None:
        super().__init__()
        self.error_type = error_type
        self.message = message
        self.suggested_fix = suggested_fix
        self.recovery_commands = recovery_commands
        self.context = context
        self.severity = severity

        self.add_class("error-panel")
        self.add_class(severity)

    def compose(self) -> ComposeResult:
        yield Label(self.error_type, classes="error-title")
        yield Static(self.message, classes="error-message")

        if self.suggested_fix:
            yield Static(f"Fix: {self.suggested_fix}", classes="suggested-fix")

        if self.recovery_commands:
            yield Label("Recovery:", classes="recovery-label")
            for cmd in self.recovery_commands:
                yield Static(cmd, classes="recovery-command")

        if self.context:
            with Collapsible(title="Details", collapsed=True):
                for key, value in self.context.items():
                    yield Static(f"{key}: {value}")
