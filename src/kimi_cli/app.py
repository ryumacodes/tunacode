import getpass
import inspect
from pathlib import Path

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.patch_stdout import patch_stdout
from rich.panel import Panel

from kimi_cli.console import console
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

    async def run(self, command: str | None = None):
        if command is not None:
            # run single command and exit
            await self.agent.run(command)
            return

        meta_command_completer = WordCompleter(
            [f"/{command.name}" for command in get_meta_commands()],
            meta_dict={f"/{command.name}": command.description for command in get_meta_commands()},
            ignore_case=True,
            match_middle=False,
            sentence=True,
        )
        session = PromptSession(
            message=FormattedText([("bold", f"{getpass.getuser()}✨ ")]),
            prompt_continuation=FormattedText([("fg:#4d4d4d", "... ")]),
            completer=meta_command_completer,
            complete_while_typing=True,
        )

        welcome = _WELCOME_MESSAGE.format(
            name=self.agent.name,
            model=self.agent.model,
            work_dir=Path.cwd().absolute(),
        )
        console.print()
        console.print(
            Panel(
                welcome,
                border_style="blue",
                expand=False,
                padding=(1, 2),
            )
        )
        console.print()

        while True:
            with patch_stdout():
                user_input = str(await session.prompt_async()).strip()
            if not user_input:
                continue

            if user_input in ["exit", "quit", "/exit", "/quit"]:
                console.print("Bye!")
                break
            if user_input.startswith("/"):
                await self._run_meta_command(user_input[1:])
                continue

            await self.agent.run(user_input)

    async def _run_meta_command(self, command_str: str):
        parts = command_str.split(" ")
        command_name = parts[0]
        command_args = parts[1:]
        command = get_meta_command(command_name)
        if command is None:
            console.print(f"Meta command /{command_name} not found")
            return
        ret = command.func(self, command_args)
        if inspect.isawaitable(ret):
            await ret
