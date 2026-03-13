from __future__ import annotations

import pytest

from tunacode.ui.commands import update


def test_should_retry_uv_tool_with_active_python_for_missing_tool_error() -> None:
    stderr = (
        "Failed to upgrade tunacode-cli\n"
        "Caused by: `tunacode-cli` is not installed; run `uv tool install tunacode-cli` to install"
    )

    assert update._should_retry_uv_tool_with_active_python(stderr) is True


def test_should_not_retry_uv_tool_with_active_python_for_other_errors() -> None:
    stderr = "error: network timeout"

    assert update._should_retry_uv_tool_with_active_python(stderr) is False


def test_get_active_python_upgrade_command_uses_current_interpreter(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_python = "/tmp/tool-venv/bin/python"
    fake_uv = "/usr/local/bin/uv"

    monkeypatch.setattr(update.sys, "executable", fake_python)
    monkeypatch.setattr(update.shutil, "which", lambda name: fake_uv if name == "uv" else None)

    cmd_result = update._get_active_python_upgrade_command("tunacode-cli")

    assert cmd_result == (
        [fake_uv, "pip", "install", "--python", fake_python, "--upgrade", "tunacode-cli"],
        "uv pip",
    )


def test_get_active_python_upgrade_command_returns_none_without_uv(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(update.shutil, "which", lambda _name: None)

    assert update._get_active_python_upgrade_command("tunacode-cli") is None
