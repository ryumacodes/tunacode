from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from tunacode.core.session import StateManager

from tunacode.ui.app import TextualReplApp
from tunacode.ui.widgets.messages import EditorSubmitRequested


class _FakeLoadingIndicator:
    def __init__(self, events: list[str]) -> None:
        self._events = events
        self.active = False

    def add_class(self, name: str) -> None:
        self._events.append(f"loading.add_class:{name}")
        self.active = True

    def remove_class(self, name: str) -> None:
        self._events.append(f"loading.remove_class:{name}")
        self.active = False


class _FakeMessageWidget:
    def __init__(self, events: list[str]) -> None:
        self._events = events

    def add_class(self, name: str) -> _FakeMessageWidget:
        self._events.append(f"message.add_class:{name}")
        return self


class _FakeChatContainer:
    def __init__(self, events: list[str]) -> None:
        self._events = events
        self.size = SimpleNamespace(width=80)

    def write(self, _content: object, **_kwargs: object) -> _FakeMessageWidget:
        self._events.append("chat.write")
        return _FakeMessageWidget(self._events)


class _FakeQueue:
    def __init__(self, events: list[str]) -> None:
        self._events = events
        self.items: list[str] = []

    def put_nowait(self, item: str) -> None:
        self._events.append(f"queue.put_nowait:{item}")
        self.items.append(item)


@pytest.mark.asyncio
async def test_submit_shows_loading_and_schedules_queue_after_refresh() -> None:
    events: list[str] = []
    app = TextualReplApp(state_manager=StateManager())
    app.loading_indicator = _FakeLoadingIndicator(events)
    app.chat_container = _FakeChatContainer(events)
    fake_queue = _FakeQueue(events)
    app.request_queue = fake_queue  # type: ignore[assignment]

    scheduled_callbacks: list[object] = []

    def _fake_call_after_refresh(callback: object) -> None:
        events.append("call_after_refresh")
        scheduled_callbacks.append(callback)

    app.call_after_refresh = _fake_call_after_refresh  # type: ignore[method-assign]

    with patch("tunacode.ui.commands.handle_command", new=AsyncMock(return_value=False)):
        await app.on_editor_submit_requested(EditorSubmitRequested(text="hello", raw_text="hello"))

    assert fake_queue.items == []
    assert app._loading_indicator_shown is True
    assert app.loading_indicator.active is True
    assert len(scheduled_callbacks) == 1
    assert events.index("loading.add_class:active") < events.index("call_after_refresh")

    callback = scheduled_callbacks[0]
    assert callable(callback)
    callback()

    assert fake_queue.items == ["hello"]
    assert events.index("call_after_refresh") < events.index("queue.put_nowait:hello")
