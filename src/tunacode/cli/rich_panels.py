"""Rich Panel Renderer for Textual TUI.

Provides Rich renderables for tools, errors, and search results that integrate
seamlessly with Textual's RichLog widget. Follows NeXTSTEP design principles:
- Consistency: Same data types render identically
- Visual Feedback: State changes immediately visible
- Information Hierarchy: Clear zoning within panels
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

from rich.console import Group, RenderableType
from rich.panel import Panel
from rich.style import Style
from rich.table import Table
from rich.text import Text

from tunacode.constants import UI_COLORS


class PanelType(str, Enum):
    """Panel type enumeration for consistent styling."""

    TOOL = "tool"
    ERROR = "error"
    SEARCH = "search"
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"


# Panel styling mapped to UI_COLORS for consistency
PANEL_STYLES: dict[PanelType, dict[str, str]] = {
    PanelType.TOOL: {
        "border": UI_COLORS["primary"],
        "title": UI_COLORS["primary"],
        "subtitle": UI_COLORS["muted"],
    },
    PanelType.ERROR: {
        "border": UI_COLORS["error"],
        "title": UI_COLORS["error"],
        "subtitle": UI_COLORS["muted"],
    },
    PanelType.SEARCH: {
        "border": UI_COLORS["accent"],
        "title": UI_COLORS["accent"],
        "subtitle": UI_COLORS["muted"],
    },
    PanelType.INFO: {
        "border": UI_COLORS["muted"],
        "title": UI_COLORS["text"],
        "subtitle": UI_COLORS["muted"],
    },
    PanelType.SUCCESS: {
        "border": UI_COLORS["success"],
        "title": UI_COLORS["success"],
        "subtitle": UI_COLORS["muted"],
    },
    PanelType.WARNING: {
        "border": UI_COLORS["warning"],
        "title": UI_COLORS["warning"],
        "subtitle": UI_COLORS["muted"],
    },
}


@dataclass
class ToolDisplayData:
    """Data structure for tool execution display.

    Maps from BaseTool and SessionState tool_calls.
    """

    tool_name: str
    status: str  # "running", "completed", "failed"
    arguments: dict[str, Any]
    result: str | None = None
    duration_ms: float | None = None
    timestamp: datetime | None = None


@dataclass
class ErrorDisplayData:
    """Data structure for error display.

    Maps from TunaCodeError exception hierarchy.
    """

    error_type: str
    message: str
    suggested_fix: str | None = None
    recovery_commands: list[str] | None = None
    context: dict[str, Any] | None = None
    severity: str = "error"  # "error", "warning", "info"


@dataclass
class SearchResultData:
    """Data structure for search result display."""

    query: str
    results: list[dict[str, Any]]
    total_count: int
    current_page: int = 1
    page_size: int = 10
    search_time_ms: float | None = None


class RichPanelRenderer:
    """Renders Rich panels for tools, errors, and search results.

    NeXTSTEP Principle: Objects that look the same should act the same.
    All panels share consistent structure while varying content by type.
    """

    @staticmethod
    def render_tool(data: ToolDisplayData) -> RenderableType:
        """Render a tool execution panel.

        NeXTSTEP: Visual feedback - state shown through highlighting.
        Running tools have accent border, completed have success, failed have error.
        """
        status_map = {
            "running": (PanelType.TOOL, "..."),
            "completed": (PanelType.SUCCESS, "done"),
            "failed": (PanelType.ERROR, "fail"),
        }
        panel_type, status_suffix = status_map.get(
            data.status, (PanelType.INFO, data.status)
        )
        styles = PANEL_STYLES[panel_type]

        # Build content with argument display
        content_parts: list[RenderableType] = []

        # Arguments table (compact)
        if data.arguments:
            args_table = Table.grid(padding=(0, 1))
            args_table.add_column(style="dim")
            args_table.add_column()
            for key, value in data.arguments.items():
                display_value = _truncate_value(value, max_length=60)
                args_table.add_row(f"{key}:", display_value)
            content_parts.append(args_table)

        # Result (if completed)
        if data.result:
            result_text = Text()
            result_text.append("\n")
            result_text.append(_truncate_value(data.result, max_length=200))
            content_parts.append(result_text)

        # Duration (if available)
        if data.duration_ms is not None:
            duration_text = Text(f"\n{data.duration_ms:.0f}ms", style="dim")
            content_parts.append(duration_text)

        content = Group(*content_parts) if content_parts else Text("...")

        # Build subtitle with timestamp
        subtitle = None
        if data.timestamp:
            time_str = data.timestamp.strftime("%H:%M:%S")
            subtitle = f"[{styles['subtitle']}]{time_str}[/]"

        return Panel(
            content,
            title=f"[{styles['title']}]{data.tool_name}[/] [{status_suffix}]",
            subtitle=subtitle,
            border_style=Style(color=styles["border"]),
            padding=(0, 1),
            expand=False,
        )

    @staticmethod
    def render_error(data: ErrorDisplayData) -> RenderableType:
        """Render an error panel with recovery options.

        NeXTSTEP: User control - provide actionable recovery paths.
        """
        severity_map = {
            "error": PanelType.ERROR,
            "warning": PanelType.WARNING,
            "info": PanelType.INFO,
        }
        panel_type = severity_map.get(data.severity, PanelType.ERROR)
        styles = PANEL_STYLES[panel_type]

        content_parts: list[RenderableType] = []

        # Error message
        message_text = Text(data.message, style=styles["title"])
        content_parts.append(message_text)

        # Suggested fix (actionable guidance)
        if data.suggested_fix:
            fix_text = Text()
            fix_text.append("\n\nFix: ", style="bold")
            fix_text.append(data.suggested_fix, style=UI_COLORS["success"])
            content_parts.append(fix_text)

        # Recovery commands (clickable actions)
        if data.recovery_commands:
            commands_text = Text("\n\nRecovery:\n", style="bold")
            for cmd in data.recovery_commands:
                commands_text.append(f"  {cmd}\n", style=UI_COLORS["primary"])
            content_parts.append(commands_text)

        # Context details (collapsed by default, expanded)
        if data.context:
            ctx_table = Table.grid(padding=(0, 1))
            ctx_table.add_column(style="dim")
            ctx_table.add_column()
            for key, value in data.context.items():
                ctx_table.add_row(f"{key}:", str(value))
            content_parts.append(Text("\n"))
            content_parts.append(ctx_table)

        content = Group(*content_parts)

        return Panel(
            content,
            title=f"[{styles['title']}]{data.error_type}[/]",
            border_style=Style(color=styles["border"]),
            padding=(0, 1),
            expand=True,
        )

    @staticmethod
    def render_search_results(data: SearchResultData) -> RenderableType:
        """Render paginated search results.

        NeXTSTEP: Information hierarchy - results ordered by relevance.
        """
        styles = PANEL_STYLES[PanelType.SEARCH]
        content_parts: list[RenderableType] = []

        # Query echo
        query_text = Text()
        query_text.append("Query: ", style="dim")
        query_text.append(data.query, style="bold")
        content_parts.append(query_text)

        # Results count and pagination
        start_idx = (data.current_page - 1) * data.page_size + 1
        end_idx = min(start_idx + len(data.results) - 1, data.total_count)
        total_pages = (data.total_count + data.page_size - 1) // data.page_size

        stats_text = Text()
        stats_text.append(f"\nShowing {start_idx}-{end_idx} of {data.total_count}", style="dim")
        if total_pages > 1:
            stats_text.append(f" (page {data.current_page}/{total_pages})", style="dim")
        content_parts.append(stats_text)

        # Search time
        if data.search_time_ms is not None:
            time_text = Text(f" in {data.search_time_ms:.0f}ms", style="dim")
            content_parts.append(time_text)

        content_parts.append(Text("\n"))

        # Results list
        results_table = Table.grid(padding=(0, 1))
        results_table.add_column(width=3, style="dim")  # Index
        results_table.add_column()  # Content

        for i, result in enumerate(data.results, start=start_idx):
            # Extract display fields from result
            title = result.get("title", result.get("file", result.get("name", "...")))
            snippet = result.get("snippet", result.get("content", ""))
            relevance = result.get("relevance", result.get("score"))

            result_text = Text()
            result_text.append(str(title), style="bold")
            if relevance is not None:
                result_text.append(f" ({relevance:.0%})", style="dim")
            if snippet:
                result_text.append(f"\n  {_truncate_value(snippet, 80)}", style="dim")

            results_table.add_row(f"{i}.", result_text)

        content_parts.append(results_table)

        content = Group(*content_parts)

        subtitle = None
        if total_pages > 1:
            subtitle = f"[{styles['subtitle']}]Use arrows to navigate[/]"

        return Panel(
            content,
            title=f"[{styles['title']}]Search Results[/]",
            subtitle=subtitle,
            border_style=Style(color=styles["border"]),
            padding=(0, 1),
            expand=True,
        )

    @staticmethod
    def render_info(title: str, content: str | RenderableType) -> RenderableType:
        """Render a generic info panel."""
        styles = PANEL_STYLES[PanelType.INFO]

        if isinstance(content, str):
            content = Text(content)

        return Panel(
            content,
            title=f"[{styles['title']}]{title}[/]",
            border_style=Style(color=styles["border"]),
            padding=(0, 1),
            expand=False,
        )

    @staticmethod
    def render_success(title: str, message: str) -> RenderableType:
        """Render a success notification panel."""
        styles = PANEL_STYLES[PanelType.SUCCESS]

        return Panel(
            Text(message, style=styles["title"]),
            title=f"[{styles['title']}]{title}[/]",
            border_style=Style(color=styles["border"]),
            padding=(0, 1),
            expand=False,
        )

    @staticmethod
    def render_warning(title: str, message: str) -> RenderableType:
        """Render a warning notification panel."""
        styles = PANEL_STYLES[PanelType.WARNING]

        return Panel(
            Text(message, style=styles["title"]),
            title=f"[{styles['title']}]{title}[/]",
            border_style=Style(color=styles["border"]),
            padding=(0, 1),
            expand=False,
        )


def _truncate_value(value: Any, max_length: int = 50) -> str:
    """Truncate a value for display, preserving meaning."""
    str_value = str(value)
    if len(str_value) <= max_length:
        return str_value
    return str_value[: max_length - 3] + "..."


# Convenience functions for quick panel creation
def tool_panel(
    name: str,
    status: str,
    args: dict[str, Any] | None = None,
    result: str | None = None,
    duration_ms: float | None = None,
) -> RenderableType:
    """Create a tool execution panel."""
    data = ToolDisplayData(
        tool_name=name,
        status=status,
        arguments=args or {},
        result=result,
        duration_ms=duration_ms,
        timestamp=datetime.now(),
    )
    return RichPanelRenderer.render_tool(data)


def error_panel(
    error_type: str,
    message: str,
    suggested_fix: str | None = None,
    recovery_commands: list[str] | None = None,
    severity: str = "error",
) -> RenderableType:
    """Create an error panel."""
    data = ErrorDisplayData(
        error_type=error_type,
        message=message,
        suggested_fix=suggested_fix,
        recovery_commands=recovery_commands,
        severity=severity,
    )
    return RichPanelRenderer.render_error(data)


def search_panel(
    query: str,
    results: list[dict[str, Any]],
    total_count: int | None = None,
    page: int = 1,
    search_time_ms: float | None = None,
) -> RenderableType:
    """Create a search results panel."""
    data = SearchResultData(
        query=query,
        results=results,
        total_count=total_count or len(results),
        current_page=page,
        search_time_ms=search_time_ms,
    )
    return RichPanelRenderer.render_search_results(data)
