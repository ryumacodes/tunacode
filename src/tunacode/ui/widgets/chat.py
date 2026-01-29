"""Chat container widget with insertion tracking for tool panels.

This widget provides a scrollable chat history with the ability to insert
widgets at tracked positions.
"""

from __future__ import annotations

from rich.console import RenderableType
from textual.containers import VerticalScroll
from textual.geometry import Region, Size
from textual.widget import Widget
from textual.widgets import Static


class ChatContainer(VerticalScroll):
    """Scrollable chat container with insertion point tracking.

    This container manages a chat history where widgets can be inserted
    at tracked positions.

    Attributes:
        _insertion_anchor: Widget before which to insert late-arriving content.
        _auto_scroll: Whether to auto-scroll on content changes.
    """

    DEFAULT_CSS = """
    ChatContainer {
        height: 1fr;
        scrollbar-gutter: stable;
    }
    """

    def __init__(
        self,
        *,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        auto_scroll: bool = True,
    ) -> None:
        super().__init__(name=name, id=id, classes=classes)
        self._insertion_anchor: Widget | None = None
        self._auto_scroll = auto_scroll

    def clear_insertion_anchor(self) -> None:
        """Clear any stored insertion anchor."""
        self._insertion_anchor = None

    def set_insertion_anchor(self, anchor: Widget) -> None:
        """Set the widget used as an insertion anchor."""
        self._insertion_anchor = anchor

    def write(
        self,
        renderable: RenderableType,
        *,
        expand: bool = False,
    ) -> Widget:
        """Append a renderable to the chat container.

        This is the primary API for adding content, compatible with RichLog.write().

        Args:
            renderable: Rich renderable to display.
            expand: If True, widget expands to fill available width.

        Returns:
            The created Static widget.
        """
        widget = Static(renderable)
        widget.add_class("chat-message")
        if expand:
            widget.add_class("expand")

        self.mount(widget)

        if self._auto_scroll:
            self.scroll_end(animate=False)

        return widget

    def clear(self) -> None:
        """Clear all content from the container."""
        self._insertion_anchor = None
        for child in list(self.children):
            child.remove()

    @property
    def content_region(self) -> Region:
        """Return the content region for width calculations."""
        return self.scrollable_content_region

    @property
    def size(self) -> Size:
        """Return the widget size."""
        return super().size
