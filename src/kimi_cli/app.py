import asyncio
import getpass
from pathlib import Path

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.patch_stdout import patch_stdout
from rich.panel import Panel

from kimi_cli.console import console
from kimi_cli.metacmd import get_meta_command, get_meta_commands
from kimi_cli.metadata import SessionMeta
from kimi_cli.soul import Soul

_WELCOME_MESSAGE = """
[bold]Welcome to {name}![/bold]

[grey30]Model: {model}[/grey30]
[grey30]Working directory: {work_dir}[/grey30]
[grey30]Session: {session_name}[/grey30]
""".strip()


class App:
    def __init__(self, soul: Soul, session: SessionMeta):
        self.soul = soul
        self.session = session

    def run(self, command: str | None = None):
        if command is not None:
            # run single command and exit
            asyncio.run(self.soul.run(command))
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
            name=self.soul.name,
            model=self.soul.model,
            work_dir=Path.cwd().absolute(),
            session_name=self.session.name,
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
                user_input = str(session.prompt()).strip()
            if not user_input:
                continue

            if user_input in ["exit", "quit", "/exit", "/quit"]:
                console.print("Bye!")
                break
            if user_input.startswith("/"):
                self._run_meta_command(user_input[1:])
                continue

            try:
                asyncio.run(self.soul.run(user_input))
            except KeyboardInterrupt:
                console.print("[bold red]Interrupted by user[/bold red]")
                continue

    def _run_meta_command(self, command_str: str):
        parts = command_str.split(" ")
        command_name = parts[0]
        command_args = parts[1:]
        command = get_meta_command(command_name)
        if command is None:
            console.print(f"Meta command /{command_name} not found")
            return
        command.func(self, command_args)
