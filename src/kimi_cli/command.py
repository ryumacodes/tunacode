from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, NamedTuple

from rich.panel import Panel

if TYPE_CHECKING:
    from kimi_cli.app import App


class Command(NamedTuple):
    name: str
    description: str
    func: Callable[["App", list[str]], Awaitable[None] | None]


_commands: dict[str, Command] = {}


def get_command(name: str) -> Command | None:
    return _commands.get(name)


def get_commands() -> list[Command]:
    return list(_commands.values())


def command(func: Callable[["App", list[str]], None]):
    _commands[func.__name__] = Command(
        name=func.__name__,
        description=(func.__doc__ or "").strip(),
        func=func,
    )
    return func


@command
def exit(app: "App", args: list[str]):
    """Exit the application."""
    # should be handled by `App`
    raise NotImplementedError


@command
def quit(app: "App", args: list[str]):
    """Quit the application."""
    # should be handled by `App`
    raise NotImplementedError


@command
def help(app: "App", args: list[str]):
    """Show help information."""
    app.console.print(
        Panel(
            f"Send message to {app.agent.name} to get things done!\n\n"
            "Meta commands are also available:\n\n"
            + "\n".join(f"  /{command.name}: {command.description}" for command in get_commands()),
            border_style="wheat4",
            expand=False,
            padding=(1, 2),
        )
    )
