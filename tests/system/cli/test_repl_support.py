from __future__ import annotations

from tinyagent.agent_types import AgentToolResult, TextContent

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


class _FakeApp:
    def __init__(self) -> None:
        self.posted_messages: list[object] = []
        self.updated_lsp_files: list[str] = []

    def post_message(self, message: object) -> bool:
        self.posted_messages.append(message)
        return True

    def update_lsp_for_file(self, filepath: str) -> None:
        self.updated_lsp_files.append(filepath)


def test_tool_result_callback_updates_lsp_and_posts_message_for_completed_file_edit() -> None:
    app = _FakeApp()
    result_callback = repl_support.build_tool_result_callback(app)

    result_callback(
        "write_file",
        "completed",
        {"filepath": " src/example.py "},
        AgentToolResult(content=[TextContent(text="ok")], details={}),
        12.0,
    )

    assert app.updated_lsp_files == ["src/example.py"]
    assert len(app.posted_messages) == 1
