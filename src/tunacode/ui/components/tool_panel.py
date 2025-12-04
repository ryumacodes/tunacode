"""Native Textual widget for tool execution display."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from textual.app import ComposeResult
from textual.widgets import Label, Static


class ToolPanel(Static):
    """Native Textual panel for tool results.

    Uses CSS classes for status-based styling:
    - .tool-panel.running
    - .tool-panel.completed
    - .tool-panel.failed
    """

    DEFAULT_CSS = """
    ToolPanel {
        border: solid $primary;
        background: $surface;
        padding: 0 1;
        margin: 0 0 1 0;
        height: auto;
    }

    ToolPanel.running {
        border: solid $accent;
    }

    ToolPanel.completed {
        border: solid $success;
    }

    ToolPanel.failed {
        border: solid $error;
    }

    ToolPanel .tool-title {
        text-style: bold;
        margin-bottom: 1;
    }

    ToolPanel .tool-args {
        color: $text-muted;
    }

    ToolPanel .tool-result {
        margin-top: 1;
    }

    ToolPanel .tool-duration {
        color: $text-muted;
        text-align: right;
    }
    """

    def __init__(
        self,
        tool_name: str,
        status: str,
        args: dict[str, Any] | None = None,
        result: str | None = None,
        duration_ms: float | None = None,
        timestamp: datetime | None = None,
    ) -> None:
        super().__init__()
        self.tool_name = tool_name
        self.status = status
        self.args = args or {}
        self.result = result
        self.duration_ms = duration_ms
        self.timestamp = timestamp or datetime.now()

        self.add_class("tool-panel")
        self.add_class(status)

    def compose(self) -> ComposeResult:
        status_suffix = {"running": "...", "completed": "done", "failed": "fail"}.get(
            self.status, self.status
        )

        yield Label(f"{self.tool_name} [{status_suffix}]", classes="tool-title")

        if self.args:
            args_text = "\n".join(f"  {k}: {_truncate(v)}" for k, v in self.args.items())
            yield Static(args_text, classes="tool-args")

        if self.result:
            yield Static(_truncate(self.result, 200), classes="tool-result")

        if self.duration_ms is not None:
            yield Static(f"{self.duration_ms:.0f}ms", classes="tool-duration")


def _truncate(value: Any, max_length: int = 60) -> str:
    s = str(value)
    if len(s) <= max_length:
        return s
    return s[: max_length - 3] + "..."
