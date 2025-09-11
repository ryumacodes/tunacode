import asyncio
import getpass
import inspect
from collections.abc import Callable
from pathlib import Path
from typing import Any, NamedTuple

from kosong.base.chat_provider import StreamedMessagePart
from kosong.base.message import TextPart, ToolCall, ToolCallPart
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.patch_stdout import patch_stdout
from rich.console import Console
from rich.markup import escape
from rich.panel import Panel

from kimi_cli.meta_command import get_meta_command, get_meta_commands
from kimi_cli.soul import Soul

_WELCOME_MESSAGE = """
[bold]Welcome to {name}![/bold]

[grey30]Model: {model} [/grey30]
[grey30]Working directory: {work_dir} [/grey30]
""".strip()


class App:
    def __init__(self, agent: Soul):
        self.agent = agent
        self.console = Console(highlight=False)

    async def run(self, command: str | None = None):
        print = _StreamPrint(self.console)
        print_queue = asyncio.Queue[_PrintAction | None]()
        print_producer = _StreamPrintProducer(print_queue, print)

        username = getpass.getuser()

        meta_command_completer = WordCompleter(
            [f"/{command.name}" for command in get_meta_commands()],
            meta_dict={f"/{command.name}": command.description for command in get_meta_commands()},
            ignore_case=True,
            match_middle=False,
            sentence=True,
        )

        session = PromptSession(
            message=FormattedText([("bold", f"{username}✨ ")]),
            prompt_continuation=FormattedText([("fg:#4d4d4d", "... ")]),
            completer=meta_command_completer,
            complete_while_typing=True,
        )

        if command is not None:
            # run single command and exit
            run_task = asyncio.create_task(self.agent.run(command, print_producer))
            await self._print_loop(print_queue)
            try:
                await run_task
            finally:
                print.ensure_nl()
            return

        welcome = _WELCOME_MESSAGE.format(
            name=self.agent.name,
            model=self.agent.model,
            work_dir=Path.cwd().absolute(),
        )
        self.console.print()
        self.console.print(
            Panel(
                welcome,
                border_style="blue",
                expand=False,
                padding=(1, 2),
            )
        )
        self.console.print()

        while True:
            with patch_stdout():
                user_input = str(await session.prompt_async()).strip()
            if not user_input:
                continue

            if user_input in ["exit", "quit", "/exit", "/quit"]:
                print.ensure_nl()
                print.line("Bye!")
                break
            if user_input.startswith("/"):
                await self._run_meta_command(user_input[1:])
                continue

            run_task = asyncio.create_task(self.agent.run(user_input, print_producer))
            await self._print_loop(print_queue)
            try:
                await run_task
            finally:
                print.ensure_nl()

    async def _print_loop(
        self,
        print_queue: asyncio.Queue["_PrintAction | None"],
    ):
        while True:
            # spin the moon at the beginning of each step
            with self.console.status("", spinner="moon"):
                action = await print_queue.get()
            while isinstance(action, _PrintAction):
                action.func(*action.args)
                action = await print_queue.get()
            if action is None:
                break

    async def _run_meta_command(self, command_str: str):
        parts = command_str.split(" ")
        command_name = parts[0]
        command_args = parts[1:]
        command = get_meta_command(command_name)
        if command is None:
            self.console.print(f"Meta command /{command_name} not found")
            return
        ret = command.func(self, command_args)
        if inspect.isawaitable(ret):
            await ret


class _PrintAction(NamedTuple):
    func: Callable[..., None]
    args: tuple[Any, ...]


class _StreamPrintProducer:
    def __init__(
        self,
        action_queue: asyncio.Queue[_PrintAction | None],
        print: "_StreamPrint",
    ):
        self._action_queue = action_queue
        self._print = print

    def start_step(self, n: int):
        self._action_queue.put_nowait(_PrintAction(self._print.start_step, (n,)))

    def end_step(self, n: int):
        self._action_queue.put_nowait(_PrintAction(self._print.end_step, (n,)))

    def end_run(self):
        self._action_queue.put_nowait(None)

    def ensure_nl(self):
        self._action_queue.put_nowait(_PrintAction(self._print.ensure_nl, ()))

    def line(self, text: str = ""):
        self._action_queue.put_nowait(_PrintAction(self._print.line, (text,)))

    def message_part(self, part: StreamedMessagePart):
        self._action_queue.put_nowait(_PrintAction(self._print.message_part, (part,)))


class _StreamPrint:
    def __init__(self, console: Console):
        self._console = console
        self._last_part_type: type[StreamedMessagePart] | None = None
        self._n_tool_call_args_parts = 0

    def start_step(self, n: int):
        self.ensure_nl()

    def end_step(self, n: int):
        pass

    def ensure_nl(self):
        if self._last_part_type is not None:
            self.line()
            self._last_part_type = None

    def line(self, text: str = ""):
        self._console.print(escape(text))
        self._last_part_type = None

    def message_part(self, part: StreamedMessagePart):
        match part:
            case str(text) | TextPart(text=text):
                if (self._last_part_type or TextPart) is not TextPart:
                    self.ensure_nl()
                self._console.print(text, end="")
                self._last_part_type = TextPart
            case ToolCall(function=function):
                self.ensure_nl()
                self._console.print(
                    f"Using [underline]{function.name}[/underline][grey30]...[/grey30]", end=""
                )
                self._last_part_type = ToolCall
            case ToolCallPart():
                if self._last_part_type not in [ToolCall, ToolCallPart]:
                    return
                self._n_tool_call_args_parts += 1
                if self._n_tool_call_args_parts == 10:
                    self._console.print("[grey30].[/grey30]", end="")
                    self._n_tool_call_args_parts = 0
                self._last_part_type = ToolCallPart
