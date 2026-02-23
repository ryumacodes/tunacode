from __future__ import annotations

from tunacode.constants import MAX_CALLBACK_CONTENT

from tunacode.ui import repl_support

DIAGNOSTICS_LINE: str = "Error (line 10): type mismatch"
FILLER_UNIT: str = "x"
NEWLINE: str = "\n"


def test_truncate_for_safety_preserves_diagnostics_block() -> None:
    diagnostics_block: str = (
        f"{repl_support.DIAGNOSTICS_BLOCK_START}{NEWLINE}"
        f"{DIAGNOSTICS_LINE}{NEWLINE}"
        f"{repl_support.DIAGNOSTICS_BLOCK_END}{NEWLINE}"
    )
    overflow_length: int = MAX_CALLBACK_CONTENT + len(diagnostics_block)
    filler: str = FILLER_UNIT * overflow_length
    content: str = f"{diagnostics_block}{filler}"

    truncated: str | None = repl_support._truncate_for_safety(content)

    assert truncated is not None
    assert truncated.startswith(diagnostics_block)
    assert DIAGNOSTICS_LINE in truncated
    assert truncated.endswith(repl_support.CALLBACK_TRUNCATION_NOTICE)


class _FakeStatusBar:
    def __init__(self) -> None:
        self.events: list[tuple[str, str]] = []
        self.edited_files: list[str] = []

    def add_edited_file(self, filepath: str) -> None:
        self.edited_files.append(filepath)

    def update_last_action(self, tool_name: str) -> None:
        self.events.append(("last", tool_name))

    def update_running_action(self, tool_name: str) -> None:
        self.events.append(("running", tool_name))

    def complete_running_action(self, tool_name: str) -> None:
        self.events.append(("complete", tool_name))


class _FakeApp:
    def __init__(self) -> None:
        self.status_bar = _FakeStatusBar()
        self.posted_messages: list[object] = []
        self.updated_lsp_files: list[str] = []

    def post_message(self, message: object) -> bool:
        self.posted_messages.append(message)
        return True

    def update_lsp_for_file(self, filepath: str) -> None:
        self.updated_lsp_files.append(filepath)


def test_tool_callbacks_complete_running_before_marking_last() -> None:
    app = _FakeApp()
    start_callback = repl_support.build_tool_start_callback(app)
    result_callback = repl_support.build_tool_result_callback(app)

    start_callback("write_file")
    start_callback("bash")

    result_callback(
        "write_file",
        "completed",
        {"filepath": "src/example.py"},
        "ok",
        12.0,
    )
    result_callback(
        "bash",
        "completed",
        {},
        "done",
        8.0,
    )

    assert app.status_bar.events == [
        ("running", "write_file"),
        ("running", "bash"),
        ("complete", "write_file"),
        ("last", "write_file"),
        ("complete", "bash"),
        ("last", "bash"),
    ]
    assert app.status_bar.edited_files == ["src/example.py"]
    assert app.updated_lsp_files == ["src/example.py"]
    assert len(app.posted_messages) == 2
