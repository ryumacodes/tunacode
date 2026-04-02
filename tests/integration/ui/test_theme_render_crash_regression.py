from __future__ import annotations

import asyncio
import time
from pathlib import Path
from unittest.mock import AsyncMock

import pytest
from rich.text import Text

from tunacode.core.session import StateManager
from tunacode.ui.app import TextualReplApp
from tunacode.ui.screens.theme_picker import ThemePickerScreen


async def _wait_until(predicate: object, *, timeout: float, step: float = 0.01) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if callable(predicate) and predicate():
            return
        await asyncio.sleep(step)
    raise AssertionError(f"Condition not met within {timeout:.2f}s")


@pytest.mark.asyncio
async def test_startup_and_theme_changes_do_not_crash_with_dim_default_renderables(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    home_dir = tmp_path / "home"
    data_dir = tmp_path / "xdg-data"
    home_dir.mkdir(exist_ok=True)
    data_dir.mkdir(exist_ok=True)
    monkeypatch.setenv("HOME", str(home_dir))
    monkeypatch.setenv("XDG_DATA_HOME", str(data_dir))

    state_manager = StateManager()
    state_manager.save_session = AsyncMock(return_value=True)  # type: ignore[method-assign]
    app = TextualReplApp(state_manager=state_manager)

    async with app.run_test() as pilot:
        await _wait_until(lambda: len(list(app.query(".chat-message"))) >= 2, timeout=1.0)

        app.chat_container.write(Text("dim-default regression probe", style="dim default on default"))
        await _wait_until(lambda: len(list(app.query(".chat-message"))) >= 3, timeout=1.0)

        for theme_name in ("dracula", "textual-light", "textual-dark", "textual-ansi"):
            app.theme = theme_name
            await pilot.pause()

        app.theme = "textual-dark"
        await pilot.pause()

        picker = ThemePickerScreen(app.supported_themes, app.theme)
        app.push_screen(picker)
        await _wait_until(lambda: picker.is_attached, timeout=1.0)
        await pilot.press("down")
        await _wait_until(lambda: app.theme == "textual-light", timeout=1.0)
        picker.action_cancel()
        await _wait_until(lambda: not picker.is_attached, timeout=1.0)

        assert len(list(app.query(".chat-message"))) >= 3
