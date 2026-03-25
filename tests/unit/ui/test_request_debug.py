from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from tunacode.ui.request_bridge import RequestUiBridge
from tunacode.ui.request_debug import RequestDebugTracer


class _FakeQueue:
    def __init__(self) -> None:
        self._size = 0

    def qsize(self) -> int:
        return self._size


class _FakeApp:
    STREAM_THROTTLE_MS = 100.0
    MILLISECONDS_PER_SECOND = 1000.0

    def __init__(self) -> None:
        self.state_manager = SimpleNamespace(session=SimpleNamespace(debug_mode=True))
        self.request_queue = _FakeQueue()
        self._loading_indicator_shown = False
        self._current_request_task = None
        self._request_bridge = None
        self.scheduled_callbacks: list[object] = []

    def call_after_refresh(self, callback: object) -> None:
        self.scheduled_callbacks.append(callback)

    def post_message(self, _message: object) -> None:
        return None


def test_request_debug_logs_submit_queue_and_start_timings() -> None:
    app = _FakeApp()
    tracer = RequestDebugTracer(app)
    logger = MagicMock()

    with (
        patch("tunacode.ui.request_debug.get_logger", return_value=logger),
        patch("tunacode.ui.request_debug.time.monotonic", side_effect=[10.0, 10.012, 10.020]),
    ):
        trace = tracer.submit_received(raw_text="hello", normalized_text="hello")
        tracer.request_enqueued_after_refresh(trace)
        tracer.request_started(tracer.pop_next_submission_trace())

    messages = [call.args[0] for call in logger.lifecycle.call_args_list]
    assert messages[0].startswith("Input: submit seq=1")
    assert "submit_to_enqueue=12.0ms" in messages[1]
    assert "enqueue_to_start=8.0ms" in messages[2]
    assert "submit_to_start=20.0ms" in messages[2]


def test_request_debug_logs_slow_keypress_after_refresh() -> None:
    app = _FakeApp()
    tracer = RequestDebugTracer(app)
    logger = MagicMock()

    with (
        patch("tunacode.ui.request_debug.get_logger", return_value=logger),
        patch(
            "tunacode.ui.request_debug.time.monotonic",
            side_effect=[1.0, 1.005, 1.010, 1.100, 1.350],
        ),
    ):
        trace = tracer.submit_received(raw_text="prompt", normalized_text="prompt")
        tracer.request_enqueued_after_refresh(trace)
        tracer.request_started(tracer.pop_next_submission_trace())
        app._loading_indicator_shown = True
        tracer.note_editor_keypress(key_label="a")
        callback = app.scheduled_callbacks[0]
        assert callable(callback)
        callback()

    messages = [call.args[0] for call in logger.lifecycle.call_args_list]
    assert any("Input: keypress_to_refresh seq=1" in message for message in messages)
    assert any("elapsed=250.0ms" in message for message in messages)


@pytest.mark.asyncio
async def test_request_bridge_drain_reports_chunk_metadata() -> None:
    bridge = RequestUiBridge(_FakeApp())

    with patch(
        "tunacode.ui.request_bridge.time.monotonic",
        side_effect=[5.0, 5.050, 5.200],
    ):
        await bridge.streaming_callback("ab")
        await bridge.streaming_callback("cde")
        batch = bridge.drain_streaming()

    assert batch.text == "abcde"
    assert batch.chunk_count == 2
    assert batch.char_count == 5
    assert batch.oldest_age_ms == pytest.approx(200.0)
    assert bridge.drain_streaming().has_data is False
