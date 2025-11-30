"""Textual-based REPL shell - Application entry point.

This replaces the legacy prompt_toolkit/Rich loop with a Textual App.
The app composes widgets from cli/widgets.py and screens from cli/screens.py.
"""

from __future__ import annotations

import asyncio
from typing import Any, cast

from rich.console import RenderableType
from rich.text import Text
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.message import Message
from textual.widgets import Footer, Header, RichLog, Static

from tunacode.cli.screens import ToolConfirmationModal, ToolConfirmationResult
from tunacode.cli.widgets import (
    Editor,
    EditorCompletionsAvailable,
    EditorSubmitRequested,
    ResourceBar,
    ToolStatusBar,
    ToolStatusClear,
    ToolStatusUpdate,
)
from tunacode.constants import THEME_NAME, build_tunacode_theme
from tunacode.core.agents.main import process_request
from tunacode.core.tool_handler import ToolHandler
from tunacode.types import (
    ModelName,
    StateManager,
    ToolConfirmationRequest,
    ToolConfirmationResponse,
)
from tunacode.ui.output import clear_output_sink, register_output_sink


class ShowToolConfirmationModal(Message):
    """Request to show a tool confirmation modal."""

    def __init__(self, *, request: ToolConfirmationRequest) -> None:
        super().__init__()
        self.request = request


class TextualReplApp(App[None]):
    """Minimal Textual shell that will host orchestrator wiring and tool UI."""

    TITLE = "TunaCode"
    CSS_PATH = "textual_repl.tcss"

    BINDINGS = [
        Binding("ctrl+p", "toggle_pause", "Pause/Resume Stream", priority=True),
    ]

    def __init__(self, *, state_manager: StateManager) -> None:
        super().__init__()
        self.state_manager: StateManager = state_manager
        self.rich_log: RichLog = RichLog(wrap=True, markup=False, highlight=False, auto_scroll=True)
        self.editor: Editor = Editor()
        self.resource_bar: ResourceBar = ResourceBar()
        self.request_queue: asyncio.Queue[str] = asyncio.Queue()
        self.pending_confirmation: asyncio.Future[ToolConfirmationResponse] | None = None

        # Streaming state
        self._streaming_paused: bool = False
        self._stream_buffer: list[str] = []
        self.current_stream_text: str = ""
        self.streaming_output: Static = Static(self._render_stream_text(""), id="streaming-output")
        self.tool_status: ToolStatusBar = ToolStatusBar()

    def compose(self) -> ComposeResult:
        yield Header()
        yield self.resource_bar
        body = Vertical(
            self.rich_log, self.tool_status, self.streaming_output, self.editor, id="body"
        )
        yield body
        yield Footer()

    def on_mount(self) -> None:
        # Register custom TunaCode theme using UI_COLORS palette
        tunacode_theme = build_tunacode_theme()
        self.register_theme(tunacode_theme)
        self.theme = THEME_NAME

        self._install_output_sink()
        self.set_focus(self.editor)
        self.run_worker(self._request_worker, exclusive=False)
        self._update_resource_bar()

    async def _request_worker(self) -> None:
        """Process requests from the queue."""
        while True:
            request = await self.request_queue.get()
            try:
                await self._process_request(request)
            except Exception as e:
                error_message = Text(f"Error: {e}", style="red")
                self.rich_log.write(error_message)
            finally:
                self.request_queue.task_done()

    async def _process_request(self, message: str) -> None:
        """Delegate request to the real orchestrator."""
        self.current_stream_text = ""
        self._update_streaming_output()

        try:
            model_name = self.state_manager.session.current_model or "openai/gpt-4o"

            await process_request(
                message=message,
                model=ModelName(model_name),
                state_manager=self.state_manager,
                tool_callback=build_textual_tool_callback(self, self.state_manager),
                streaming_callback=self.streaming_callback,
                tool_status_callback=build_tool_status_callback(self),
            )
        except Exception as e:
            # Ensure errors surface visibly
            processing_error = Text(f"Processing Error: {e}", style="bold red")
            self.rich_log.write(processing_error)
            raise  # Re-raise to be caught by worker loop logging
        finally:
            # Commit the streamed response to the persistent log
            if self.current_stream_text:
                self.rich_log.write(self.current_stream_text)

            # Reset the streaming display
            self.current_stream_text = ""
            self._update_streaming_output()

            # Update resource bar with latest stats
            self._update_resource_bar()

    def on_editor_completions_available(self, message: EditorCompletionsAvailable) -> None:
        # Temporary surfacing until a popover is implemented.
        self.rich_log.write(f"Suggestions: {', '.join(message.candidates)}")

    async def on_editor_submit_requested(self, message: EditorSubmitRequested) -> None:
        await self.request_queue.put(message.text)
        self.rich_log.write(f"> {message.text}")

    async def request_tool_confirmation(
        self, request: ToolConfirmationRequest
    ) -> ToolConfirmationResponse:
        """Ask user to confirm a tool call via modal; non-blocking to UI."""
        if self.pending_confirmation is not None and not self.pending_confirmation.done():
            raise RuntimeError("Previous confirmation still pending")

        self.pending_confirmation = asyncio.Future()
        self.post_message(ShowToolConfirmationModal(request=request))
        return await self.pending_confirmation

    def on_show_tool_confirmation_modal(self, message: ShowToolConfirmationModal) -> None:
        self.push_screen(ToolConfirmationModal(message.request))

    def on_tool_confirmation_result(self, message: ToolConfirmationResult) -> None:
        if self.pending_confirmation is None or self.pending_confirmation.done():
            return
        self.pending_confirmation.set_result(message.response)
        self.pending_confirmation = None

    def on_tool_status_update(self, message: ToolStatusUpdate) -> None:
        """Handle tool status update message."""
        self.tool_status.set_status(message.status)

    def on_tool_status_clear(self, message: ToolStatusClear) -> None:
        """Handle tool status clear message."""
        self.tool_status.clear()

    async def streaming_callback(self, chunk: str) -> None:
        """Receive streaming chunks from the orchestrator."""
        if self._streaming_paused:
            self._stream_buffer.append(chunk)
        else:
            self.current_stream_text += chunk
            self._update_streaming_output()
            # Optional: Scroll to keep streaming output in view if needed
            # self.rich_log.scroll_end() # Not needed as this is outside log

    def action_toggle_pause(self) -> None:
        """Toggle the streaming pause state."""
        if self._streaming_paused:
            self.resume_streaming()
        else:
            self.pause_streaming()

    def pause_streaming(self) -> None:
        self._streaming_paused = True
        # We don't write to RichLog here to avoid polluting history with meta-messages
        # But visual feedback is good. Maybe update status bar?
        # For now, appending to stream text might be confusing if it's not part of response.
        # Let's just rely on the UI state or a separate notification if needed.
        # The original plan asked for visual indicator.
        self.notify("Streaming paused...")

    def resume_streaming(self) -> None:
        self._streaming_paused = False
        self.notify("Streaming resumed...")

        # Flush buffer
        if self._stream_buffer:
            buffered_text = "".join(self._stream_buffer)
            self.current_stream_text += buffered_text
            self._update_streaming_output()
            self._stream_buffer.clear()

    def _update_resource_bar(self) -> None:
        """Refresh the resource bar with current session stats."""
        session = self.state_manager.session
        usage = session.session_total_usage
        last_usage = session.last_call_usage

        self.resource_bar.update_stats(
            model=session.current_model,
            tokens=session.total_tokens,
            max_tokens=session.max_tokens or 200000,
            cost=last_usage.get("cost", 0.0),
            session_cost=usage.get("cost", 0.0),
        )

    def _render_stream_text(self, content: str) -> Text:
        return Text(content, overflow="fold", no_wrap=False)

    def _update_streaming_output(self) -> None:
        stream_renderable = self._render_stream_text(self.current_stream_text)
        self.streaming_output.update(stream_renderable)

    def _install_output_sink(self) -> None:
        """Route legacy console output into the Textual RichLog."""

        def _log_to_rich_log(renderable: object, options: dict[str, Any]) -> None:
            content = self._coerce_renderable_for_log(renderable, options)
            log_kwargs = self._extract_log_kwargs(options)

            self.rich_log.write(content, **log_kwargs)

        register_output_sink(_log_to_rich_log)

    def _coerce_renderable_for_log(
        self, renderable: object, options: dict[str, Any]
    ) -> RenderableType:
        """Translate console renderables to a RichLog-friendly form."""
        style = options.get("style")
        markup_enabled = bool(options.get("markup", True))

        if isinstance(renderable, Text):
            text_renderable = renderable.copy()
            if style:
                text_renderable.stylize(style)
            return text_renderable

        if isinstance(renderable, str):
            text_renderable = (
                Text.from_markup(renderable) if markup_enabled else Text(renderable)
            )
            if style:
                text_renderable.stylize(style)
            return text_renderable

        return cast(RenderableType, renderable)

    def _extract_log_kwargs(self, options: dict[str, Any]) -> dict[str, Any]:
        """Filter kwargs supported by RichLog.write to avoid TypeErrors."""
        allowed_keys = ("width", "expand", "shrink", "scroll_end", "animate")
        return {key: options[key] for key in allowed_keys if key in options}


async def run_textual_repl(state_manager: StateManager) -> None:
    """Launch the Textual REPL application."""
    app = TextualReplApp(state_manager=state_manager)
    try:
        await app.run_async()
    finally:
        clear_output_sink()


def build_textual_tool_callback(app: TextualReplApp, state_manager: StateManager):
    """Create a tool callback using the Textual confirmation flow."""
    async def _callback(part: Any, _node: Any = None) -> None:
        tool_handler = state_manager.tool_handler or ToolHandler(state_manager)
        state_manager.set_tool_handler(tool_handler)

        if not tool_handler.should_confirm(part.tool_name):
            return

        from tunacode.cli.repl_components.command_parser import parse_args
        from tunacode.exceptions import UserAbortError

        args = parse_args(part.args)
        request = tool_handler.create_confirmation_request(part.tool_name, args)
        response = await app.request_tool_confirmation(request)
        if not tool_handler.process_confirmation(response, part.tool_name):
            raise UserAbortError("User aborted tool execution")

    return _callback


def build_tool_status_callback(app: TextualReplApp):
    """Create a callback to update the tool status bar via Textual messages.

    This follows the same pattern as streaming_callback - the callback
    posts a message to the app which handles it on the main thread.
    """

    def _callback(status: str) -> None:
        if status:
            app.post_message(ToolStatusUpdate(status=status))
        else:
            app.post_message(ToolStatusClear())

    return _callback
