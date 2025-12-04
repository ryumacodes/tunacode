"""Search Result Display for Textual TUI."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, TypeVar

from rich.console import RenderableType
from rich.panel import Panel
from rich.style import Style
from rich.text import Text

from tunacode.ui.renderers.panels import RichPanelRenderer, SearchResultData
from tunacode.constants import UI_COLORS

T = TypeVar("T")


def _paginate(items: list[T], page: int, page_size: int) -> tuple[list[T], int, int]:
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    total_pages = (len(items) + page_size - 1) // page_size if items else 1
    return items[start_idx:end_idx], start_idx, total_pages


@dataclass
class FileSearchResult:
    file_path: str
    line_number: int | None = None
    content: str = ""
    match_start: int | None = None
    match_end: int | None = None
    relevance: float | None = None


@dataclass
class CodeSearchResult:
    file_path: str
    symbol_name: str
    symbol_type: str
    line_number: int
    context: str = ""
    relevance: float | None = None


class SearchDisplayRenderer:
    @staticmethod
    def render_file_results(
        query: str,
        results: list[FileSearchResult],
        page: int = 1,
        page_size: int = 10,
        search_time_ms: float | None = None,
    ) -> RenderableType:
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

            if r.match_start is not None and r.match_end is not None:
                before = r.content[: r.match_start]
                match = r.content[r.match_start : r.match_end]
                after = r.content[r.match_end :]
                result_dict["snippet"] = f"{before}[{match}]{after}"
            else:
                result_dict["snippet"] = r.content

            generic_results.append(result_dict)

        page_results, _, _ = _paginate(generic_results, page, page_size)

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
        generic_results = []
        for r in results:
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

        page_results, _, _ = _paginate(generic_results, page, page_size)

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

    @staticmethod
    def parse_grep_output(text: str, query: str | None = None) -> SearchResultData | None:
        if not text or "Found" not in text:
            return None

        header_match = re.match(r"Found (\d+) match(?:es)? for pattern: (.+)", text)
        if not header_match:
            return None

        total_count = int(header_match.group(1))
        detected_query = header_match.group(2).strip()
        final_query = query or detected_query

        results: list[dict[str, Any]] = []
        file_pattern = re.compile(r"📁 (.+?):(\d+)")
        match_pattern = re.compile(r"▶\s*(\d+)│\s*(.*?)⟨(.+?)⟩(.*)")

        current_file: str | None = None

        for line in text.split("\n"):
            file_match = file_pattern.search(line)
            if file_match:
                current_file = file_match.group(1)
                continue

            match_line = match_pattern.search(line)
            if match_line and current_file:
                line_num = int(match_line.group(1))
                before = match_line.group(2)
                match_text = match_line.group(3)
                after = match_line.group(4)

                results.append(
                    {
                        "title": f"{current_file}:{line_num}",
                        "file": current_file,
                        "snippet": f"{before}[{match_text}]{after}",
                        "line_number": line_num,
                    }
                )

        if not results:
            return None

        return SearchResultData(
            query=final_query,
            results=results,
            total_count=total_count,
            current_page=1,
            page_size=len(results),
        )

    @staticmethod
    def parse_glob_output(text: str, pattern: str | None = None) -> SearchResultData | None:
        if not text or "Found" not in text:
            return None

        header_match = re.match(r"Found (\d+) files? matching pattern: (.+)", text)
        if not header_match:
            return None

        total_count = int(header_match.group(1))
        detected_pattern = header_match.group(2).strip()
        final_pattern = pattern or detected_pattern

        results: list[dict[str, Any]] = []
        dir_pattern = re.compile(r"📁 (.+)/")
        file_pattern = re.compile(r"^\s+-\s+(.+)$")

        current_dir: str | None = None

        for line in text.split("\n"):
            dir_match = dir_pattern.search(line)
            if dir_match:
                current_dir = dir_match.group(1)
                continue

            file_match = file_pattern.match(line)
            if file_match and current_dir is not None:
                filename = file_match.group(1)
                full_path = f"{current_dir}/{filename}"
                results.append(
                    {
                        "title": full_path,
                        "file": full_path,
                        "snippet": filename,
                    }
                )

        if not results:
            return None

        return SearchResultData(
            query=final_pattern,
            results=results,
            total_count=total_count,
            current_page=1,
            page_size=len(results),
        )


def file_search_panel(
    query: str,
    results: list[FileSearchResult],
    page: int = 1,
    search_time_ms: float | None = None,
) -> RenderableType:
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
    if not results:
        return SearchDisplayRenderer.render_empty_results(query)
    return SearchDisplayRenderer.render_code_results(
        query, results, page, search_time_ms=search_time_ms
    )


def quick_results(results: list[dict[str, Any]], max_display: int = 5) -> RenderableType:
    return SearchDisplayRenderer.render_inline_results(results, max_display)
