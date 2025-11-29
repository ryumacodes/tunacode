"""Textual-based REPL shell skeleton.

This replaces the legacy prompt_toolkit/Rich loop with a Textual App.
Phase coverage (Tasks 1-6):
- Textual app wired as CLI entry point.
- Editor widget with completions and submit handling.
- Tool confirmation modal (Future-based).
- Streaming integration (pause/resume/buffer).
- Real orchestrator wiring (worker loop + process_request).
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Iterable, Optional

from rich.text import Text
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.events import Key
from textual.message import Message
from textual.screen import ModalScreen
from textual.theme import Theme
from textual.widgets import Button, Checkbox, Footer, Header, Label, RichLog, Static, TextArea

from tunacode.cli.commands.registry import CommandRegistry
from tunacode.constants import UI_COLORS
from tunacode.core.agents.main import process_request
from tunacode.core.tool_handler import ToolHandler
from tunacode.types import (
    ModelName,
    StateManager,
    ToolConfirmationRequest,
    ToolConfirmationResponse,
)


def _gather_command_names() -> list[str]:
    registry = CommandRegistry()
    registry.register_all_default_commands()
    return registry.get_command_names()


def _complete_paths(prefix: str) -> list[str]:
    base = Path(prefix).expanduser()
    search_root = base.parent if base.parent != Path(".") else Path.cwd()
    stem = base.name
    candidates: list[str] = []
    try:
        for entry in search_root.iterdir():
            if entry.name.startswith(stem):
                if prefix.startswith("/"):
                    candidate = str(entry)
                else:
                    candidate = entry.name if search_root == Path.cwd() else str(entry)
                suffix = "/" if entry.is_dir() else ""
                candidates.append(candidate + suffix)
    except (FileNotFoundError, PermissionError):
        return []
    return sorted(candidates)


def _replace_token(text: str, start: int, end: int, replacement: str) -> str:
    return text[:start] + replacement + text[end:]


class ResourceBar(Static):
    """Top bar showing resources: tokens, model, cost."""

    def __init__(self) -> None:
        super().__init__("")
        self._tokens: int = 0
        self._max_tokens: int = 200000
        self._model: str = "---"
        self._cost: float = 0.0
        self._session_cost: float = 0.0

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

    def _refresh_display(self) -> None:
        content = Text.assemble(
            ("Model: ", "dim"),
            (self._model, "cyan"),
        )
        self.update(content)


class Editor(TextArea):
    """Multiline editor with Esc+Enter newline binding, Tab completions, and submit on Enter."""

    BINDINGS = [
        Binding("tab", "complete", "Complete", show=False),
        Binding("enter", "submit", "Submit", show=False),
    ]

    def __init__(self, *, language: Optional[str] = None) -> None:
        super().__init__(language=language, placeholder="Enter a request...")
        self._awaiting_escape_enter: bool = False
        self._command_names: list[str] = _gather_command_names()

    def action_complete(self) -> None:
        prefix, start, end = self._current_token()
        if prefix is None:
            return
        if prefix.startswith("/"):
            candidates = [c for c in self._command_names if c.startswith(prefix)]
        elif prefix.startswith("@"):
            candidates = [f"@{c}" for c in _complete_paths(prefix[1:])]
        else:
            candidates = []

        if not candidates:
            return

        replacement = candidates[0]
        self.text = _replace_token(self.text, start, end, replacement)
        cursor_row, cursor_col = self.cursor_location
        self.move_cursor((cursor_row, start + len(replacement)))

        if len(candidates) > 1:
            # Surface alternatives in the log for now; future UI will show a popover.
            self.post_message(EditorCompletionsAvailable(candidates=candidates))

    def action_submit(self) -> None:
        text = self.text.strip()
        if not text:
            return

        self.post_message(EditorSubmitRequested(text=text, raw_text=self.text))
        self.text = ""

    def _current_token(self) -> tuple[Optional[str], int, int]:
        cursor_row, cursor_col = self.cursor_location
        lines = self.text.splitlines()
        if cursor_row >= len(lines):
            return None, cursor_col, cursor_col
        line = lines[cursor_row]
        left = line.rfind(" ", 0, cursor_col) + 1
        token = line[left:cursor_col]
        if not token:
            return None, left, left
        return token, left, left + len(token)

    async def on_key(self, event: Key) -> None:
        if event.key == "escape":
            self._awaiting_escape_enter = True
            event.stop()
            return
        if event.key == "enter" and self._awaiting_escape_enter:
            self._awaiting_escape_enter = False
            event.stop()
            self.insert("\n")
            return
        if event.key == "enter":
            self._awaiting_escape_enter = False
            event.stop()
            self.action_submit()
            return

        self._awaiting_escape_enter = False
        await self._on_key(event)


class EditorCompletionsAvailable(Message):
    """Notify the app when multiple completions are available."""

    def __init__(self, *, candidates: Iterable[str]) -> None:
        super().__init__()
        self.candidates = list(candidates)


class EditorSubmitRequested(Message):
    """Submit event for the current editor content."""

    def __init__(self, *, text: str, raw_text: str) -> None:
        super().__init__()
        self.text = text
        self.raw_text = raw_text


class ShowToolConfirmationModal(Message):
    """Request to show a tool confirmation modal."""

    def __init__(self, *, request: ToolConfirmationRequest) -> None:
        super().__init__()
        self.request = request


class ToolConfirmationResult(Message):
    """Result of a tool confirmation modal."""

    def __init__(self, *, response: ToolConfirmationResponse) -> None:
        super().__init__()
        self.response = response


THEME_NAME = "tunacode"


def _build_tunacode_theme() -> Theme:
    palette = UI_COLORS
    custom_variables = {
        "text-muted": palette["muted"],
        "border": palette["border"],
        "border-light": palette["border_light"],
    }
    return Theme(
        name=THEME_NAME,
        primary=palette["primary"],
        secondary=palette["accent"],
        accent=palette["primary_light"],
        background=palette["background"],
        surface=palette["surface"],
        panel=palette["border_light"],
        success=palette["success"],
        warning=palette["warning"],
        error=palette["error"],
        boost=palette["primary_dark"],
        foreground=palette["primary_light"],
        variables=custom_variables,
    )


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

    def compose(self) -> ComposeResult:
        yield Header()
        yield self.resource_bar
        yield Vertical(self.rich_log, self.streaming_output, self.editor, id="body")
        yield Footer()

    def on_mount(self) -> None:
        # Register custom TunaCode theme using UI_COLORS palette
        tunacode_theme = _build_tunacode_theme()
        self.register_theme(tunacode_theme)
        self.theme = THEME_NAME

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


async def run_textual_repl(state_manager: StateManager) -> None:
    """Launch the Textual REPL application."""
    app = TextualReplApp(state_manager=state_manager)
    await app.run_async()


class ToolConfirmationModal(ModalScreen[None]):
    """Modal that gathers tool confirmation asynchronously."""

    def __init__(self, request: ToolConfirmationRequest) -> None:
        super().__init__()
        self.request = request
        self.skip_future = Checkbox(label="Skip future confirmations for this tool", value=False)

    def compose(self) -> ComposeResult:
        yield Vertical(
            Label(f"Confirm tool: {self.request.tool_name}", id="tool-title"),
            Label(f"Args: {self.request.args}"),
            self.skip_future,
            Horizontal(
                Button("Yes", id="yes", variant="success"),
                Button("No", id="no", variant="error"),
                id="actions",
            ),
            id="modal-body",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        approved = event.button.id == "yes"
        response = ToolConfirmationResponse(
            approved=approved,
            skip_future=self.skip_future.value,
            abort=not approved,
        )
        self.app.post_message(ToolConfirmationResult(response=response))
        self.app.pop_screen()


def build_textual_tool_callback(app: TextualReplApp, state_manager: StateManager):
    """Create a tool callback using the Textual confirmation flow."""

    async def _callback(part, _node=None):
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
