"""Streaming-output state management for TunaCode TUI."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from textual.widgets import Static


class StreamingHandler:
    def __init__(self, output_widget: Static, throttle_ms: float) -> None:
        self._output = output_widget
        self._throttle_ms = throttle_ms
        self._text: str = ""
        self._last_update: float = 0.0

    async def callback(self, chunk: str) -> None:
        self._text += chunk
        is_first_chunk = not self._output.has_class("active")
        if is_first_chunk:
            self._output.add_class("active")
        now = time.monotonic()
        elapsed_ms = (now - self._last_update) * 1000.0
        if elapsed_ms >= self._throttle_ms or is_first_chunk:
            self._last_update = now
            self._output.update(self._text)

    def reset(self) -> None:
        self._output.update("")
        self._output.remove_class("active")
        self._text = ""
        self._last_update = 0.0
