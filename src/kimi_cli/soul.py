import asyncio

import kosong
from kosong import StepResult
from kosong.base.chat_provider import ChatProvider
from kosong.base.message import ContentPart, Message, TextPart, ToolCall, ToolCallPart
from kosong.context import LinearContext
from kosong.context.linear import LinearStorage
from kosong.tooling import ToolResult, Toolset

from kimi_cli.console import console
from kimi_cli.event import ContextUsageUpdate, EventQueue, RunBegin, RunEnd, StepBegin
from kimi_cli.liveview import StepLiveView
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
        self._max_context_size: int = 200_000  # unit: tokens
        self._context_size: int = 0  # unit: tokens

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

    @property
    def context_usage(self) -> float:
        return self._context_size / self._max_context_size

    async def run(self, user_input: str, max_steps: int | None = None):
        context = self._get_context()
        await context.add_message(Message(role="user", content=user_input))

        event_queue = EventQueue()
        vis_task = asyncio.create_task(self._visualization_loop(event_queue))
        try:
            event_queue.put_nowait(RunBegin())
            await self._agent_loop(context, event_queue, max_steps)
        finally:
            event_queue.put_nowait(RunEnd())
            await vis_task  # RunEnd should break the visualization loop

    async def _visualization_loop(self, event_queue: EventQueue):
        # expect a RunBegin
        assert isinstance(await event_queue.get(), RunBegin)
        # expect a StepBegin
        assert isinstance(await event_queue.get(), StepBegin)

        while True:
            # spin the moon at the beginning of each step
            with console.status("", spinner="moon"):
                event = await event_queue.get()

            with StepLiveView(self.context_usage) as step:
                # step visualization loop
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
                # cleanup the step live view before next step
                step.finish()

            # step end or run end
            if isinstance(event, StepBegin):
                # start a new step
                continue
            assert isinstance(event, RunEnd)
            break

    async def _agent_loop(
        self,
        context: LinearContext,
        event_queue: EventQueue,
        max_steps: int | None = None,
    ):
        n_steps = 0
        while True:
            event_queue.put_nowait(StepBegin(n_steps))
            finished = await self._step(context, event_queue)
            n_steps += 1
            if finished:
                return
            if max_steps is not None and n_steps > max_steps:
                # TODO: print some warning
                return

    async def _step(self, context: LinearContext, event_queue: EventQueue) -> bool:
        """Run an single step and return whether the run is finished."""
        # run an LLM step (may be interrupted)
        result = await kosong.step(
            self._chat_provider,
            context,
            on_message_part=event_queue.put_nowait,
            on_tool_result=event_queue.put_nowait,
        )
        if result.usage is not None:
            self._context_size = result.usage.total
            event_queue.put_nowait(ContextUsageUpdate(self.context_usage))

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
