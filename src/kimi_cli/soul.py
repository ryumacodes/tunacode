from typing import Protocol, runtime_checkable

import kosong
from kosong.base.chat_provider import ChatProvider, StreamedMessagePart
from kosong.base.message import Message
from kosong.context import LinearContext
from kosong.context.linear import LinearStorage
from kosong.tooling import Toolset

from kimi_cli.utils.message import tool_result_to_messages


class Soul:
    def __init__(
        self,
        name: str,
        *,
        chat_provider: ChatProvider,
        system_prompt: str,
        toolset: Toolset,
        context_storage: LinearStorage,
    ):
        self.name = name
        self._chat_provider = chat_provider
        self._system_prompt = system_prompt
        self._toolset = toolset
        self._context_storage = context_storage
        self._context: LinearContext | None = None

    @property
    def model(self) -> str:
        return self._chat_provider.model_name

    def _get_context(self) -> LinearContext:
        if self._context is None:
            self._context = LinearContext(
                system_prompt=self._system_prompt,
                toolset=self._toolset,
                storage=self._context_storage,
            )
        return self._context

    async def run(self, user_input: str, print: "StreamPrint", max_steps: int | None = None):
        context = self._get_context()
        await context.add_message(Message(role="user", content=user_input))
        try:
            return await self._loop(print, max_steps)
        finally:
            print.end_run()

    async def _loop(self, print: "StreamPrint", max_steps: int | None = None):
        context = self._get_context()
        n_steps = 0
        while True:
            print.start_step(n_steps)

            result = await kosong.step(
                self._chat_provider,
                context,
                on_message_part=print.message_part,
            )
            print.ensure_nl()

            await context.add_message(result.message)
            for tool_result in await result.tool_results():
                for message in tool_result_to_messages(tool_result):
                    await context.add_message(message)

            if not result.tool_calls or (max_steps is not None and n_steps >= max_steps):
                return result.message.content

            print.end_step(n_steps)
            n_steps += 1


@runtime_checkable
class StreamPrint(Protocol):
    def start_step(self, n: int):
        """Start a new step."""
        ...

    def end_step(self, n: int):
        """End the current step."""
        ...

    def end_run(self):
        """End the agent run."""
        ...

    def ensure_nl(self):
        """Ensure the printer is at the beginning of a new line."""
        ...

    def line(self, text: str = ""):
        """Print a text + line break."""
        ...

    def message_part(self, part: StreamedMessagePart):
        """Print a message part."""
        ...
