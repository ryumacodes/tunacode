"""Resource bar widget for TunaCode REPL."""

from __future__ import annotations

from rich.text import Text
from textual.widgets import Static

from tunacode.core.constants import RESOURCE_BAR_COST_FORMAT, RESOURCE_BAR_SEPARATOR

from tunacode.ui.styles import (
    STYLE_ERROR,
    STYLE_MUTED,
    STYLE_SUCCESS,
    STYLE_WARNING,
)


class ResourceBar(Static):
    """Top bar showing resources: tokens, model, cost, LSP status."""

    def __init__(self) -> None:
        super().__init__("Loading...")
        self._tokens: int = 0
        self._max_tokens: int = 200000
        self._model: str = "---"
        self._cost: float = 0.0
        self._session_cost: float = 0.0
        self._lsp_server: str | None = None
        self._lsp_available: bool = False

    def on_mount(self) -> None:
        self._refresh_display()

    def update_stats(
        self,
        *,
        tokens: int | None = None,
        max_tokens: int | None = None,
        model: str | None = None,
        cost: float | None = None,
        session_cost: float | None = None,
    ) -> None:
        if tokens is not None:
            self._tokens = tokens
        if max_tokens is not None:
            self._max_tokens = max_tokens
        if model is not None:
            self._model = model
        if cost is not None:
            self._cost = cost
        if session_cost is not None:
            self._session_cost = session_cost
        self._refresh_display()

    def update_lsp_status(self, server: str | None, available: bool) -> None:
        """Update LSP server status display.

        Args:
            server: Server binary name (e.g., 'ruff') or None if unsupported
            available: True if server binary exists on PATH
        """
        self._lsp_server = server
        self._lsp_available = available
        self._refresh_display()

    def _calculate_remaining_pct(self) -> float:
        if self._max_tokens == 0:
            return 0.0
        raw_pct = (self._max_tokens - self._tokens) / self._max_tokens * 100
        return max(0.0, min(100.0, raw_pct))

    def _get_circle_color(self, remaining_pct: float) -> str:
        if remaining_pct > 60:
            return STYLE_SUCCESS
        if remaining_pct > 30:
            return STYLE_WARNING
        return STYLE_ERROR

    def _get_circle_char(self, remaining_pct: float) -> str:
        if remaining_pct > 87.5:
            return "●"
        if remaining_pct > 62.5:
            return "◕"
        if remaining_pct > 37.5:
            return "◑"
        if remaining_pct > 12.5:
            return "◔"
        return "○"

    def _refresh_display(self) -> None:
        sep = RESOURCE_BAR_SEPARATOR
        session_cost_str = RESOURCE_BAR_COST_FORMAT.format(cost=self._session_cost)

        remaining_pct = self._calculate_remaining_pct()
        circle_char = self._get_circle_char(remaining_pct)
        circle_color = self._get_circle_color(remaining_pct)

        parts: list[tuple[str, str]] = [
            (circle_char, circle_color),
            (f" {remaining_pct:.0f}%", circle_color),
            (sep, STYLE_MUTED),
            (session_cost_str, STYLE_SUCCESS),
        ]

        if self._lsp_server:
            lsp_indicator = "●" if self._lsp_available else "○"
            lsp_color = STYLE_SUCCESS if self._lsp_available else STYLE_MUTED
            parts.append((sep, STYLE_MUTED))
            parts.append((f"{self._lsp_server} ", STYLE_MUTED))
            parts.append((lsp_indicator, lsp_color))

        content = Text.assemble(*parts)
        self.update(content)
