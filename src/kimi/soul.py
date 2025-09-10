from typing import Protocol, runtime_checkable

import kosong
from kosong.base.chat_provider import ChatProvider, StreamedMessagePart
from kosong.base.message import Message
from kosong.context import LinearContext
from kosong.tooling import Toolset

from kimi.utils.message import tool_result_to_messages


class Soul:
    def __init__(
        self,
        name: str,
        *,
        chat_provider: ChatProvider,
        system_prompt: str,
        toolset: Toolset,
    ):
        self.name = name
        self._chat_provider = chat_provider
        self._system_prompt = system_prompt
        self._toolset = toolset
        self._context: LinearContext | None = None

    @property
    def model(self) -> str:
        return self._chat_provider.model_name

    def _get_context(self) -> LinearContext:
        if self._context is None:
            self._context = LinearContext(
                system_prompt=self._system_prompt,
                toolset=self._toolset,
            )
        return self._context

    async def run(self, user_input: str, printer: "Printer", max_steps: int | None = None):
        context = self._get_context()
        await context.add_message(Message(role="user", content=user_input))

        n_steps = 0
        while True:
            if n_steps > 0:
                printer.separate_step()

            result = await kosong.step(
                self._chat_provider,
                context,
                on_message_part=printer.print_message_part,
            )
            printer.ensure_new_line()

            await context.add_message(result.message)
            for tool_result in await result.tool_results():
                for message in tool_result_to_messages(tool_result):
                    await context.add_message(message)

            if not result.tool_calls or (max_steps is not None and n_steps >= max_steps):
                return result.message.content

            n_steps += 1


@runtime_checkable
class Printer(Protocol):
    def separate_step(self): ...
    def ensure_new_line(self): ...
    def println(self, text: str = ""): ...
    def print_message_part(self, part: StreamedMessagePart): ...
