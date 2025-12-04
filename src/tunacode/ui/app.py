"""Textual-based REPL shell - Application entry point."""

from __future__ import annotations

import asyncio
from typing import Any

from rich.text import Text
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.message import Message
from textual.widgets import RichLog

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
from tunacode.ui.renderers.errors import render_exception
from tunacode.ui.renderers.panels import tool_panel_smart
from tunacode.ui.screens import ToolConfirmationModal, ToolConfirmationResult
from tunacode.ui.widgets import (
    Editor,
    EditorCompletionsAvailable,
    EditorSubmitRequested,
    ResourceBar,
    StatusBar,
    ToolResultDisplay,
)


class ShowToolConfirmationModal(Message):
    def __init__(self, *, request: ToolConfirmationRequest) -> None:
        super().__init__()
        self.request = request


class TextualReplApp(App[None]):
    TITLE = "TunaCode"
    CSS_PATH = "app.tcss"

    BINDINGS = [
        Binding("ctrl+p", "toggle_pause", "Pause/Resume Stream", show=False, priority=True),
        Binding("escape", "cancel_stream", "Cancel", show=False, priority=True),
    ]

    def __init__(self, *, state_manager: StateManager, show_wizard: bool = False) -> None:
        super().__init__()
        self.state_manager: StateManager = state_manager
        self.request_queue: asyncio.Queue[str] = asyncio.Queue()
        self.pending_confirmation: asyncio.Future[ToolConfirmationResponse] | None = None
        self._show_wizard: bool = show_wizard

        self._streaming_paused: bool = False
        self._streaming_cancelled: bool = False
        self._stream_buffer: list[str] = []
        self.current_stream_text: str = ""
        self._current_request_task: asyncio.Task | None = None

        self.rich_log: RichLog
        self.editor: Editor
        self.resource_bar: ResourceBar
        self.status_bar: StatusBar

    def compose(self) -> ComposeResult:
        self.resource_bar = ResourceBar()
        self.rich_log = RichLog(wrap=True, markup=False, highlight=False, auto_scroll=True)
        self.editor = Editor()
        self.status_bar = StatusBar()

        yield self.resource_bar
        yield self.rich_log
        yield self.editor
        yield self.status_bar

    def on_mount(self) -> None:
        tunacode_theme = build_tunacode_theme()
        self.register_theme(tunacode_theme)
        self.theme = THEME_NAME

        self.set_focus(self.editor)
        self.run_worker(self._request_worker, exclusive=False)
        self._update_resource_bar()
        self._show_welcome()

        if self._show_wizard:
            from tunacode.ui.screens import SetupWizardScreen

            self.push_screen(SetupWizardScreen(self.state_manager))

    def _show_welcome(self) -> None:
        welcome = Text()
        welcome.append("🍣 Welcome to TunaCode\n", style="magenta bold")
        welcome.append("AI-powered coding assistant in your terminal.\n\n", style="dim")
        welcome.append("What I can do:\n", style="cyan")
        welcome.append("  • Read, write, and edit files\n", style="")
        welcome.append("  • Run shell commands\n", style="")
        welcome.append("  • Search code with grep/glob\n", style="")
        welcome.append("  • Answer questions about your codebase\n", style="")
        welcome.append("  • Help debug and refactor code\n", style="")
        self.rich_log.write(welcome)

    async def _request_worker(self) -> None:
        while True:
            request = await self.request_queue.get()
            try:
                await self._process_request(request)
            except Exception as e:
                error_renderable = render_exception(e)
                self.rich_log.write(error_renderable)
            finally:
                self.request_queue.task_done()

    async def _process_request(self, message: str) -> None:
        self.current_stream_text = ""
        self._streaming_cancelled = False
        self.rich_log.add_class(RICHLOG_CLASS_STREAMING)

        try:
            model_name = self.state_manager.session.current_model or "openai/gpt-4o"

            self._current_request_task = asyncio.create_task(
                process_request(
                    message=message,
                    model=ModelName(model_name),
                    state_manager=self.state_manager,
                    tool_callback=build_textual_tool_callback(self, self.state_manager),
                    streaming_callback=self.streaming_callback,
                    tool_result_callback=build_tool_result_callback(self),
                    tool_start_callback=build_tool_start_callback(self),
                )
            )
            await self._current_request_task
        except asyncio.CancelledError:
            self.notify("Cancelled")
        except Exception as e:
            error_renderable = render_exception(e)
            self.rich_log.write(error_renderable)
        finally:
            self._current_request_task = None
            self.rich_log.remove_class(RICHLOG_CLASS_STREAMING)
            self.rich_log.remove_class(RICHLOG_CLASS_PAUSED)

            if self.current_stream_text and not self._streaming_cancelled:
                self.rich_log.write(self.current_stream_text)

            self.current_stream_text = ""
            self._streaming_cancelled = False
            self._update_resource_bar()
            self.status_bar.update_bg_status("")

    def on_editor_completions_available(self, message: EditorCompletionsAvailable) -> None:
        self.rich_log.write(f"Suggestions: {', '.join(message.candidates)}")

    async def on_editor_submit_requested(self, message: EditorSubmitRequested) -> None:
        from tunacode.ui.commands import handle_command

        if await handle_command(self, message.text):
            return

        await self.request_queue.put(message.text)

        from datetime import datetime

        timestamp = datetime.now().strftime("%I:%M %p").lstrip("0")
        user_block = Text()
        user_block.append(f"│ {message.text}\n", style="cyan")
        user_block.append(f"│ tc {timestamp}", style="dim cyan")
        self.rich_log.write(user_block)

    async def request_tool_confirmation(
        self, request: ToolConfirmationRequest
    ) -> ToolConfirmationResponse:
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
        panel = tool_panel_smart(
            name=message.tool_name,
            status=message.status,
            args=message.args,
            result=message.result,
            duration_ms=message.duration_ms,
        )
        self.rich_log.write(panel)

    async def streaming_callback(self, chunk: str) -> None:
        if self._streaming_paused:
            self._stream_buffer.append(chunk)
        else:
            self.current_stream_text += chunk
            self.rich_log.scroll_end()

    def action_toggle_pause(self) -> None:
        if self._streaming_paused:
            self.resume_streaming()
        else:
            self.pause_streaming()

    def pause_streaming(self) -> None:
        self._streaming_paused = True
        self.rich_log.add_class(RICHLOG_CLASS_PAUSED)
        self.notify("Streaming paused...")

    def resume_streaming(self) -> None:
        self._streaming_paused = False
        self.rich_log.remove_class(RICHLOG_CLASS_PAUSED)
        self.notify("Streaming resumed...")

        if self._stream_buffer:
            buffered_text = "".join(self._stream_buffer)
            self.current_stream_text += buffered_text
            self._stream_buffer.clear()

    def action_cancel_stream(self) -> None:
        if self._current_request_task is None:
            return
        self._streaming_cancelled = True
        self._stream_buffer.clear()
        self.current_stream_text = ""
        self._current_request_task.cancel()

    def _update_resource_bar(self) -> None:
        session = self.state_manager.session
        usage = session.session_total_usage

        actual_tokens = usage.get("prompt_tokens", 0) + usage.get("completion_tokens", 0)

        self.resource_bar.update_stats(
            model=session.current_model or "No model selected",
            tokens=actual_tokens,
            max_tokens=session.max_tokens or 200000,
            session_cost=usage.get("cost", 0.0),
        )


async def run_textual_repl(state_manager: StateManager, show_wizard: bool = False) -> None:
    app = TextualReplApp(state_manager=state_manager, show_wizard=show_wizard)
    await app.run_async()


def build_textual_tool_callback(app: TextualReplApp, state_manager: StateManager):
    async def _callback(part: Any, _node: Any = None) -> None:
        tool_handler = state_manager.tool_handler or ToolHandler(state_manager)
        state_manager.set_tool_handler(tool_handler)

        if not tool_handler.should_confirm(part.tool_name):
            return

        from tunacode.exceptions import UserAbortError
        from tunacode.utils.parsing.command_parser import parse_args

        args = parse_args(part.args)
        request = tool_handler.create_confirmation_request(part.tool_name, args)
        response = await app.request_tool_confirmation(request)
        if not tool_handler.process_confirmation(response, part.tool_name):
            raise UserAbortError("User aborted tool execution")

    return _callback


def build_tool_result_callback(app: TextualReplApp):
    def _callback(
        tool_name: str,
        status: str,
        args: dict,
        result: str | None = None,
        duration_ms: float | None = None,
    ) -> None:
        app.status_bar.update_last_action(tool_name)

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


def build_tool_start_callback(app: TextualReplApp):
    def _callback(tool_name: str) -> None:
        app.status_bar.update_bg_status(tool_name)

    return _callback
