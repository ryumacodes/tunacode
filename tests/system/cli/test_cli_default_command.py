"""Tests for CLI default command behavior."""

import os
import subprocess

TEST_TIMEOUT_SECONDS = 30
HELP_OUTPUT_COLUMNS = 120


def _run_cli_help() -> subprocess.CompletedProcess[str]:
    help_env = os.environ.copy()
    help_env["COLUMNS"] = str(HELP_OUTPUT_COLUMNS)

    return subprocess.run(
        ["tunacode", "--help"],
        capture_output=True,
        text=True,
        timeout=TEST_TIMEOUT_SECONDS,
        env=help_env,
    )


def test_cli_help_lists_run_command() -> None:
    result = _run_cli_help()
    assert result.returncode == 0
    assert "TunaCode - OS AI-powered development assistant" in result.stdout
    assert "run" in result.stdout
    assert "--setup" in result.stdout


def test_cli_help_hides_main_alias() -> None:
    result = _run_cli_help()
    assert result.returncode == 0
    assert "\n│ main" not in result.stdout
