"""Thread-safe request-to-UI callback bridge."""

from __future__ import annotations

from queue import Empty, SimpleQueue
from typing import TYPE_CHECKING

from tunacode.ui.widgets import CompactionStatusChanged, SystemNoticeDisplay

if TYPE_CHECKING:
    from tunacode.ui.app import TextualReplApp


class RequestUiBridge:
    """Adapt request-thread callbacks into UI-thread message routing.

    These callbacks must not raise. They only enqueue deltas or post messages,
    and UI mutation happens later when the app flushes queued state.
    """

    def __init__(self, app: TextualReplApp) -> None:
        self._app = app
        self._streaming_deltas: SimpleQueue[str] = SimpleQueue()
        self._thinking_deltas: SimpleQueue[str] = SimpleQueue()

    async def streaming_callback(self, delta: str) -> None:
        self._streaming_deltas.put(delta)

    async def thinking_callback(self, delta: str) -> None:
        self._thinking_deltas.put(delta)

    def notice_callback(self, notice: str) -> None:
        self._app.post_message(SystemNoticeDisplay(notice=notice))

    def compaction_status_callback(self, active: bool) -> None:
        self._app.post_message(CompactionStatusChanged(active=active))

    def drain_streaming(self) -> str:
        return self._drain_queue(self._streaming_deltas)

    def drain_thinking(self) -> str:
        return self._drain_queue(self._thinking_deltas)

    def _drain_queue(self, queue: SimpleQueue[str]) -> str:
        chunks: list[str] = []
        while True:
            try:
                chunks.append(queue.get_nowait())
            except Empty:
                return "".join(chunks)
