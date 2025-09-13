import json

import streamingjson
from kosong.base.message import ToolCall, ToolCallPart
from kosong.tooling import ToolResult, ToolReturnType
from kosong.tooling.error import ToolError
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

        self._headline_markup = f"Using [bold blue]{self._tool_name}[/bold blue]"
        self._detail = _extract_detail(self._lexer, self._tool_name)
        self._finished = False
        self._spinner = Spinner("dots", text=self._spinner_markup)
        self.renderable: RenderableType = Group(self._spinner)

    @property
    def finished(self) -> bool:
        return self._finished

    @property
    def _detail_markup(self) -> str:
        return f"[grey50]: {escape(self._detail)}[/grey50]" if self._detail else ""

    @property
    def _spinner_markup(self) -> str:
        return self._headline_markup + self._detail_markup

    def append_args_part(self, args_part: str):
        if self.finished:
            return
        if len(self._detail) > 50:
            # TODO: better truncation
            return
        self._lexer.append_string(args_part)
        new_detail = _extract_detail(self._lexer, self._tool_name)
        if new_detail and new_detail != self._detail:
            self._detail = new_detail
            self._spinner.update(text=self._spinner_markup)

    def finish(self, result: ToolReturnType | ToolError):
        """
        Finish the live display of a tool call.
        After calling this, the `renderable` property should be re-rendered.
        """
        self._finished = True
        sign = (
            "[bold red]✗[/bold red]"
            if isinstance(result, ToolError)
            else "[bold green]✓[/bold green]"
        )
        lines = [
            Text.from_markup(
                f"{sign} Used [bold blue]{self._tool_name}[/bold blue]" + self._detail_markup
            )
        ]
        if isinstance(result, ToolError):
            lines.append(Text.from_markup(f"  [red]{result.message}[/red]"))
        self.renderable = Group(*lines)


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
    def __init__(self, context_usage: float):
        self._text = Text("")
        self._tool_calls: dict[str, _ToolCallDisplay] = {}
        self._last_tool_call: _ToolCallDisplay | None = None
        self._context_usage_text: Text | None = Text(
            f"context: {context_usage:.1%}", style="grey50", justify="right"
        )

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
            sections.append(view.renderable)
        sections.append(self._context_usage_text)
        return Group(*sections)

    def append_text(self, text: str):
        if not self._text:
            self._text = Text(text)
            # update the whole display
            self._live.update(self._compose())
        else:
            # only update the Text
            self._text.append(text)
            # TODO: print to console once a `\n` is encountered

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

    def append_tool_result(self, tool_result: ToolResult):
        if view := self._tool_calls.get(tool_result.tool_call_id):
            view.finish(tool_result.result)
            self._live.update(self._compose())

    def update_context_usage(self, usage: float):
        if self._context_usage_text is None:
            return
        self._context_usage_text.plain = f"context: {usage:.1%}"

    def finish(self):
        if not self._tool_calls:
            return
        for view in self._tool_calls.values():
            if not view.finished:
                # this should not happen, but just in case
                view.finish("")
        self._live.update(self._compose())

    def cancel(self):
        if not self._tool_calls:
            return
        for view in self._tool_calls.values():
            if not view.finished:
                view.finish(ToolError("Cancelled"))
        self._live.update(self._compose())
