from __future__ import annotations

from types import SimpleNamespace

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


async def test_run_upgrade_command_retries_uv_tool_with_active_python(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_python = "/tmp/tool-venv/bin/python"
    fake_uv = "/usr/local/bin/uv"
    retry_message = (
        "error: Failed to upgrade tunacode-cli\n"
        "  Caused by: `tunacode-cli` is not installed; "
        "run `uv tool install tunacode-cli` to install"
    )
    writes: list[str] = []
    app = SimpleNamespace(
        chat_container=SimpleNamespace(write=lambda message: writes.append(message))
    )
    calls: list[list[str]] = []
    results = iter(
        [
            SimpleNamespace(returncode=1, stderr=retry_message),
            SimpleNamespace(returncode=0, stderr=""),
        ]
    )

    monkeypatch.setattr(update.sys, "executable", fake_python)
    monkeypatch.setattr(update.shutil, "which", lambda name: fake_uv if name == "uv" else None)

    def fake_run(
        cmd: list[str],
        *,
        capture_output: bool,
        text: bool,
        timeout: int,
    ) -> SimpleNamespace:
        assert capture_output is True
        assert text is True
        assert timeout == update.UPDATE_INSTALL_TIMEOUT_SECONDS
        calls.append(cmd)
        return next(results)

    monkeypatch.setattr("subprocess.run", fake_run)

    returncode, stderr = await update._run_upgrade_command(
        app,
        [fake_uv, "tool", "upgrade", "tunacode-cli"],
        "uv tool",
        "tunacode-cli",
    )

    assert returncode == 0
    assert stderr == ""
    assert calls == [
        [fake_uv, "tool", "upgrade", "tunacode-cli"],
        [fake_uv, "pip", "install", "--python", fake_python, "--upgrade", "tunacode-cli"],
    ]
    assert writes == [
        "uv tool could not locate this install; retrying with uv pip against the active Python..."
    ]


async def test_run_upgrade_command_does_not_retry_for_unrelated_uv_tool_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_uv = "/usr/local/bin/uv"
    writes: list[str] = []
    app = SimpleNamespace(
        chat_container=SimpleNamespace(write=lambda message: writes.append(message))
    )
    calls: list[list[str]] = []

    monkeypatch.setattr(update.shutil, "which", lambda name: fake_uv if name == "uv" else None)

    def fake_run(
        cmd: list[str],
        *,
        capture_output: bool,
        text: bool,
        timeout: int,
    ) -> SimpleNamespace:
        assert capture_output is True
        assert text is True
        assert timeout == update.UPDATE_INSTALL_TIMEOUT_SECONDS
        calls.append(cmd)
        return SimpleNamespace(returncode=1, stderr="error: network timeout")

    monkeypatch.setattr("subprocess.run", fake_run)

    returncode, stderr = await update._run_upgrade_command(
        app,
        [fake_uv, "tool", "upgrade", "tunacode-cli"],
        "uv tool",
        "tunacode-cli",
    )

    assert returncode == 1
    assert stderr == "error: network timeout"
    assert calls == [[fake_uv, "tool", "upgrade", "tunacode-cli"]]
    assert writes == []
