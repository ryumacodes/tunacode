"""Status bar widget for TunaCode REPL."""

from __future__ import annotations

import os
import subprocess
from typing import TYPE_CHECKING

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Static

if TYPE_CHECKING:
    pass

# Maximum length for operation text in status bar
MAX_STATUS_OPERATION_LEN = 25


class StatusBar(Horizontal):
    """Bottom status bar - 3 zones."""

    def __init__(self) -> None:
        super().__init__()
        self._edited_files: set[str] = set()
        self._location_text: str = ""
        self._last_action: str = "-"
        self._running_actions: dict[str, int] = {}
        self._running_focus: str | None = None

    def compose(self) -> ComposeResult:
        yield Static("main ● ~/proj", id="status-left")
        yield Static("edited: -", id="status-mid")
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
        self._location_text = f"{branch} ● {dirname}"
        self.query_one("#status-left", Static).update(self._location_text)

    def _truncate_status_operation(self, operation_name: str) -> str:
        if len(operation_name) <= MAX_STATUS_OPERATION_LEN:
            return operation_name
        max_prefix_length = MAX_STATUS_OPERATION_LEN - 3
        if max_prefix_length <= 0:
            return operation_name[:MAX_STATUS_OPERATION_LEN]
        return f"{operation_name[:max_prefix_length]}..."

    def _total_running_actions(self) -> int:
        return sum(self._running_actions.values())

    def _update_right_status(self) -> None:
        right_status = self.query_one("#status-right", Static)
        running_total = self._total_running_actions()
        if running_total > 0:
            focus = self._running_focus
            if focus is None or focus not in self._running_actions:
                focus = next(reversed(self._running_actions))
                self._running_focus = focus
            focus_text = self._truncate_status_operation(focus)
            overflow_suffix = f" +{running_total - 1}" if running_total > 1 else ""
            right_status.update(f"running: {focus_text}{overflow_suffix}")
            return
        right_status.update(f"last: {self._last_action}")

    def update_last_action(self, tool_name: str) -> None:
        normalized_name = tool_name.strip() if tool_name.strip() else "-"
        self._last_action = self._truncate_status_operation(normalized_name)
        self._update_right_status()

    def update_running_action(self, tool_name: str) -> None:
        normalized_name = tool_name.strip() if tool_name.strip() else "unknown"
        self._running_actions[normalized_name] = self._running_actions.get(normalized_name, 0) + 1
        self._running_focus = normalized_name
        self._update_right_status()

    def complete_running_action(self, tool_name: str) -> None:
        normalized_name = tool_name.strip() if tool_name.strip() else "unknown"
        running_count = self._running_actions.get(normalized_name)
        if running_count is None:
            return
        if running_count <= 1:
            self._running_actions.pop(normalized_name, None)
        else:
            self._running_actions[normalized_name] = running_count - 1

        if not self._running_actions:
            self._running_focus = None
        elif self._running_focus not in self._running_actions:
            self._running_focus = next(reversed(self._running_actions))
        self._update_right_status()

    def add_edited_file(self, filepath: str) -> None:
        """Track an edited file and update display."""
        filename = os.path.basename(filepath)
        self._edited_files.add(filename)
        self._update_edited_display()

    def _update_edited_display(self) -> None:
        """Update mid zone with edited files list."""
        files = sorted(self._edited_files)
        if not files:
            text = "edited: -"
        elif len(files) <= 3:
            text = f"edited: {', '.join(files)}"
        else:
            shown = ", ".join(files[:2])
            text = f"edited: {shown} +{len(files) - 2}"
        self.query_one("#status-mid", Static).update(text)

    def set_mode(self, mode: str | None) -> None:
        """Show mode indicator in status bar."""
        left = self.query_one("#status-left", Static)
        if mode:
            left.add_class("mode-active")
            left.update(f"[{mode}] {self._location_text}")
        else:
            left.remove_class("mode-active")
            left.update(self._location_text)
