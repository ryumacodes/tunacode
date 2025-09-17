import asyncio
from collections.abc import Callable, Coroutine

import kosong
from kosong import StepResult
from kosong.base.chat_provider import ChatProvider
from kosong.base.message import Message
from kosong.tooling import ToolResult

from kimi_cli.agent import Agent
from kimi_cli.constant import MAX_CONTEXT_SIZE, MAX_STEPS
from kimi_cli.context import Context
from kimi_cli.event import (
    ContextUsageUpdate,
    EventQueue,
    RunBegin,
    RunEnd,
    StepBegin,
    StepCancelled,
)
from kimi_cli.utils.message import tool_result_to_messages

type VisualizeFn = Callable[[EventQueue], Coroutine[None, None, None]]
"""
An async function that consumes events from the event queue and visualizes the agent behavior.
The function should never raise any exception.
"""


class Soul:
    """The soul of Kimi CLI."""

    def __init__(
        self,
        agent: Agent,
        *,
        chat_provider: ChatProvider,
        context: Context,
    ):
        self._agent = agent
        self._chat_provider = chat_provider
        self._context = context
        self._max_context_size: int = MAX_CONTEXT_SIZE  # unit: tokens

    @property
    def name(self) -> str:
        return self._agent.name

    @property
    def model(self) -> str:
        return self._chat_provider.model_name

    @property
    def context_usage(self) -> float:
        return self._context.token_count / self._max_context_size

    async def run(self, user_input: str, visualize: VisualizeFn):
        await self._context.append_message(Message(role="user", content=user_input))

        event_queue = EventQueue()
        vis_task = asyncio.create_task(visualize(event_queue))
        try:
            event_queue.put_nowait(RunBegin())
            await self._agent_loop(event_queue)
        except asyncio.CancelledError:
            # the run is cancelled, propagate the cancellation
            # TODO: maybe need to manipulate the context to add some notes
            raise
        finally:
            event_queue.put_nowait(RunEnd())
            await vis_task  # RunEnd should break the visualization loop

    async def _agent_loop(
        self,
        event_queue: EventQueue,
    ):
        """The main agent loop for one run."""
        n_steps = 0
        while True:
            event_queue.put_nowait(StepBegin(n_steps))
            try:
                finished = await self._step(event_queue)
            except asyncio.CancelledError:
                event_queue.put_nowait(StepCancelled())
                # break the agent loop
                raise
            n_steps += 1
            if finished:
                return
            if n_steps > MAX_STEPS:
                # TODO: print some warning
                return

    async def _step(self, event_queue: EventQueue) -> bool:
        """Run an single step and return whether the run is finished."""
        # run an LLM step (may be interrupted)
        result = await kosong.step(
            self._chat_provider,
            self._agent.system_prompt,
            self._agent.toolset,
            self._context.history,
            on_message_part=event_queue.put_nowait,
            on_tool_result=event_queue.put_nowait,
        )
        if result.usage is not None:
            # mark the token count for the context before the step
            await self._context.update_token_count(result.usage.input)
            event_queue.put_nowait(ContextUsageUpdate(self.context_usage))

        # wait for all tool results (may be interrupted)
        results = await result.tool_results()
        # shield the context manipulation from interruption
        await asyncio.shield(self._grow_context(result, results))

        return not result.tool_calls

    async def _grow_context(self, result: StepResult, tool_results: list[ToolResult]):
        await self._context.append_message(result.message)
        if result.usage is not None:
            await self._context.update_token_count(result.usage.total)

        # token count of tool results are not available yet
        for tool_result in tool_results:
            await self._context.append_message(tool_result_to_messages(tool_result))
