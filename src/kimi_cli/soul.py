import asyncio
from collections.abc import Callable
from typing import Any, NamedTuple

import kosong
from kosong import StepResult
from kosong.base.chat_provider import ChatProvider, StreamedMessagePart
from kosong.base.message import Message, TextPart, ToolCall, ToolCallPart
from kosong.context import LinearContext
from kosong.context.linear import LinearStorage
from kosong.tooling import ToolResult, Toolset
from rich.markup import escape

from kimi_cli.console import console
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

    async def run(self, user_input: str, max_steps: int | None = None):
        context = self._get_context()
        await context.add_message(Message(role="user", content=user_input))

        print = _StreamPrint()
        print_queue = _PrintQueue()
        print_producer = _StreamPrintProducer(print_queue, print)

        agent_loop_task = asyncio.create_task(self._agent_loop(context, print_producer, max_steps))
        try:
            await self._print_loop(print_queue)
            await agent_loop_task
        finally:
            print.ensure_nl()

    async def _print_loop(self, print_queue: "_PrintQueue"):
        while True:
            # spin the moon at the beginning of each step
            with console.status("", spinner="moon"):
                await asyncio.sleep(0.5)
                action = await print_queue.get()
            while isinstance(action, _PrintAction):
                action.func(*action.args)
                action = await print_queue.get()
            if isinstance(action, _StepSep):
                continue
            if action is None:
                break

    async def _agent_loop(
        self,
        context: LinearContext,
        print: "_StreamPrintProducer",
        max_steps: int | None = None,
    ):
        try:
            n_steps = 0
            while True:
                print.start_step(n_steps)
                finished = await self._step(context, print)
                n_steps += 1
                if finished:
                    return
                if max_steps is not None and n_steps > max_steps:
                    # TODO: print some warning
                    return
        finally:
            print.end_run()

    async def _step(self, context: LinearContext, print: "_StreamPrintProducer") -> bool:
        """Run an single step and return whether the run is finished."""
        # run an LLM step (may be interrupted)
        result = await kosong.step(
            self._chat_provider,
            context,
            on_message_part=print.message_part,
        )
        print.ensure_nl()

        # wait for all tool results (may be interrupted)
        results = await result.tool_results()
        # shield the context manipulation from interruption
        await asyncio.shield(self._grow_context(result, results))

        return not result.tool_calls

    async def _grow_context(self, result: StepResult, tool_results: list[ToolResult]):
        context = self._get_context()
        await context.add_message(result.message)
        for tool_result in tool_results:
            for message in tool_result_to_messages(tool_result):
                await context.add_message(message)


class _PrintAction(NamedTuple):
    func: Callable[..., None]
    args: tuple[Any, ...]


class _StepSep:
    pass


_PrintQueue = asyncio.Queue[_PrintAction | _StepSep | None]


class _StreamPrintProducer:
    def __init__(self, print_queue: _PrintQueue, print: "_StreamPrint"):
        self._print_queue = print_queue
        self._print = print

    def start_step(self, n: int):
        self._print_queue.put_nowait(_PrintAction(self._print.step_begin, ()))
        if n > 0:
            self._print_queue.put_nowait(_StepSep())

    def end_run(self):
        self._print_queue.put_nowait(None)

    def ensure_nl(self):
        self._print_queue.put_nowait(_PrintAction(self._print.ensure_nl, ()))

    def line(self, text: str = ""):
        self._print_queue.put_nowait(_PrintAction(self._print.line, (text,)))

    def message_part(self, part: StreamedMessagePart):
        self._print_queue.put_nowait(_PrintAction(self._print.message_part, (part,)))


class _StreamPrint:
    def __init__(self):
        self._last_part_type: type[StreamedMessagePart] | None = None
        self._n_tool_call_args_parts = 0

    def step_begin(self):
        self.ensure_nl()

    def ensure_nl(self):
        if self._last_part_type is not None:
            self.line()
            self._last_part_type = None

    def line(self, text: str = ""):
        console.print(escape(text))
        self._last_part_type = None

    def message_part(self, part: StreamedMessagePart):
        match part:
            case str(text) | TextPart(text=text):
                if (self._last_part_type or TextPart) is not TextPart:
                    self.ensure_nl()
                console.print(text, end="")
                self._last_part_type = TextPart
            case ToolCall(function=function):
                self.ensure_nl()
                console.print(
                    f"Using [underline]{function.name}[/underline][grey30]...[/grey30]", end=""
                )
                self._last_part_type = ToolCall
            case ToolCallPart():
                if self._last_part_type not in [ToolCall, ToolCallPart]:
                    return
                self._n_tool_call_args_parts += 1
                if self._n_tool_call_args_parts == 10:
                    console.print("[grey30].[/grey30]", end="")
                    self._n_tool_call_args_parts = 0
                self._last_part_type = ToolCallPart
