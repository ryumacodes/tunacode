import json

import streamingjson
from kosong.base.message import ToolCall, ToolCallPart
from kosong.utils.typing import JsonType
from rich.console import Group, RenderableType
from rich.live import Live
from rich.markup import escape
from rich.spinner import Spinner
from rich.text import Text

from kimi_cli.console import console


class _ToolCallDisplay:
    def __init__(self, tool_call: ToolCall):
        self._tool_name = tool_call.function.name
        self._lexer = streamingjson.Lexer()
        if tool_call.function.arguments is not None:
            self._lexer.append_string(tool_call.function.arguments)

        self._headline_markup = f"using [bold blue]{self._tool_name}[/bold blue]"
        self._detail = _extract_detail(self._lexer, self._tool_name)
        self._renderable: Spinner | Text = Spinner("dots", text=self._spinner_markup)

    @property
    def _detail_markup(self) -> str:
        return f"[grey50]: {escape(self._detail)}[/grey50]" if self._detail else ""

    @property
    def _spinner_markup(self) -> str:
        return self._headline_markup + self._detail_markup

    def append_args_part(self, args_part: str):
        if self.finished:
            return

        if len(self._detail) > 53:
            return
        if len(self._detail) > 50:
            # TODO: better truncation
            new_detail = self._detail + "..."
        else:
            self._lexer.append_string(args_part)
            new_detail = _extract_detail(self._lexer, self._tool_name)

        if new_detail and new_detail != self._detail:
            self._detail = new_detail
            assert isinstance(self._renderable, Spinner)
            self._renderable.update(text=self._spinner_markup)

    def finish(self):
        self._renderable = Text.from_markup(
            f"[bold green]✓[/bold green] "
            f"used [bold blue]{self._tool_name}[/bold blue]" + self._detail_markup
        )

    @property
    def finished(self) -> bool:
        return isinstance(self._renderable, Text)


def _extract_detail(lexer: streamingjson.Lexer, tool_name: str) -> str:
    try:
        curr_args: JsonType = json.loads(lexer.complete_json())
    except json.JSONDecodeError:
        return ""
    if not curr_args:
        return ""
    match tool_name:
        case "shell":
            if not isinstance(curr_args, dict) or not curr_args.get("command"):
                return ""
            return str(curr_args["command"])
        case _:
            return "".join(lexer.json_content)


class StepLiveView:
    def __init__(self):
        self._text = Text("")
        self._tool_calls: dict[str, _ToolCallDisplay] = {}
        self._last_tool_call: _ToolCallDisplay | None = None

    def __enter__(self):
        self._live = Live(self._compose(), console=console, refresh_per_second=4)
        self._live.__enter__()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._live.__exit__(exc_type, exc_value, traceback)

    def _compose(self) -> RenderableType:
        sections = []
        if self._text:
            sections.append(self._text)
        for view in self._tool_calls.values():
            sections.append(view._renderable)
        return Group(*sections)

    def append_text(self, text: str):
        if not self._text:
            self._text = Text(text)
            # update the whole display
            self._live.update(self._compose())
        else:
            # only update the Text
            self._text.append(text)

    def append_tool_call(self, tool_call: ToolCall):
        self._tool_calls[tool_call.id] = _ToolCallDisplay(tool_call)
        self._last_tool_call = self._tool_calls[tool_call.id]
        self._live.update(self._compose())

    def append_tool_call_part(self, tool_call_part: ToolCallPart):
        if not tool_call_part.arguments_part:
            return
        if self._last_tool_call is None:
            return
        self._last_tool_call.append_args_part(tool_call_part.arguments_part)

    def finish_all(self):
        if not self._tool_calls:
            return
        for view in self._tool_calls.values():
            view.finish()
        self._live.update(self._compose())
