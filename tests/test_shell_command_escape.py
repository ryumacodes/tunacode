"""Tests for TUI shell command ergonomics (! prefix + Escape)."""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from tunacode.ui.app import TextualReplApp
from tunacode.ui.commands import handle_command


@dataclass
class _FakeEditor:
    value: str
    cleared: bool = False

    def clear_input(self) -> None:
        self.value = ""
        self.cleared = True


@pytest.mark.asyncio
async def test_handle_command_bang_starts_shell_command() -> None:
    started: list[str] = []

    class FakeApp:
        def start_shell_command(self, raw_cmd: str) -> None:
            started.append(raw_cmd)

    handled = await handle_command(FakeApp(), "! ls")
    assert handled is True
    assert [cmd.strip() for cmd in started] == ["ls"]


def test_escape_clears_editor_when_no_streaming_or_shell_running() -> None:
    fake_app = type(
        "FakeApp",
        (),
        {
            "pending_confirmation": None,
            "_current_request_task": None,
            "_shell_command_task": None,
            "editor": _FakeEditor("! ls"),
        },
    )()

    TextualReplApp.action_cancel_stream(fake_app)
    assert fake_app.editor.cleared is True
    assert fake_app.editor.value == ""
