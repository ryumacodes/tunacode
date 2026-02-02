"""Tests for CLI default command behavior."""

import os
import re
import subprocess

TEST_TIMEOUT_SECONDS = 30
HELP_OUTPUT_COLUMNS = 120
NO_COLOR_ENV_VAR = "NO_COLOR"
NO_COLOR_ENV_VALUE = "1"
ANSI_ESCAPE_REGEX = r"\x1b\[[0-?]*[ -/]*[@-~]"
ANSI_ESCAPE_PATTERN = re.compile(ANSI_ESCAPE_REGEX)


def _strip_ansi(text: str) -> str:
    return ANSI_ESCAPE_PATTERN.sub("", text)


def _run_cli_help() -> subprocess.CompletedProcess[str]:
    help_env = os.environ.copy()
    help_env["COLUMNS"] = str(HELP_OUTPUT_COLUMNS)
    help_env[NO_COLOR_ENV_VAR] = NO_COLOR_ENV_VALUE

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

    output = _strip_ansi(result.stdout)
    assert "TunaCode - OS AI-powered development assistant" in output
    assert "run" in output
    assert "--setup" in output


def test_cli_help_hides_main_alias() -> None:
    result = _run_cli_help()
    assert result.returncode == 0

    output = _strip_ansi(result.stdout)
    assert "\n│ main" not in output
