from __future__ import annotations

from unittest.mock import patch

from rich.text import Text

from tunacode.core.session import StateManager

from tunacode.ui.app import TextualReplApp
from tunacode.ui.lifecycle import AppLifecycle
from tunacode.ui.request_bridge import RequestUiBridge
from tunacode.ui.widgets.messages import TuiLogDisplay


class _FakeChatContainer:
    def __init__(self) -> None:
        self.calls: list[object] = []

    def write(self, content: object, **_kwargs: object) -> None:
        self.calls.append(content)


class _FakeLogger:
    def __init__(self) -> None:
        self.state_manager: StateManager | None = None
        self.tui_callback: object | None = None

    def set_state_manager(self, state_manager: StateManager) -> None:
        self.state_manager = state_manager

    def set_tui_callback(self, callback: object) -> None:
        self.tui_callback = callback


class _FakeBridgeApp:
    def __init__(self) -> None:
        self.messages: list[object] = []

    def post_message(self, message: object) -> bool:
        self.messages.append(message)
        return True


def test_tui_log_display_is_written_via_message_handler() -> None:
    app = TextualReplApp(state_manager=StateManager())
    app.chat_container = _FakeChatContainer()  # type: ignore[assignment]

    renderable = Text("thread-safe log")
    app.on_tui_log_display(TuiLogDisplay(renderable=renderable))

    assert app.chat_container.calls == [renderable]


def test_logger_tui_callback_posts_message_not_widget_write() -> None:
    app = TextualReplApp(state_manager=StateManager())
    app.chat_container = _FakeChatContainer()  # type: ignore[assignment]
    posted_messages: list[object] = []
    app.post_message = posted_messages.append  # type: ignore[method-assign]
    fake_logger = _FakeLogger()

    with patch("tunacode.core.logging.get_logger", return_value=fake_logger):
        AppLifecycle(app)._setup_logger()

    assert fake_logger.state_manager is app.state_manager
    assert callable(fake_logger.tui_callback)

    renderable = Text("queued log")
    fake_logger.tui_callback(renderable)

    assert app.chat_container.calls == []
    assert len(posted_messages) == 1
    message = posted_messages[0]
    assert isinstance(message, TuiLogDisplay)
    assert message.renderable == renderable


async def test_request_ui_bridge_drains_all_chunks_in_order() -> None:
    bridge = RequestUiBridge(_FakeBridgeApp())

    await bridge.streaming_callback("hello")
    await bridge.streaming_callback(" ")
    await bridge.streaming_callback("world")
    await bridge.thinking_callback("thinking")
    await bridge.thinking_callback("...")

    assert bridge.drain_streaming() == "hello world"
    assert bridge.drain_streaming() == ""
    assert bridge.drain_thinking() == "thinking..."
    assert bridge.drain_thinking() == ""
