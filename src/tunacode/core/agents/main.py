"""Main agent functionality for the tinyagent event-stream orchestrator."""

from __future__ import annotations

import asyncio
import time
import uuid
from dataclasses import dataclass
from typing import Protocol, cast

from tinyagent.agent import Agent, extract_text
from tinyagent.agent_types import (
    AgentEndEvent,
    AgentEvent,
    AgentMessage,
    AgentTool,
    AssistantMessage,
    CustomAgentMessage,
    MessageEndEvent,
    MessageUpdateEvent,
    TextContent,
    ToolExecutionEndEvent,
    ToolExecutionStartEvent,
    ToolResultMessage,
    TurnEndEvent,
    UserMessage,
    is_agent_end_event,
    is_message_end_event,
    is_tool_execution_end_event,
    is_tool_execution_start_event,
    is_turn_end_event,
)

from tunacode.constants import DEFAULT_CONTEXT_WINDOW
from tunacode.exceptions import (
    AgentError,
    ContextOverflowError,
    GlobalRequestTimeoutError,
    UserAbortError,
)
from tunacode.types import (
    ModelName,
    NoticeCallback,
    StreamingCallback,
    ToolResultCallback,
    ToolStartCallback,
    UsageMetrics,
)
from tunacode.utils.messaging import estimate_messages_tokens

from tunacode.core.compaction.controller import (
    CompactionStatusCallback,
    apply_compaction_messages,
    build_compaction_notice,
    get_or_create_compaction_controller,
)
from tunacode.core.compaction.types import CompactionOutcome
from tunacode.core.debug.usage_trace import log_usage_update
from tunacode.core.logging.manager import LogManager, get_logger
from tunacode.core.types.state import SessionStateProtocol, StateManagerProtocol
from tunacode.core.types.state_structures import RuntimeState

from . import agent_components as ac
from .agent_components.agent_config import _coerce_global_request_timeout
from .helpers import (
    CONTEXT_OVERFLOW_FAILURE_NOTICE,
    CONTEXT_OVERFLOW_RETRY_NOTICE,
    coerce_error_text,
    coerce_tinyagent_history,
    extract_tool_result_text,
    is_context_overflow_error,
    parse_canonical_usage,
)
from .resume import sanitize

REQUEST_ID_LENGTH = 8
MILLISECONDS_PER_SECOND = 1000


@dataclass(slots=True)
class _TinyAgentStreamState:
    runtime: RuntimeState
    tool_start_times: dict[str, float]
    active_tool_call_ids: set[str]
    batch_tool_call_ids: set[str]
    last_assistant_message: AssistantMessage | None = None


class _ModelDumpableMessage(Protocol):
    def model_dump(self, *, exclude_none: bool = False) -> object:
        del exclude_none
        raise NotImplementedError


def _coerce_max_iterations(session: SessionStateProtocol) -> int:
    return int(session.user_config["settings"]["max_iterations"])


def _serialize_agent_messages(messages: list[AgentMessage]) -> list[object]:
    serialized_messages: list[object] = []
    for index, message in enumerate(messages):
        serialized_message = cast(_ModelDumpableMessage, message).model_dump(exclude_none=True)
        if not isinstance(serialized_message, dict):
            raise TypeError(
                "tinyagent message model_dump(exclude_none=True) must return dict; "
                f"got {type(serialized_message).__name__} at index {index}"
            )
        serialized_messages.append(cast(dict[str, object], serialized_message))
    return serialized_messages


def _deserialize_agent_messages(raw_messages: list[object]) -> list[AgentMessage]:
    deserialized_messages: list[AgentMessage] = []
    for index, raw_message in enumerate(raw_messages):
        if not isinstance(raw_message, dict):
            raise TypeError(
                "sanitized message must be a dict, "
                f"got {type(raw_message).__name__} at index {index}"
            )
        typed_raw_message = cast(dict[str, object], raw_message)
        role = typed_raw_message.get("role")
        if role == "user":
            deserialized_messages.append(
                cast(UserMessage, UserMessage.model_validate(typed_raw_message))
            )
            continue
        if role == "assistant":
            deserialized_messages.append(
                cast(AssistantMessage, AssistantMessage.model_validate(typed_raw_message))
            )
            continue
        if role == "tool_result":
            deserialized_messages.append(
                cast(ToolResultMessage, ToolResultMessage.model_validate(typed_raw_message))
            )
            continue
        deserialized_messages.append(
            cast(CustomAgentMessage, CustomAgentMessage.model_validate(typed_raw_message))
        )
    return deserialized_messages


class RequestOrchestrator:
    """Orchestrates the request processing loop using tinyagent events."""

    def __init__(
        self,
        message: str,
        model: ModelName,
        state_manager: StateManagerProtocol,
        streaming_callback: StreamingCallback | None,
        thinking_callback: StreamingCallback | None = None,
        tool_result_callback: ToolResultCallback | None = None,
        tool_start_callback: ToolStartCallback | None = None,
        notice_callback: NoticeCallback | None = None,
        compaction_status_callback: CompactionStatusCallback | None = None,
    ) -> None:
        self.message = message
        self.model = model
        self.state_manager = state_manager
        self.streaming_callback = streaming_callback
        self.thinking_callback = thinking_callback
        self.tool_result_callback = tool_result_callback
        self.tool_start_callback = tool_start_callback
        self.notice_callback = notice_callback
        self.compaction_status_callback = compaction_status_callback
        self.compaction_controller = get_or_create_compaction_controller(state_manager)
        self._active_stream_state: _TinyAgentStreamState | None = None

    async def run(self) -> Agent:
        timeout = _coerce_global_request_timeout(self.state_manager.session)
        if timeout is None:
            return await self._run_impl()
        try:
            return await asyncio.wait_for(self._run_impl(), timeout=timeout)
        except TimeoutError as exc:
            self._invalidate_agent_cache_after_timeout(timeout)
            raise GlobalRequestTimeoutError(timeout) from exc

    def _invalidate_agent_cache_after_timeout(self, timeout: float) -> None:
        _ = timeout
        logger = get_logger()
        if ac.invalidate_agent_cache(self.model, self.state_manager):
            logger.lifecycle("Agent cache invalidated after timeout")

    async def _run_impl(self) -> Agent:
        request_context = self._initialize_request()
        logger = get_logger()
        logger.info("Request started", request_id=request_context.request_id)

        session = self.state_manager.session
        conversation = session.conversation
        agent = ac.get_or_create_agent(self.model, self.state_manager)
        history = coerce_tinyagent_history(conversation.messages)
        self.compaction_controller.set_status_callback(self.compaction_status_callback)
        compacted_history = await self._compact_history_for_request(history)
        baseline_message_count = len(conversation.messages)
        pre_request_history = list(conversation.messages)
        agent.replace_messages(compacted_history)
        session._debug_raw_stream_accum = ""

        try:
            await self._run_stream(
                agent=agent,
                request_context=request_context,
                baseline_message_count=baseline_message_count,
            )
            await self._retry_after_context_overflow_if_needed(
                agent=agent,
                request_context=request_context,
                pre_request_history=pre_request_history,
            )
            return agent
        except (UserAbortError, asyncio.CancelledError):
            self._handle_abort_cleanup(
                logger,
                agent=agent,
                baseline_message_count=baseline_message_count,
                invalidate_cache=False,
            )
            raise

    def _initialize_request(self) -> RequestContext:
        request_id = str(uuid.uuid4())[:REQUEST_ID_LENGTH]
        session = self.state_manager.session
        runtime = session.runtime
        runtime.request_id = request_id
        runtime.current_iteration = 0
        runtime.iteration_count = 0
        runtime.tool_registry.clear()
        runtime.batch_counter = 0
        session.usage.last_call_usage = UsageMetrics()
        if not session.task.original_query:
            session.task.original_query = self.message
        return RequestContext(
            request_id=request_id,
            max_iterations=_coerce_max_iterations(session),
            debug_metrics=False,
        )

    def _maybe_emit_compaction_notice(self, outcome: CompactionOutcome) -> None:
        if self.notice_callback is None:
            return
        notice = build_compaction_notice(outcome)
        if notice is not None:
            self.notice_callback(notice)

    async def _compact_history_for_request(self, history: list[AgentMessage]) -> list[AgentMessage]:
        self.compaction_controller.reset_request_state()
        outcome = await self.compaction_controller.check_and_compact(
            history,
            max_tokens=self.state_manager.session.conversation.max_tokens,
            signal=None,
            allow_threshold=True,
        )
        self._maybe_emit_compaction_notice(outcome)
        return apply_compaction_messages(self.state_manager, outcome.messages)

    async def _force_compact_history(self, history: list[AgentMessage]) -> list[AgentMessage]:
        outcome = await self.compaction_controller.force_compact(
            history,
            max_tokens=self.state_manager.session.conversation.max_tokens,
            signal=None,
        )
        self._maybe_emit_compaction_notice(outcome)
        return apply_compaction_messages(self.state_manager, outcome.messages)

    async def _retry_after_context_overflow_if_needed(
        self,
        *,
        agent: Agent,
        request_context: RequestContext,
        pre_request_history: list[AgentMessage],
    ) -> None:
        error_text = self._agent_error_text(agent)
        if not is_context_overflow_error(error_text):
            return

        logger = get_logger()
        logger.warning("Context overflow detected; forcing compaction and retrying")
        if self.notice_callback is not None:
            self.notice_callback(CONTEXT_OVERFLOW_RETRY_NOTICE)

        conversation = self.state_manager.session.conversation
        apply_compaction_messages(self.state_manager, pre_request_history)
        forced_history = await self._force_compact_history(pre_request_history)
        agent.replace_messages(forced_history)
        self.state_manager.session._debug_raw_stream_accum = ""
        await self._run_stream(
            agent=agent,
            request_context=request_context,
            baseline_message_count=len(conversation.messages),
        )

        retry_error_text = self._agent_error_text(agent)
        if not is_context_overflow_error(retry_error_text):
            return

        if self.notice_callback is not None:
            self.notice_callback(CONTEXT_OVERFLOW_FAILURE_NOTICE)
        raise ContextOverflowError(
            estimated_tokens=estimate_messages_tokens(conversation.messages),
            max_tokens=conversation.max_tokens or DEFAULT_CONTEXT_WINDOW,
            model=self.model,
        )

    def _agent_error_text(self, agent: Agent) -> str:
        return coerce_error_text(agent.state.error)

    def _mark_tool_start_batch_state(
        self, state: _TinyAgentStreamState, *, tool_call_id: str
    ) -> None:
        if state.active_tool_call_ids:
            state.batch_tool_call_ids.update(state.active_tool_call_ids)
            state.batch_tool_call_ids.add(tool_call_id)
        state.active_tool_call_ids.add(tool_call_id)

    def _clear_tool_batch_state_if_idle(self, state: _TinyAgentStreamState) -> None:
        if not state.active_tool_call_ids:
            state.batch_tool_call_ids.clear()

    def _resolve_tool_duration_ms(
        self,
        state: _TinyAgentStreamState,
        *,
        tool_call_id: str,
    ) -> float | None:
        start_time = state.tool_start_times.pop(tool_call_id, None)
        if start_time is None or tool_call_id in state.batch_tool_call_ids:
            return None
        return (time.perf_counter() - start_time) * MILLISECONDS_PER_SECOND

    def _persist_agent_messages(self, agent: Agent, baseline_message_count: int) -> None:
        conversation = self.state_manager.session.conversation
        external_messages = list(conversation.messages[baseline_message_count:])
        conversation.messages = [*list(agent.state.messages), *external_messages]

    def _remove_in_flight_tool_registry_entries(self, logger: LogManager) -> None:
        active_stream_state = self._active_stream_state
        if active_stream_state is None:
            return

        unresolved_tool_call_ids = set(active_stream_state.active_tool_call_ids)
        if not unresolved_tool_call_ids:
            return

        removed_count = self.state_manager.session.runtime.tool_registry.remove_many(
            unresolved_tool_call_ids
        )
        if removed_count > 0:
            logger.lifecycle(f"Removed {removed_count} in-flight tool call(s) after abort")

    def _sanitize_conversation_after_abort(self, logger: LogManager) -> None:
        session = self.state_manager.session
        serialized_messages = _serialize_agent_messages(session.conversation.messages)
        cleanup_applied, dangling_tool_call_ids = sanitize.run_cleanup_loop(
            serialized_messages,
            session.runtime.tool_registry,
        )
        if cleanup_applied:
            session.conversation.messages = _deserialize_agent_messages(serialized_messages)
        if cleanup_applied and dangling_tool_call_ids:
            logger.lifecycle(
                f"Cleaned up {len(dangling_tool_call_ids)} dangling tool call(s) after abort"
            )

    def _append_interrupted_partial_message(self) -> None:
        session = self.state_manager.session
        partial_text = session._debug_raw_stream_accum
        if not partial_text.strip():
            return

        latest_assistant_text = ""
        for message in reversed(session.conversation.messages):
            if isinstance(message, AssistantMessage):
                latest_assistant_text = extract_text(message)
                break
        if latest_assistant_text.strip() == partial_text.strip():
            return

        session.conversation.messages.append(
            AssistantMessage(
                content=[TextContent(text=f"[INTERRUPTED]\n\n{partial_text}")],
                stop_reason="aborted",
                timestamp=int(time.time() * MILLISECONDS_PER_SECOND),
            )
        )

    async def _handle_stream_turn_end(
        self,
        event_obj: TurnEndEvent,
        *,
        agent: Agent,
        state: _TinyAgentStreamState,
        request_context: RequestContext,
        baseline_message_count: int,
    ) -> bool:
        _ = (event_obj, baseline_message_count)
        state.runtime.iteration_count += 1
        state.runtime.current_iteration = state.runtime.iteration_count
        if state.runtime.iteration_count <= request_context.max_iterations:
            return False
        agent.abort()
        raise RuntimeError(f"Max iterations exceeded ({request_context.max_iterations}); aborted")

    async def _handle_stream_message_update(
        self,
        event_obj: MessageUpdateEvent,
        *,
        agent: Agent,
        state: _TinyAgentStreamState,
        request_context: RequestContext,
        baseline_message_count: int,
    ) -> bool:
        _ = (agent, state, request_context, baseline_message_count)
        await self._handle_message_update(event_obj)
        return False

    async def _handle_stream_message_end(
        self,
        event_obj: MessageEndEvent,
        *,
        agent: Agent,
        state: _TinyAgentStreamState,
        request_context: RequestContext,
        baseline_message_count: int,
    ) -> bool:
        _ = (agent, baseline_message_count)
        if not isinstance(event_obj.message, AssistantMessage):
            return False
        state.last_assistant_message = event_obj.message
        usage = parse_canonical_usage(event_obj.message.usage)
        session = self.state_manager.session
        session.usage.last_call_usage = usage
        session.usage.session_total_usage.add(usage)
        log_usage_update(
            logger=get_logger(),
            request_id=request_context.request_id,
            event_name="message_end",
            last_call_usage=session.usage.last_call_usage,
            session_total_usage=session.usage.session_total_usage,
        )
        return False

    async def _handle_stream_tool_execution_start(
        self,
        event_obj: ToolExecutionStartEvent,
        *,
        agent: Agent,
        state: _TinyAgentStreamState,
        request_context: RequestContext,
        baseline_message_count: int,
    ) -> bool:
        _ = (agent, request_context, baseline_message_count)
        tool_call_id = event_obj.tool_call_id
        tool_name = event_obj.tool_name
        args = normalize_tool_event_args(
            event_obj.args,
            event_name="tool_execution_start",
            tool_call_id=tool_call_id,
        )
        state.tool_start_times[tool_call_id] = time.perf_counter()
        self._mark_tool_start_batch_state(state, tool_call_id=tool_call_id)
        state.runtime.tool_registry.register(
            tool_call_id,
            tool_name,
            cast(dict[str, object], args),
        )
        state.runtime.tool_registry.start(tool_call_id)
        log_tool_execution_start(
            get_logger(),
            state=state,
            tool_call_id=tool_call_id,
            tool_name=tool_name,
        )
        if self.tool_start_callback is not None:
            self.tool_start_callback(tool_name)
        return False

    async def _handle_stream_tool_execution_end(
        self,
        event_obj: ToolExecutionEndEvent,
        *,
        agent: Agent,
        state: _TinyAgentStreamState,
        request_context: RequestContext,
        baseline_message_count: int,
    ) -> bool:
        _ = (agent, request_context, baseline_message_count)
        tool_call_id = event_obj.tool_call_id
        tool_name = event_obj.tool_name
        duration_ms = self._resolve_tool_duration_ms(state, tool_call_id=tool_call_id)
        result_text = extract_tool_result_text(event_obj.result)
        status = "failed" if event_obj.is_error else "completed"
        was_parallel_batch_member = tool_call_id in state.batch_tool_call_ids

        if event_obj.is_error:
            state.runtime.tool_registry.fail(tool_call_id, error=result_text)
        else:
            state.runtime.tool_registry.complete(tool_call_id, result=result_text)

        state.active_tool_call_ids.discard(tool_call_id)
        self._clear_tool_batch_state_if_idle(state)
        log_tool_execution_end(
            get_logger(),
            state=state,
            tool_call_id=tool_call_id,
            tool_name=tool_name,
            status=status,
            duration_ms=duration_ms,
            was_parallel_batch_member=was_parallel_batch_member,
        )

        if self.tool_result_callback is None:
            return False

        callback_args = state.runtime.tool_registry.get_args(tool_call_id)
        self.tool_result_callback(
            tool_name,
            status,
            coerce_tool_callback_args(callback_args),
            result_text,
            duration_ms,
        )
        return False

    async def _handle_stream_agent_end(
        self,
        event_obj: AgentEndEvent,
        *,
        agent: Agent,
        state: _TinyAgentStreamState,
        request_context: RequestContext,
        baseline_message_count: int,
    ) -> bool:
        _ = (event_obj, state, request_context)
        self._persist_agent_messages(agent, baseline_message_count)
        return True

    async def _dispatch_stream_event(
        self,
        *,
        event: AgentEvent,
        agent: Agent,
        state: _TinyAgentStreamState,
        request_context: RequestContext,
        baseline_message_count: int,
    ) -> bool:
        if is_turn_end_event(event):
            return await self._handle_stream_turn_end(
                event,
                agent=agent,
                state=state,
                request_context=request_context,
                baseline_message_count=baseline_message_count,
            )
        if isinstance(event, MessageUpdateEvent):
            return await self._handle_stream_message_update(
                event,
                agent=agent,
                state=state,
                request_context=request_context,
                baseline_message_count=baseline_message_count,
            )
        if is_message_end_event(event):
            return await self._handle_stream_message_end(
                event,
                agent=agent,
                state=state,
                request_context=request_context,
                baseline_message_count=baseline_message_count,
            )
        if is_tool_execution_start_event(event):
            return await self._handle_stream_tool_execution_start(
                event,
                agent=agent,
                state=state,
                request_context=request_context,
                baseline_message_count=baseline_message_count,
            )
        if is_tool_execution_end_event(event):
            return await self._handle_stream_tool_execution_end(
                event,
                agent=agent,
                state=state,
                request_context=request_context,
                baseline_message_count=baseline_message_count,
            )
        if is_agent_end_event(event):
            return await self._handle_stream_agent_end(
                event,
                agent=agent,
                state=state,
                request_context=request_context,
                baseline_message_count=baseline_message_count,
            )
        return False

    async def _run_stream(
        self,
        *,
        agent: Agent,
        request_context: RequestContext,
        baseline_message_count: int,
    ) -> Agent:
        logger = get_logger()
        runtime = self.state_manager.session.runtime
        state = _TinyAgentStreamState(
            runtime=runtime,
            tool_start_times={},
            active_tool_call_ids=set(),
            batch_tool_call_ids=set(),
        )
        self._active_stream_state = state
        started_at = time.perf_counter()
        try:
            async for event in agent.stream(self.message):
                should_stop = await self._dispatch_stream_event(
                    event=event,
                    agent=agent,
                    state=state,
                    request_context=request_context,
                    baseline_message_count=baseline_message_count,
                )
                if should_stop:
                    break
        finally:
            self._active_stream_state = None

        elapsed_ms = (time.perf_counter() - started_at) * MILLISECONDS_PER_SECOND
        logger.lifecycle(f"Request complete ({elapsed_ms:.0f}ms)")

        error_text = self._agent_error_text(agent)
        if error_text and not is_context_overflow_error(error_text):
            raise AgentError(error_text)

        return agent

    async def _handle_message_update(self, event: MessageUpdateEvent) -> None:
        assistant_event = event.assistant_message_event
        if (
            assistant_event is None
            or not isinstance(assistant_event.delta, str)
            or not assistant_event.delta
        ):
            return

        if assistant_event.type == "text_delta":
            self.state_manager.session._debug_raw_stream_accum += assistant_event.delta
            if self.streaming_callback is not None:
                await self.streaming_callback(assistant_event.delta)
            return

        if assistant_event.type == "thinking_delta" and self.thinking_callback is not None:
            await self.thinking_callback(assistant_event.delta)

    def _handle_abort_cleanup(
        self,
        logger: LogManager,
        *,
        agent: Agent | None = None,
        baseline_message_count: int | None = None,
        invalidate_cache: bool = False,
    ) -> None:
        if agent is not None and baseline_message_count is not None:
            self._persist_agent_messages(agent, baseline_message_count)

        self._remove_in_flight_tool_registry_entries(logger)
        self._sanitize_conversation_after_abort(logger)
        self._append_interrupted_partial_message()
        if invalidate_cache and ac.invalidate_agent_cache(self.model, self.state_manager):
            logger.lifecycle("Agent cache invalidated after abort")


def get_agent_tool() -> tuple[type[Agent], type[object]]:
    """Return the (Agent, AgentTool) classes."""
    return Agent, cast(type[object], AgentTool)


async def process_request(
    message: str,
    model: ModelName,
    state_manager: StateManagerProtocol,
    streaming_callback: StreamingCallback | None = None,
    thinking_callback: StreamingCallback | None = None,
    tool_result_callback: ToolResultCallback | None = None,
    tool_start_callback: ToolStartCallback | None = None,
    notice_callback: NoticeCallback | None = None,
    compaction_status_callback: CompactionStatusCallback | None = None,
) -> Agent:
    orchestrator = RequestOrchestrator(
        message,
        model,
        state_manager,
        streaming_callback,
        thinking_callback,
        tool_result_callback,
        tool_start_callback,
        notice_callback,
        compaction_status_callback,
    )
    return await orchestrator.run()
