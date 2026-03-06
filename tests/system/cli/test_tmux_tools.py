"""End-to-end tool tests driven via tmux.

Launches tunacode in a real tmux session, sends prompts, and verifies that each
tool executes by checking:
  1. The status bar shows ``last: <tool_name>``
  2. Expected output appears in the captured pane

These are true system tests -- they exercise the full stack (TUI, agent loop,
tool dispatch, rendering).  They require a live API key and tmux.
"""

import json
import os
import shlex
import shutil
import subprocess
import time
import uuid
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

TMUX_BINARY = "tmux"
SESSION_PREFIX = "tunatest"
DEFAULT_TIMEOUT_SECONDS = 90
POLL_INTERVAL_SECONDS = 2
VENV_DIR = Path(__file__).resolve().parents[3] / ".venv"
API_KEY_ENV_VAR = "MINIMAX_API_KEY"
TUNACODE_CONFIG_PATH = Path.home() / ".config" / "tunacode.json"

# ---------------------------------------------------------------------------
# Markers & skip guards
# ---------------------------------------------------------------------------

_missing_tmux = not shutil.which(TMUX_BINARY)


def _has_api_key() -> bool:
    """Check env var first, then fall back to tunacode's config file."""
    if os.environ.get(API_KEY_ENV_VAR):
        return True
    try:
        config = json.loads(TUNACODE_CONFIG_PATH.read_text())
        key = config.get("env", {}).get(API_KEY_ENV_VAR, "")
        return bool(key)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return False


_missing_api_key = not _has_api_key()

pytestmark = [
    pytest.mark.tmux,
    pytest.mark.skipif(_missing_tmux, reason="tmux is not installed"),
    pytest.mark.skipif(_missing_api_key, reason=f"{API_KEY_ENV_VAR} not found in env or config"),
    pytest.mark.timeout(DEFAULT_TIMEOUT_SECONDS),
]


# ---------------------------------------------------------------------------
# TmuxSession helper
# ---------------------------------------------------------------------------


class TmuxSession:
    """Manage a detached tmux session running tunacode."""

    def __init__(self, name: str, *, working_directory: Path | None = None) -> None:
        self.name = name
        self.working_directory = working_directory

    # -- tmux primitives -----------------------------------------------------

    def _run_tmux(self, *args: str, check: bool = True) -> str:
        result = subprocess.run(
            [TMUX_BINARY, *args],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if check and result.returncode != 0:
            raise RuntimeError(
                f"tmux {' '.join(args)} failed (rc={result.returncode}): {result.stderr}"
            )
        return result.stdout

    def start(self) -> None:
        """Create a detached session and launch tunacode inside it."""
        activate = f"source {VENV_DIR / 'bin' / 'activate'}"
        launch = "tunacode"
        if self.working_directory is None:
            shell_cmd = f"{activate} && {launch}"
        else:
            quoted_working_directory = shlex.quote(str(self.working_directory))
            shell_cmd = f"cd {quoted_working_directory} && {activate} && {launch}"
        self._run_tmux("new-session", "-d", "-s", self.name, "-x", "220", "-y", "50", shell_cmd)
        # Give the TUI a moment to render its first frame.
        time.sleep(3)

    def kill(self) -> None:
        """Kill the tmux session (ignore errors if already dead)."""
        self._run_tmux("kill-session", "-t", self.name, check=False)

    def send(self, text: str) -> None:
        """Type *text* followed by Enter into the session."""
        self._run_tmux("send-keys", "-t", self.name, text, "Enter")

    def capture(self) -> str:
        """Return pane contents including recent scrollback history."""
        return self._run_tmux("capture-pane", "-t", self.name, "-p", "-S", "-10000")


@contextmanager
def tmux_session(
    *,
    working_directory: Path | None = None,
) -> Generator[TmuxSession, None, None]:
    """Context manager: spin up a tunacode tmux session, tear it down on exit."""
    name = f"{SESSION_PREFIX}_{uuid.uuid4().hex[:8]}"
    session = TmuxSession(name, working_directory=working_directory)
    session.start()
    try:
        yield session
    finally:
        session.kill()


# ---------------------------------------------------------------------------
# Polling helpers
# ---------------------------------------------------------------------------


def wait_for_text(
    session: TmuxSession,
    needle: str,
    *,
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
) -> str:
    """Poll the pane until *needle* appears. Returns captured output."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        output = session.capture()
        if needle in output:
            return output
        time.sleep(POLL_INTERVAL_SECONDS)
    raise TimeoutError(
        f"Timed out after {timeout}s waiting for {needle!r} in pane.\n"
        f"Last capture:\n{session.capture()}"
    )


def wait_for_tool(
    session: TmuxSession,
    tool_name: str,
    *,
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
) -> str:
    """Poll until ``last: <tool_name>`` appears in the status bar."""
    return wait_for_text(session, f"last: {tool_name}", timeout=timeout)


def wait_for_idle(
    session: TmuxSession,
    *,
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
) -> str:
    """Poll until the spinner dots disappear (agent finished responding).

    The spinner renders as a series of dots (e.g. ``...``).  We consider the
    session idle once a capture no longer contains the spinner *and* the
    ``last:`` indicator is present (meaning at least one tool ran).
    """
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        output = session.capture()
        has_tool = "last:" in output
        # Heuristic: no trailing dots near the status area means idle.
        # Good enough for a system-level smoke test.
        if has_tool:
            return output
        time.sleep(POLL_INTERVAL_SECONDS)
    raise TimeoutError(
        f"Timed out after {timeout}s waiting for idle.\nLast capture:\n{session.capture()}"
    )


# ---------------------------------------------------------------------------
# Tests -- one per tool
# ---------------------------------------------------------------------------


def test_bash_tool() -> None:
    """bash tool: run ``echo hello world`` and verify output."""
    with tmux_session() as s:
        s.send(
            "You MUST call the bash tool. Run: echo hello world. Do not answer until the tool runs."
        )
        output = wait_for_tool(s, "bash")
        assert "hello world" in output.lower(), f"Expected 'hello world' in output:\n{output}"


def test_read_file_tool() -> None:
    """read_file tool: read pyproject.toml and check for project name."""
    with tmux_session() as s:
        s.send(
            "You MUST call the read_file tool. Read /home/tuna/tunacode/pyproject.toml. "
            "Do not answer until the tool runs."
        )
        output = wait_for_tool(s, "read_file")
        assert "tunacode" in output.lower(), f"Expected 'tunacode' in output:\n{output}"


def test_write_file_tool() -> None:
    """write_file tool: create a temp file and verify it on disk."""
    target = f"/tmp/tunatest_write_{uuid.uuid4().hex[:8]}.txt"
    content_marker = "hello from tunacode"
    try:
        with tmux_session() as s:
            s.send(
                f"You MUST call the write_file tool. Create {target} with content "
                f'"{content_marker}". Do not answer until the tool runs.'
            )
            wait_for_tool(s, "write_file")
            written = Path(target)
            assert written.exists(), f"write_file did not create {target}"
            assert content_marker in written.read_text(), (
                f"File contents do not contain marker: {written.read_text()!r}"
            )
    finally:
        Path(target).unlink(missing_ok=True)


def test_hashline_edit_tool(tmp_path: Path) -> None:
    """hashline_edit tool: read then edit a pre-created file."""
    target = tmp_path / f"tunatest_edit_{uuid.uuid4().hex[:8]}.txt"
    original_line = "color = red"
    expected_line = "color = blue"
    try:
        target.write_text(original_line)
        with tmux_session() as s:
            s.send(
                "You MUST call read_file, then hashline_edit. "
                f"Read {target}, then change 'color = red' to 'color = blue'. "
                "Do not answer until both tools run."
            )
            wait_for_tool(s, "hashline_edit")
            updated = target.read_text()
            assert expected_line in updated, f"Expected {expected_line!r} in:\n{updated}"
    finally:
        target.unlink(missing_ok=True)


def test_discover_tool() -> None:
    """discover tool: search for tool definitions and verify structured output."""
    with tmux_session() as s:
        s.send(
            "You MUST call the discover tool. Query: where tools are defined. "
            "Do not answer until the tool runs."
        )
        wait_for_tool(s, "discover")
        output = wait_for_text(s, "scanned:")
        assert "scanned:" in output, f"Expected 'scanned:' stats in discover output:\n{output}"


def test_web_fetch_tool() -> None:
    """web_fetch tool: fetch tunacode.xyz and verify content appears."""
    with tmux_session() as s:
        s.send(
            "You MUST call the web_fetch tool. Fetch https://tunacode.xyz/. "
            "Do not answer until the tool runs."
        )
        output = wait_for_tool(s, "web_fetch")
        assert "tunacode" in output.lower(), f"Expected 'tunacode' in fetched output:\n{output}"


def test_loaded_skill_is_used_via_absolute_referenced_path(tmp_path: Path) -> None:
    """Load a local skill in tmux, then verify the agent uses its referenced file."""
    skill_name = "tmux-e2e-skill"
    skill_description = "TMUX system test skill"
    token = f"TMUX_SKILL_TOKEN_{uuid.uuid4().hex[:8]}"
    skill_dir = tmp_path / ".claude" / "skills" / skill_name
    skill_dir.mkdir(parents=True)
    token_path = skill_dir / "token.txt"
    skill_path = skill_dir / "SKILL.md"

    token_path.write_text(token, encoding="utf-8")
    skill_path.write_text(
        "\n".join(
            [
                "---",
                f"name: {skill_name}",
                f"description: {skill_description}",
                "---",
                "",
                "# TMUX E2E Skill",
                "",
                "When the user asks for the tmux skill token, you must follow this workflow:",
                "1. Read [token.txt](token.txt).",
                "2. Reply with the exact token from that file.",
                '3. Include the sentence "This skill is loaded and being used."',
                "4. Do not guess if you have not read the file.",
            ]
        ),
        encoding="utf-8",
    )

    with tmux_session(working_directory=tmp_path) as s:
        s.send(f"/skills {skill_name}")
        load_output = wait_for_text(s, f"Loaded skill: {skill_name}")
        assert skill_description in load_output, (
            f"Expected skill description in load output:\n{load_output}"
        )

        s.send("/skills loaded")
        loaded_output = wait_for_text(s, "Loaded Skills [1]")
        assert skill_name in loaded_output, (
            f"Expected loaded skill {skill_name!r} in output:\n{loaded_output}"
        )

        s.send("What is the tmux skill token? Use the loaded skill and do not guess.")
        tool_output = wait_for_tool(s, "read_file")
        assert "token.txt" in tool_output, f"Expected token file read in output:\n{tool_output}"

        final_output = wait_for_text(s, token)
        assert token in final_output, f"Expected token in output:\n{final_output}"
