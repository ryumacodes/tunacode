from __future__ import annotations

from textual import events
from textual.app import App, ComposeResult

from tunacode.ui.widgets.editor import Editor


class EditorTestApp(App[None]):
    def compose(self) -> ComposeResult:
        self.editor = Editor()
        yield self.editor


async def test_editor_single_line_paste_inserts_once() -> None:
    app = EditorTestApp()
    text = "Hello! Ready to work on some code. What are we building?"

    async with app.run_test(headless=True) as pilot:
        app.editor.focus()
        app.editor.post_message(events.Paste(text))
        await pilot.pause(0.1)

    assert app.editor.value == text
    assert app.editor.has_paste_buffer is False


async def test_editor_multiline_paste_uses_buffer_without_inserting_first_line() -> None:
    app = EditorTestApp()
    text = "line1\nline2"

    async with app.run_test(headless=True) as pilot:
        app.editor.focus()
        app.editor.post_message(events.Paste(text))
        await pilot.pause(0.1)

    assert app.editor.value == ""
    assert app.editor.has_paste_buffer is True
    assert app.editor.paste_summary == "[[ 2 lines ]]"
