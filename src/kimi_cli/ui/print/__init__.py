import asyncio

from kosong.base.message import ContentPart, TextPart, ToolCall, ToolCallPart
from kosong.tooling import ToolResult

from kimi_cli.event import ContextUsageUpdate, EventQueue, RunEnd, StepInterrupted
from kimi_cli.soul import Soul


class PrintApp:
    def __init__(self, soul: Soul):
        self.soul = soul

    def run(self, command: str):
        if not command:
            return

        asyncio.run(self.soul.run(command, self._visualize))

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
