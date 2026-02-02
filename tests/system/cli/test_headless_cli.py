"""Tests for headless CLI mode."""

import os
import re
import subprocess

TEST_TIMEOUT_SECONDS = 15
HELP_OUTPUT_COLUMNS = 120
NO_COLOR_ENV_VAR = "NO_COLOR"
NO_COLOR_ENV_VALUE = "1"
ANSI_ESCAPE_REGEX = r"\x1b\[[0-?]*[ -/]*[@-~]"
ANSI_ESCAPE_PATTERN = re.compile(ANSI_ESCAPE_REGEX)


def _strip_ansi(text: str) -> str:
    return ANSI_ESCAPE_PATTERN.sub("", text)


def _run_headless_help() -> subprocess.CompletedProcess[str]:
    help_env = os.environ.copy()
    help_env["COLUMNS"] = str(HELP_OUTPUT_COLUMNS)
    help_env[NO_COLOR_ENV_VAR] = NO_COLOR_ENV_VALUE

    return subprocess.run(
        ["tunacode", "run", "--help"],
        capture_output=True,
        text=True,
        timeout=TEST_TIMEOUT_SECONDS,
        env=help_env,
    )


def test_run_command_exists_and_shows_help() -> None:
    """Verify the run command exists and shows help."""
    result = _run_headless_help()
    assert result.returncode == 0

    output = _strip_ansi(result.stdout)
    assert "Run TunaCode in non-interactive headless mode" in output
    assert "--auto-approve" in output
    assert "--output-json" in output
    assert "--timeout" in output
    assert "--cwd" in output
    assert "--model" in output


def test_run_command_executes_without_tui() -> None:
    """Verify headless mode doesn't import Textual during execution."""
    result = subprocess.run(
        ["tunacode", "run", "echo test", "--auto-approve", "--timeout", "5"],
        capture_output=True,
        text=True,
        timeout=TEST_TIMEOUT_SECONDS,
    )
    # Should complete without TUI (exit code 0 or model error, not import error)
    # The command may fail due to no API key, but it shouldn't have Textual errors
    assert "Textual" not in result.stderr
    # Exit code 0=success, 1=model/network error is OK (not import failures)
    assert result.returncode in (0, 1)
