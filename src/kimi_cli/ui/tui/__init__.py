import asyncio
import getpass

from kosong.base.message import ContentPart, TextPart, ToolCall, ToolCallPart
from kosong.chat_provider import ChatProviderError
from kosong.tooling import ToolResult
from prompt_toolkit import PromptSession
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.patch_stdout import patch_stdout
from rich.panel import Panel

from kimi_cli.event import (
    ContextUsageUpdate,
    EventQueue,
    RunBegin,
    RunEnd,
    StepBegin,
    StepInterrupted,
)
from kimi_cli.soul import MaxStepsReached, Soul
from kimi_cli.ui.tui.console import console
from kimi_cli.ui.tui.liveview import StepLiveView
from kimi_cli.ui.tui.metacmd import (
    MetaCommandCompleter,
    get_meta_command,
)


class App:
    def __init__(self, soul: Soul, welcome_info: dict[str, str]):
        self.soul = soul
        self.welcome_info = welcome_info

    def run(self, command: str | None = None):
        if command is not None:
            # run single command and exit
            asyncio.run(self.soul.run(command, self._visualize))
            return

        session = PromptSession(
            message=FormattedText([("bold", f"{getpass.getuser()}✨ ")]),
            prompt_continuation=FormattedText([("fg:#4d4d4d", "... ")]),
            completer=MetaCommandCompleter(),
            complete_while_typing=True,
        )

        welcome = f"[bold]Welcome to {self.soul.name}![/bold]"
        if self.welcome_info:
            welcome += "\n\n" + "\n".join(
                f"[grey30]{key}: {value}[/grey30]" for key, value in self.welcome_info.items()
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
            try:
                with patch_stdout():
                    user_input = str(session.prompt()).strip()
            except KeyboardInterrupt:
                console.print("[grey30]Tip: press Ctrl-D or send 'exit' to quit[/grey30]")
                continue
            except EOFError:
                console.print("Bye!")
                break

            if not user_input:
                continue

            if user_input in ["exit", "quit", "/exit", "/quit"]:
                console.print("Bye!")
                break
            if user_input.startswith("/"):
                self._run_meta_command(user_input[1:])
                continue

            try:
                asyncio.run(self.soul.run(user_input, self._visualize))
            except MaxStepsReached as e:
                console.print(f"[bold yellow]Max steps reached: {e.n_steps}[/bold yellow]")
            except ChatProviderError as e:
                console.print(f"[bold red]LLM provider error: {e}[/bold red]")
            except KeyboardInterrupt:
                console.print("[bold red]Interrupted by user[/bold red]")
            except BaseException as e:
                console.print(f"[bold red]Unknown error: {e}[/bold red]")

    async def _visualize(self, event_queue: EventQueue):
        """
        A loop to consume agent events and visualize the agent behavior.
        This loop never raise any exception.
        """
        # expect a RunBegin
        assert isinstance(await event_queue.get(), RunBegin)
        # expect a StepBegin
        assert isinstance(await event_queue.get(), StepBegin)

        while True:
            # spin the moon at the beginning of each step
            with console.status("", spinner="moon"):
                event = await event_queue.get()

            with StepLiveView(self.soul.context_usage) as step:
                # visualization loop for one step
                while True:
                    match event:
                        case TextPart(text=text):
                            step.append_text(text)
                        case ContentPart():
                            # TODO: support more content parts
                            step.append_text(f"[{event.__class__.__name__}]")
                        case ToolCall():
                            step.append_tool_call(event)
                        case ToolCallPart():
                            step.append_tool_call_part(event)
                        case ToolResult():
                            step.append_tool_result(event)
                        case ContextUsageUpdate(usage_percentage=usage):
                            step.update_context_usage(usage)
                        case _:
                            break  # break the step loop
                    event = await event_queue.get()

                # cleanup the step live view
                if isinstance(event, StepInterrupted):
                    step.interrupt()
                else:
                    step.finish()

            if isinstance(event, StepInterrupted):
                # for StepInterrupted, the visualization loop should end immediately
                break

            assert isinstance(event, StepBegin | RunEnd), "expect a StepBegin or RunEnd"
            if isinstance(event, StepBegin):
                # start a new step
                continue
            else:
                # end the run
                break

    def _run_meta_command(self, command_str: str):
        parts = command_str.split(" ")
        command_name = parts[0]
        command_args = parts[1:]
        command = get_meta_command(command_name)
        if command is None:
            console.print(f"Meta command /{command_name} not found")
            return
        command.func(self, command_args)
