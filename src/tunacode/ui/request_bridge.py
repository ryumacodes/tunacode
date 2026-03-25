"""Thread-safe request-to-UI callback bridge."""

from __future__ import annotations

import time
from queue import Empty, SimpleQueue
from typing import TYPE_CHECKING

from tunacode.ui.request_debug import BridgeDrainBatch
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
        self._streaming_deltas: SimpleQueue[tuple[str, float]] = SimpleQueue()
        self._thinking_deltas: SimpleQueue[tuple[str, float]] = SimpleQueue()

    async def streaming_callback(self, delta: str) -> None:
        self._streaming_deltas.put((delta, time.monotonic()))

    async def thinking_callback(self, delta: str) -> None:
        self._thinking_deltas.put((delta, time.monotonic()))

    def notice_callback(self, notice: str) -> None:
        self._app.post_message(SystemNoticeDisplay(notice=notice))

    def compaction_status_callback(self, active: bool) -> None:
        self._app.post_message(CompactionStatusChanged(active=active))

    def drain_streaming(self) -> BridgeDrainBatch:
        return self._drain_queue(self._streaming_deltas)

    def drain_thinking(self) -> BridgeDrainBatch:
        return self._drain_queue(self._thinking_deltas)

    def _drain_queue(self, queue: SimpleQueue[tuple[str, float]]) -> BridgeDrainBatch:
        chunks: list[str] = []
        chunk_count = 0
        char_count = 0
        oldest_enqueued_at = 0.0
        while True:
            try:
                chunk, enqueued_at = queue.get_nowait()
            except Empty:
                if chunk_count == 0:
                    return BridgeDrainBatch()
                oldest_age_ms = (time.monotonic() - oldest_enqueued_at) * 1000.0
                return BridgeDrainBatch(
                    text="".join(chunks),
                    chunk_count=chunk_count,
                    char_count=char_count,
                    oldest_age_ms=oldest_age_ms,
                )
            if chunk_count == 0:
                oldest_enqueued_at = enqueued_at
            chunks.append(chunk)
            chunk_count += 1
            char_count += len(chunk)
