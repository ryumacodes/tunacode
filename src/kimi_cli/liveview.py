import streamingjson
from kosong.base.message import ToolCall, ToolCallPart
from rich.console import Group, RenderableType
from rich.live import Live
from rich.spinner import Spinner
from rich.text import Text

from kimi_cli.console import console


class _ToolCallDisplay:
    def __init__(self, tool_call: ToolCall):
        self.tool_call = tool_call
        self.lexer = streamingjson.Lexer()
        if tool_call.function.arguments is not None:
            self.lexer.append_string(tool_call.function.arguments)
        headline = f"using [bold blue]{tool_call.function.name}[/bold blue][grey50]...[/grey50]"
        self.renderable: Spinner | Text = Spinner("dots", text=headline)


class StepLiveView:
    def __init__(self):
        self._text = Text("")
        self._tool_calls: dict[str, _ToolCallDisplay] = {}
        self._last_tool_call: _ToolCallDisplay | None = None

    def __enter__(self):
        self.live = Live(self._compose(), console=console, refresh_per_second=4)
        self.live.__enter__()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.live.__exit__(exc_type, exc_value, traceback)

    def _compose(self) -> RenderableType:
        sections = []
        if self._text:
            sections.append(self._text)
        for view in self._tool_calls.values():
            sections.append(view.renderable)
        return Group(*sections)

    def append_text(self, text: str):
        if not self._text:
            self._text = Text(text)
            # update the whole display
            self.live.update(self._compose())
        else:
            # only update the Text
            self._text.append(text)

    def append_tool_call(self, tool_call: ToolCall):
        self._tool_calls[tool_call.id] = _ToolCallDisplay(tool_call)
        self._last_tool_call = self._tool_calls[tool_call.id]
        self.live.update(self._compose())

    def append_tool_call_part(self, tool_call_part: ToolCallPart):
        if not tool_call_part.arguments_part:
            return
        if self._last_tool_call is None:
            return
        self._last_tool_call.lexer.append_string(tool_call_part.arguments_part)
        # TODO: update the tool call view

    def finish_all(self):
        if not self._tool_calls:
            return
        for view in self._tool_calls.values():
            view.renderable = Text.from_markup(
                "[bold green]✓[/bold green] "
                f"used [bold blue]{view.tool_call.function.name}[/bold blue]"
            )
        self.live.update(self._compose())
