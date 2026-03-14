"""Streaming-output state management for TunaCode TUI."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from textual.widgets import Static


class StreamingHandler:
    """Owns all streaming state and provides the streaming callback."""

    THROTTLE_MS: float = 100.0
    _MS_PER_SEC: float = 1000.0

    def __init__(self, output_widget: Static) -> None:
        self._output = output_widget
        self._text: str = ""
        self._last_update: float = 0.0

    async def callback(self, chunk: str) -> None:
        """Accumulate streaming chunks and throttle UI updates."""
        self._text += chunk
        is_first_chunk = not self._output.has_class("active")
        if is_first_chunk:
            self._output.add_class("active")
        now = time.monotonic()
        elapsed_ms = (now - self._last_update) * self._MS_PER_SEC
        if elapsed_ms >= self.THROTTLE_MS or is_first_chunk:
            self._last_update = now
            self._output.update(self._text)

    def reset(self) -> None:
        """Clear streaming state and hide the output widget."""
        self._output.update("")
        self._output.remove_class("active")
        self._text = ""
        self._last_update = 0.0
