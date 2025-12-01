"""Search Result Display for Textual TUI.

Provides paginated search results with relevance scoring and context highlighting.
Follows NeXTSTEP principles:
- Information Hierarchy: Results ordered by relevance
- User Control: Pagination for navigation
- Visual Feedback: Highlighted matches
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from rich.console import RenderableType
from rich.panel import Panel
from rich.style import Style
from rich.text import Text

from tunacode.cli.rich_panels import RichPanelRenderer, SearchResultData
from tunacode.constants import UI_COLORS


@dataclass
class FileSearchResult:
    """Search result for file/grep operations."""

    file_path: str
    line_number: int | None = None
    content: str = ""
    match_start: int | None = None
    match_end: int | None = None
    relevance: float | None = None


@dataclass
class CodeSearchResult:
    """Search result for code/symbol search."""

    file_path: str
    symbol_name: str
    symbol_type: str  # "function", "class", "variable", etc.
    line_number: int
    context: str = ""
    relevance: float | None = None


class SearchDisplayRenderer:
    """Renders search results with highlighting and pagination.

    NeXTSTEP: Maximum viewport for results, clear relevance ordering.
    """

    @staticmethod
    def render_file_results(
        query: str,
        results: list[FileSearchResult],
        page: int = 1,
        page_size: int = 10,
        search_time_ms: float | None = None,
    ) -> RenderableType:
        """Render file search results (grep-style)."""
        # Convert to generic format
        generic_results = []
        for r in results:
            result_dict: dict[str, Any] = {
                "file": r.file_path,
                "content": r.content,
            }
            if r.line_number is not None:
                result_dict["title"] = f"{r.file_path}:{r.line_number}"
            else:
                result_dict["title"] = r.file_path

            if r.relevance is not None:
                result_dict["relevance"] = r.relevance

            # Build snippet with highlighting
            if r.match_start is not None and r.match_end is not None:
                before = r.content[: r.match_start]
                match = r.content[r.match_start : r.match_end]
                after = r.content[r.match_end :]
                result_dict["snippet"] = f"{before}[{match}]{after}"
            else:
                result_dict["snippet"] = r.content

            generic_results.append(result_dict)

        # Paginate
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        page_results = generic_results[start_idx:end_idx]

        data = SearchResultData(
            query=query,
            results=page_results,
            total_count=len(results),
            current_page=page,
            page_size=page_size,
            search_time_ms=search_time_ms,
        )

        return RichPanelRenderer.render_search_results(data)

    @staticmethod
    def render_code_results(
        query: str,
        results: list[CodeSearchResult],
        page: int = 1,
        page_size: int = 10,
        search_time_ms: float | None = None,
    ) -> RenderableType:
        """Render code/symbol search results."""
        # Convert to generic format with symbol-specific display
        generic_results = []
        for r in results:
            # Symbol type icons
            type_icons = {
                "function": "fn",
                "class": "cls",
                "variable": "var",
                "method": "mtd",
                "constant": "const",
            }
            type_label = type_icons.get(r.symbol_type, r.symbol_type[:3])

            result_dict: dict[str, Any] = {
                "title": f"[{type_label}] {r.symbol_name}",
                "file": f"{r.file_path}:{r.line_number}",
                "snippet": r.context,
            }
            if r.relevance is not None:
                result_dict["relevance"] = r.relevance

            generic_results.append(result_dict)

        # Paginate
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        page_results = generic_results[start_idx:end_idx]

        data = SearchResultData(
            query=query,
            results=page_results,
            total_count=len(results),
            current_page=page,
            page_size=page_size,
            search_time_ms=search_time_ms,
        )

        return RichPanelRenderer.render_search_results(data)

    @staticmethod
    def render_inline_results(
        results: list[dict[str, Any]],
        max_display: int = 5,
    ) -> RenderableType:
        """Render compact inline results for quick display.

        Used when results should appear inline without full panel.
        NeXTSTEP: Don't interrupt user flow for non-critical info.
        """
        if not results:
            return Text("No results found", style="dim")

        content = Text()
        display_results = results[:max_display]

        for i, result in enumerate(display_results):
            title = result.get("title", result.get("file", "..."))
            content.append(f"{i + 1}. ", style="dim")
            content.append(str(title), style=UI_COLORS["primary"])
            content.append("\n")

        if len(results) > max_display:
            remaining = len(results) - max_display
            content.append(f"   ...and {remaining} more", style="dim")

        return content

    @staticmethod
    def render_empty_results(query: str) -> RenderableType:
        """Render empty results state with suggestions."""
        content = Text()
        content.append("No results found for: ", style="dim")
        content.append(query, style="bold")
        content.append("\n\nSuggestions:\n", style="dim")
        content.append("  - Try a different search term\n", style="dim")
        content.append("  - Use broader patterns\n", style="dim")
        content.append("  - Check file paths and extensions", style="dim")

        return Panel(
            content,
            title=f"[{UI_COLORS['warning']}]No Results[/]",
            border_style=Style(color=UI_COLORS["warning"]),
            padding=(0, 1),
            expand=False,
        )


# Convenience functions
def file_search_panel(
    query: str,
    results: list[FileSearchResult],
    page: int = 1,
    search_time_ms: float | None = None,
) -> RenderableType:
    """Create a file search results panel."""
    if not results:
        return SearchDisplayRenderer.render_empty_results(query)
    return SearchDisplayRenderer.render_file_results(
        query, results, page, search_time_ms=search_time_ms
    )


def code_search_panel(
    query: str,
    results: list[CodeSearchResult],
    page: int = 1,
    search_time_ms: float | None = None,
) -> RenderableType:
    """Create a code search results panel."""
    if not results:
        return SearchDisplayRenderer.render_empty_results(query)
    return SearchDisplayRenderer.render_code_results(
        query, results, page, search_time_ms=search_time_ms
    )


def quick_results(results: list[dict[str, Any]], max_display: int = 5) -> RenderableType:
    """Create inline results for quick display."""
    return SearchDisplayRenderer.render_inline_results(results, max_display)
