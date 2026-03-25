from __future__ import annotations

from rich.text import Text

from tunacode.core.session import StateManager

from tunacode.ui.app import TextualReplApp
from tunacode.ui.widgets.messages import TuiLogDisplay


class _FakeChatContainer:
    def __init__(self) -> None:
        self.calls: list[object] = []

    def write(self, content: object, **_kwargs: object) -> None:
        self.calls.append(content)


def test_tui_log_display_is_written_via_message_handler() -> None:
    app = TextualReplApp(state_manager=StateManager())
    app.chat_container = _FakeChatContainer()  # type: ignore[assignment]

    renderable = Text("thread-safe log")
    app.on_tui_log_display(TuiLogDisplay(renderable=renderable))

    assert app.chat_container.calls == [renderable]
