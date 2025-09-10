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

from kimi_cli.command import get_command, get_commands
from kimi_cli.soul import Soul


class _PrintAction(NamedTuple):
    func: Callable[..., None]
    args: tuple[Any, ...]


class _StepSep:
    pass


class _AgentMessagePrinter:
    def __init__(
        self,
        impl: "_AgentMessagePrinterImpl",
        action_queue: asyncio.Queue[_PrintAction | _StepSep | None],
    ):
        self._impl = impl
        self._action_queue = action_queue

    def _end_of_run(self):
        self._action_queue.put_nowait(None)

    def separate_step(self):
        self._action_queue.put_nowait(_StepSep())

    def ensure_new_line(self):
        self._action_queue.put_nowait(_PrintAction(self._impl.ensure_new_line, ()))

    def println(self, text: str = ""):
        self._action_queue.put_nowait(_PrintAction(self._impl.println, (text,)))

    def print_message_part(self, part: StreamedMessagePart):
        self._action_queue.put_nowait(_PrintAction(self._impl.print_message_part, (part,)))


class _AgentMessagePrinterImpl:
    def __init__(self, console: Console):
        self._console = console
        self._last_part_type: type[StreamedMessagePart] | None = None
        self._n_tool_call_args_parts = 0

    def separate_step(self):
        self.ensure_new_line()

    def ensure_new_line(self):
        if self._last_part_type is not None:
            self.println()
            self._last_part_type = None

    def println(self, text: str = ""):
        self._console.print(escape(text))
        self._last_part_type = None

    def print_message_part(self, part: StreamedMessagePart):
        match part:
            case str(text) | TextPart(text=text):
                if (self._last_part_type or TextPart) is not TextPart:
                    self.ensure_new_line()
                self._console.print(text, end="")
                self._last_part_type = TextPart
            case ToolCall(function=function):
                self.ensure_new_line()
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


_WELCOME_MESSAGE = """
[bold]Welcome to {name}![/bold]

[grey30]Model: {model} [/grey30]
[grey30]Workspace: {workspace} [/grey30]
""".strip()


class App:
    def __init__(self, agent: Soul):
        self.agent = agent
        self.console = Console(highlight=False)

    async def run(self):
        printer_impl = _AgentMessagePrinterImpl(self.console)
        print_action_queue = asyncio.Queue[_PrintAction | _StepSep | None]()
        printer = _AgentMessagePrinter(printer_impl, print_action_queue)

        username = getpass.getuser()

        command_completer = WordCompleter(
            [f"/{command.name}" for command in get_commands()],
            meta_dict={f"/{command.name}": command.description for command in get_commands()},
            ignore_case=True,
            match_middle=False,
            sentence=True,
        )

        session = PromptSession(
            message=FormattedText([("bold", f"{username}✨ ")]),
            prompt_continuation=FormattedText([("fg:#4d4d4d", "... ")]),
            completer=command_completer,
            complete_while_typing=True,
        )

        welcome = _WELCOME_MESSAGE.format(
            name=self.agent.name,
            model=self.agent.model,
            workspace=Path.cwd().absolute(),
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
                printer_impl.ensure_new_line()
                printer_impl.println("Bye!")
                break
            if user_input.startswith("/"):
                await self._run_command(user_input[1:])
                continue

            run_task = asyncio.create_task(self._run_agent(user_input, printer))
            while True:
                # spin the moon at the beginning of each step
                with self.console.status("", spinner="moon"):
                    action = await print_action_queue.get()

                while isinstance(action, _PrintAction):
                    action.func(*action.args)
                    action = await print_action_queue.get()

                if isinstance(action, _StepSep):
                    printer_impl.separate_step()
                    continue
                if action is None:
                    break

            try:
                await run_task
            except:
                raise
            finally:
                printer_impl.ensure_new_line()

    async def _run_agent(self, user_input: str, printer: _AgentMessagePrinter):
        try:
            await self.agent.run(user_input, printer)
        finally:
            printer._end_of_run()

    async def _run_command(self, command_str: str):
        parts = command_str.split(" ")
        command_name = parts[0]
        command_args = parts[1:]
        command = get_command(command_name)
        if command is None:
            self.console.print(f"Meta command /{command_name} not found")
            return
        ret = command.func(self, command_args)
        if inspect.isawaitable(ret):
            await ret
