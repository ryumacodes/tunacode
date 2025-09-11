from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, NamedTuple

from rich.panel import Panel

if TYPE_CHECKING:
    from kimi_cli.app import App


class MetaCommand(NamedTuple):
    name: str
    description: str
    func: Callable[["App", list[str]], Awaitable[None] | None]


_meta_commands: dict[str, MetaCommand] = {}


def get_meta_command(name: str) -> MetaCommand | None:
    return _meta_commands.get(name)


def get_meta_commands() -> list[MetaCommand]:
    return list(_meta_commands.values())


def meta_command(func: Callable[["App", list[str]], None]):
    _meta_commands[func.__name__] = MetaCommand(
        name=func.__name__,
        description=(func.__doc__ or "").strip(),
        func=func,
    )
    return func


@meta_command
def exit(app: "App", args: list[str]):
    """Exit the application."""
    # should be handled by `App`
    raise NotImplementedError


@meta_command
def quit(app: "App", args: list[str]):
    """Quit the application."""
    # should be handled by `App`
    raise NotImplementedError


@meta_command
def help(app: "App", args: list[str]):
    """Show help information."""
    app.console.print(
        Panel(
            f"Send message to {app.agent.name} to get things done!\n\n"
            "Meta commands are also available:\n\n"
            + "\n".join(
                f"  /{command.name}: {command.description}" for command in get_meta_commands()
            ),
            border_style="wheat4",
            expand=False,
            padding=(1, 2),
        )
    )
