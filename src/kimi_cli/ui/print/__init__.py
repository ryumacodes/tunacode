import asyncio
from typing import override

from kosong.base.message import ContentPart, TextPart, ToolCall, ToolCallPart
from kosong.chat_provider import ChatProviderError
from kosong.tooling import ToolResult

from kimi_cli.event import ContextUsageUpdate, EventQueue, RunEnd, StepInterrupted
from kimi_cli.logging import logger
from kimi_cli.soul import MaxStepsReached, Soul
from kimi_cli.ui import BaseApp


class PrintApp(BaseApp):
    def __init__(self, soul: Soul):
        self.soul = soul

    @override
    def run(self, command: str | None = None) -> bool:
        if not command:
            return False

        # TODO: maybe unify with `_soul_run` in `ShellApp`
        try:
            logger.info("Running agent with command: {command}", command=command)
            asyncio.run(self.soul.run(command, self._visualize))
            return True
        except ChatProviderError as e:
            logger.exception("LLM provider error:")
            print(f"LLM provider error: {e}")
        except MaxStepsReached as e:
            logger.warning("Max steps reached: {n_steps}", n_steps=e.n_steps)
            print(f"Max steps reached: {e.n_steps}")
        except KeyboardInterrupt:
            logger.error("Interrupted by user")
            print("Interrupted by user")
        except BaseException as e:
            logger.exception("Unknown error:")
            print(f"Unknown error: {e}")
        return False

    async def _visualize(self, event_queue: EventQueue):
        while True:
            event = await event_queue.get()
            if isinstance(event, StepInterrupted | RunEnd):
                break

            match event:
                case TextPart(text=text):
                    print(text)
                case ContentPart():
                    print(f"Content part: {event}")
                case ToolCall():
                    print(f"Using `{event.function.name}` with args: {event.function.arguments}")
                case ToolCallPart():
                    print(f"Tool call part: {event.arguments_part}")
                case ToolResult():
                    print(f"Tool result: {event.result}")
                case ContextUsageUpdate(usage_percentage=usage):
                    print(f"Context usage: {usage:.1%}")
                case _:
                    pass
