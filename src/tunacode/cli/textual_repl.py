"""Textual-based REPL shell - Application entry point.

This replaces the legacy prompt_toolkit/Rich loop with a Textual App.
The app composes widgets from cli/widgets.py and screens from cli/screens.py.
"""

from __future__ import annotations

import asyncio
from typing import Any

from rich.text import Text
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.message import Message
from textual.widgets import RichLog, Static

from tunacode.cli.error_panels import render_exception
from tunacode.cli.rich_panels import tool_panel_smart
from tunacode.cli.screens import ToolConfirmationModal, ToolConfirmationResult
from tunacode.cli.widgets import (
    Editor,
    EditorCompletionsAvailable,
    EditorSubmitRequested,
    ResourceBar,
    StatusBar,
    ToolResultDisplay,
)
from tunacode.constants import (
    RICHLOG_CLASS_PAUSED,
    RICHLOG_CLASS_STREAMING,
    THEME_NAME,
    build_tunacode_theme,
)
from tunacode.core.agents.main import process_request
from tunacode.tools.authorization.handler import ToolHandler
from tunacode.types import (
    ModelName,
    StateManager,
    ToolConfirmationRequest,
    ToolConfirmationResponse,
)


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
        Binding("ctrl+p", "toggle_pause", "Pause/Resume Stream", show=False, priority=True),
    ]

    def __init__(self, *, state_manager: StateManager) -> None:
        super().__init__()
        self.state_manager: StateManager = state_manager
        self.request_queue: asyncio.Queue[str] = asyncio.Queue()
        self.pending_confirmation: asyncio.Future[ToolConfirmationResponse] | None = None

        # Streaming state
        self._streaming_paused: bool = False
        self._stream_buffer: list[str] = []
        self.current_stream_text: str = ""

        # Widgets are created in compose() to ensure app context is active
        self.rich_log: RichLog
        self.editor: Editor
        self.resource_bar: ResourceBar
        self.status_bar: StatusBar

    def compose(self) -> ComposeResult:
        """Compose NeXTSTEP zone-based layout.

        ┌─────────────────────────────────────────────┐
        │ Model │ Tokens │ Cost │ Session             │  ← PERSISTENT STATUS
        ├─────────────────────────────────────────────┤
        │                                             │
        │           Main conversation/code            │  ← MAXIMUM VIEWPORT
        │                                             │
        ├─────────────────────────────────────────────┤
        │ > input here_                               │  ← INPUT BAR
        ├───────────────┬─────────────┬───────────────┤
        │ main ● ~/proj │ bg: index.. │ last: action  │  ← STATUS BAR
        └───────────────┴─────────────┴───────────────┘
        """
        # Create widgets here where app context is active
        self.resource_bar = ResourceBar()
        self.rich_log = RichLog(wrap=True, markup=False, highlight=False, auto_scroll=True)
        self.editor = Editor()
        self.status_bar = StatusBar()

        # Persistent status zone (top)
        yield self.resource_bar

        # Primary viewport (center)
        yield self.rich_log

        # Bottom zone - input bar + status bar
        prompt_label = Static("> ", id="input-prompt")
        input_row = Horizontal(prompt_label, self.editor, id="input-row")
        bottom_zone = Vertical(input_row, self.status_bar, id="bottom-zone")
        yield bottom_zone

    def on_mount(self) -> None:
        # Register custom TunaCode theme using UI_COLORS palette
        tunacode_theme = build_tunacode_theme()
        self.register_theme(tunacode_theme)
        self.theme = THEME_NAME

        self.set_focus(self.editor)
        self.run_worker(self._request_worker, exclusive=False)
        self._update_resource_bar()
        self._show_welcome()

    def _show_welcome(self) -> None:
        """Display welcome message with TunaCode capabilities."""
        welcome = Text()
        welcome.append("🍣 Welcome to TunaCode\n", style="magenta bold")
        welcome.append("AI-powered coding assistant in your terminal.\n\n", style="dim")
        welcome.append("What I can do:\n", style="cyan")
        welcome.append("  • Read, write, and edit files\n", style="")
        welcome.append("  • Run shell commands\n", style="")
        welcome.append("  • Search code with grep/glob\n", style="")
        welcome.append("  • Answer questions about your codebase\n", style="")
        welcome.append("  • Help debug and refactor code\n\n", style="")
        welcome.append("Type a message below to get started.\n", style="dim")
        self.rich_log.write(welcome)

    async def _request_worker(self) -> None:
        """Process requests from the queue."""
        while True:
            request = await self.request_queue.get()
            try:
                await self._process_request(request)
            except Exception as e:
                # Use rich error panels for structured error display
                error_renderable = render_exception(e)
                self.rich_log.write(error_renderable)
            finally:
                self.request_queue.task_done()

    async def _process_request(self, message: str) -> None:
        """Delegate request to the real orchestrator."""
        self.current_stream_text = ""
        # Enter streaming mode - NeXTSTEP visual feedback
        self.rich_log.add_class(RICHLOG_CLASS_STREAMING)

        try:
            model_name = self.state_manager.session.current_model or "openai/gpt-4o"

            await process_request(
                message=message,
                model=ModelName(model_name),
                state_manager=self.state_manager,
                tool_callback=build_textual_tool_callback(self, self.state_manager),
                streaming_callback=self.streaming_callback,
                tool_result_callback=build_tool_result_callback(self),
            )
        except Exception as e:
            # Use rich error panels for structured error display
            error_renderable = render_exception(e)
            self.rich_log.write(error_renderable)
            raise  # Re-raise to be caught by worker loop logging
        finally:
            # Exit streaming mode
            self.rich_log.remove_class(RICHLOG_CLASS_STREAMING)
            self.rich_log.remove_class(RICHLOG_CLASS_PAUSED)

            # Commit the streamed response to the persistent log
            if self.current_stream_text:
                self.rich_log.write(self.current_stream_text)

            # Reset the streaming state
            self.current_stream_text = ""

            # Update resource bar with latest stats
            self._update_resource_bar()

    def on_editor_completions_available(self, message: EditorCompletionsAvailable) -> None:
        # Temporary surfacing until a popover is implemented.
        self.rich_log.write(f"Suggestions: {', '.join(message.candidates)}")

    async def on_editor_submit_requested(self, message: EditorSubmitRequested) -> None:
        await self.request_queue.put(message.text)

        # Format user message with left border and timestamp
        from datetime import datetime

        timestamp = datetime.now().strftime("%I:%M %p").lstrip("0")
        user_block = Text()
        user_block.append(f"│ {message.text}\n", style="cyan")
        user_block.append(f"│ tc {timestamp}", style="dim cyan")
        self.rich_log.write(user_block)

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

    def on_tool_result_display(self, message: ToolResultDisplay) -> None:
        """Handle tool result display - write panel to RichLog.

        Uses tool_panel_smart() to route grep/glob results to SearchPanel.
        """
        panel = tool_panel_smart(
            name=message.tool_name,
            status=message.status,
            args=message.args,
            result=message.result,
            duration_ms=message.duration_ms,
        )
        self.rich_log.write(panel)

    async def streaming_callback(self, chunk: str) -> None:
        """Receive streaming chunks from the orchestrator.

        NeXTSTEP: Content streams directly into unified viewport (RichLog).
        """
        if self._streaming_paused:
            self._stream_buffer.append(chunk)
        else:
            self.current_stream_text += chunk
            # Scroll to keep content visible during streaming
            self.rich_log.scroll_end()

    def action_toggle_pause(self) -> None:
        """Toggle the streaming pause state."""
        if self._streaming_paused:
            self.resume_streaming()
        else:
            self.pause_streaming()

    def pause_streaming(self) -> None:
        """Pause streaming and show visual indicator.

        NeXTSTEP: "Modes must be visually apparent at all times"
        """
        self._streaming_paused = True
        self.rich_log.add_class(RICHLOG_CLASS_PAUSED)
        self.notify("Streaming paused...")

    def resume_streaming(self) -> None:
        """Resume streaming and remove pause indicator."""
        self._streaming_paused = False
        self.rich_log.remove_class(RICHLOG_CLASS_PAUSED)
        self.notify("Streaming resumed...")

        # Flush buffer
        if self._stream_buffer:
            buffered_text = "".join(self._stream_buffer)
            self.current_stream_text += buffered_text
            self._stream_buffer.clear()

    def _update_resource_bar(self) -> None:
        """Refresh the resource bar with current session stats."""
        session = self.state_manager.session
        usage = session.session_total_usage

        # Show actual tokens used from API (prompt + completion)
        actual_tokens = usage.get("prompt_tokens", 0) + usage.get("completion_tokens", 0)

        self.resource_bar.update_stats(
            model=session.current_model,
            tokens=actual_tokens,
            max_tokens=session.max_tokens or 200000,
            session_cost=usage.get("cost", 0.0),
        )


async def run_textual_repl(state_manager: StateManager) -> None:
    """Launch the Textual REPL application."""
    app = TextualReplApp(state_manager=state_manager)
    await app.run_async()


def build_textual_tool_callback(app: TextualReplApp, state_manager: StateManager):
    """Create a tool callback using the Textual confirmation flow."""

    async def _callback(part: Any, _node: Any = None) -> None:
        tool_handler = state_manager.tool_handler or ToolHandler(state_manager)
        state_manager.set_tool_handler(tool_handler)

        if not tool_handler.should_confirm(part.tool_name):
            return

        from tunacode.cli.command_parser import parse_args
        from tunacode.exceptions import UserAbortError

        args = parse_args(part.args)
        request = tool_handler.create_confirmation_request(part.tool_name, args)
        response = await app.request_tool_confirmation(request)
        if not tool_handler.process_confirmation(response, part.tool_name):
            raise UserAbortError("User aborted tool execution")

    return _callback


def build_tool_result_callback(app: TextualReplApp):
    """Create a callback to display tool results as panels in RichLog.

    Called after each tool execution completes with structured data.
    """

    def _callback(
        tool_name: str,
        status: str,
        args: dict,
        result: str | None = None,
        duration_ms: float | None = None,
    ) -> None:
        app.post_message(
            ToolResultDisplay(
                tool_name=tool_name,
                status=status,
                args=args,
                result=result,
                duration_ms=duration_ms,
            )
        )

    return _callback
