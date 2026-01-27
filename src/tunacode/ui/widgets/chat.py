"""Chat container widget with insertion tracking for tool panels.

This widget provides a scrollable chat history with the ability to insert
widgets at tracked positions, solving the race condition where tool panels
appear at the wrong position after stream cancellation or end.
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
    at tracked positions. It solves the race condition where tool panels
    arrive after the stream ends and need to be inserted before the
    finalized agent response.

    Attributes:
        _current_stream: The currently streaming Static widget, if any.
        _insertion_anchor: Widget before which to insert after stream ends.
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
        self._current_stream: Static | None = None
        self._insertion_anchor: Widget | None = None
        self._auto_scroll = auto_scroll

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

    def start_stream(self, initial_content: RenderableType | None = None) -> Widget:
        """Begin a streaming response.

        Creates a new streaming widget and clears any stale insertion anchor.

        Args:
            initial_content: Optional initial content for the streaming widget.

        Returns:
            The streaming widget.
        """
        # Clear stale anchor from previous request
        self._insertion_anchor = None

        content = initial_content if initial_content is not None else ""
        self._current_stream = Static(content)
        self._current_stream.add_class("chat-message", "streaming")

        self.mount(self._current_stream)
        self.add_class("streaming")

        if self._auto_scroll:
            self.scroll_end(animate=False)

        return self._current_stream

    def update_stream(self, renderable: RenderableType) -> None:
        """Update the current streaming widget content.

        Args:
            renderable: New content for the streaming widget.
        """
        if self._current_stream is not None:
            self._current_stream.update(renderable)

            if self._auto_scroll:
                self.scroll_end(animate=False)

    def end_stream(self) -> None:
        """End streaming and set insertion anchor.

        Captures the finalized stream widget as the insertion anchor
        so late-arriving tool panels insert before it.
        """
        if self._current_stream is not None:
            # Capture the finalized widget as insertion anchor
            self._insertion_anchor = self._current_stream
            self._current_stream.remove_class("streaming")
            self._current_stream = None

        self.remove_class("streaming")

    def cancel_stream(self) -> None:
        """Cancel streaming and preserve insertion context.

        On cancel, we want late-arriving tool panels to appear at the
        position where streaming was occurring. We track the position
        by finding the widget that was before the stream widget.
        """
        if self._current_stream is not None:
            children = list(self.children)
            try:
                idx = children.index(self._current_stream)
                # Set anchor to widget before the stream position
                # so insert_before_stream inserts AFTER it
                if idx > 0:
                    self._insertion_anchor = children[idx - 1]
                else:
                    self._insertion_anchor = None
            except ValueError:
                self._insertion_anchor = None

            self._current_stream.remove()
            self._current_stream = None

        self.remove_class("streaming")

    def insert_before_stream(self, renderable: RenderableType) -> Widget:
        """Insert a widget before the streaming position.

        This is the key method for solving the tool panel race condition.
        Tool panels should appear inline with the streaming context, not
        appended to the end.

        Insertion behavior:
        - If stream is active: insert before the streaming widget
        - If stream ended: insert before the finalized message (anchor)
        - If cancelled: insert after the preserved anchor position
        - If no context: append to end

        Args:
            renderable: Rich renderable to insert.

        Returns:
            The created Static widget.
        """
        widget = Static(renderable)
        widget.add_class("chat-message", "tool-panel")

        if self._current_stream is not None:
            # Active stream: insert before streaming widget
            self.mount(widget, before=self._current_stream)
        elif self._insertion_anchor is not None:
            # Stream ended or cancelled: insert relative to anchor
            # For end_stream: anchor IS the finalized message, insert before it
            # For cancel_stream: anchor is widget BEFORE stream, insert after it
            if self._insertion_anchor in self.children:
                # Check if anchor was set by end_stream (has streaming class removed)
                # or cancel_stream (was the widget before the stream)
                self.mount(widget, before=self._insertion_anchor)
            else:
                # Anchor widget was removed, fall back to append
                self.mount(widget)
        else:
            # No context: append
            self.mount(widget)

        if self._auto_scroll:
            self.scroll_end(animate=False)

        return widget

    def clear(self) -> None:
        """Clear all content from the container."""
        self._current_stream = None
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
