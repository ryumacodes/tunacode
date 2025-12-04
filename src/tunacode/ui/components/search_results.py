"""Native Textual widget for search results display."""

from __future__ import annotations

from typing import Any

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import DataTable, Static


class SearchResultsTable(Static):
    """Interactive DataTable for search results.

    Supports row selection and pagination.
    """

    DEFAULT_CSS = """
    SearchResultsTable {
        border: solid $accent;
        background: $surface;
        padding: 0 1;
        margin: 0 0 1 0;
        height: auto;
        max-height: 20;
    }

    SearchResultsTable .search-header {
        margin-bottom: 1;
    }

    SearchResultsTable .search-query {
        text-style: bold;
    }

    SearchResultsTable .search-stats {
        color: $text-muted;
    }

    SearchResultsTable DataTable {
        height: auto;
        max-height: 15;
    }
    """

    def __init__(
        self,
        query: str,
        results: list[dict[str, Any]],
        total_count: int | None = None,
        search_time_ms: float | None = None,
    ) -> None:
        super().__init__()
        self.query = query
        self.results = results
        self.total_count = total_count or len(results)
        self.search_time_ms = search_time_ms

        self.add_class("search-panel")

    def compose(self) -> ComposeResult:
        with Vertical(classes="search-header"):
            yield Static(f"Query: {self.query}", classes="search-query")

            stats = f"Found {self.total_count} results"
            if self.search_time_ms is not None:
                stats += f" in {self.search_time_ms:.0f}ms"
            yield Static(stats, classes="search-stats")

        table = DataTable()
        table.add_columns("#", "File", "Match")
        table.cursor_type = "row"

        for i, result in enumerate(self.results, start=1):
            title = result.get("title", result.get("file", "..."))
            snippet = result.get("snippet", result.get("content", ""))
            snippet = _truncate(snippet, 50)
            table.add_row(str(i), str(title), snippet)

        yield table


def _truncate(value: Any, max_length: int = 50) -> str:
    s = str(value)
    if len(s) <= max_length:
        return s
    return s[: max_length - 3] + "..."
