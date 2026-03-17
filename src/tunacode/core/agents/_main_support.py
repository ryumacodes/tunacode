"""Private support helpers for the main tinyagent orchestrator."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from tunacode.types import NoticeCallback

from tunacode.core.logging.manager import LogManager, get_logger
from tunacode.core.types.state import StateManagerProtocol

from . import agent_components as ac

TOOL_EXECUTION_LIFECYCLE_PREFIX = "Tool execution"
PARALLEL_TOOL_CALLS_LIFECYCLE_PREFIX = "Parallel tool calls"
DURATION_NOT_AVAILABLE_LABEL = "n/a"


class StreamLifecycleState(Protocol):
    active_tool_call_ids: set[str]
    batch_tool_call_ids: set[str]


@dataclass(slots=True)
class _EmptyResponseStateView:
    sm: StateManagerProtocol
    show_thoughts: bool


def normalize_tool_event_args(
    raw_args: object,
    *,
    event_name: str,
    tool_call_id: str,
) -> dict[str, object]:
    if raw_args is None:
        return {}
    if not isinstance(raw_args, dict):
        raise TypeError(
            f"{event_name} args must be an object for tool_call_id='{tool_call_id}', "
            f"got {type(raw_args).__name__}"
        )
    if not all(isinstance(key, str) for key in raw_args):
        raise TypeError(f"{event_name} args keys must be strings")
    return {key: value for key, value in raw_args.items() if isinstance(key, str)}


def coerce_tool_callback_args(raw_args: object) -> dict[str, object]:
    if raw_args is None:
        return {}
    if not isinstance(raw_args, dict):
        raise TypeError(f"tool callback args must be a dict, got {type(raw_args).__name__}")
    if not all(isinstance(key, str) for key in raw_args):
        raise TypeError("tool callback args keys must be strings")
    return {key: value for key, value in raw_args.items() if isinstance(key, str)}


def _format_duration_ms(duration_ms: float | None) -> str:
    if duration_ms is None:
        return DURATION_NOT_AVAILABLE_LABEL
    return f"{duration_ms:.1f}"


def log_tool_execution_start(
    logger: LogManager,
    *,
    state: StreamLifecycleState,
    tool_call_id: str,
    tool_name: str,
) -> None:
    in_flight = len(state.active_tool_call_ids)
    logger.lifecycle(
        f"{TOOL_EXECUTION_LIFECYCLE_PREFIX} start: "
        f"name={tool_name} tool_call_id={tool_call_id} in_flight={in_flight}"
    )
    if in_flight > 1:
        logger.lifecycle(
            f"{PARALLEL_TOOL_CALLS_LIFECYCLE_PREFIX} active: "
            f"in_flight={in_flight} batch_size={len(state.batch_tool_call_ids)}"
        )


def log_tool_execution_end(
    logger: LogManager,
    *,
    state: StreamLifecycleState,
    tool_call_id: str,
    tool_name: str,
    status: str,
    duration_ms: float | None,
    was_parallel_batch_member: bool,
) -> None:
    in_flight = len(state.active_tool_call_ids)
    logger.lifecycle(
        f"{TOOL_EXECUTION_LIFECYCLE_PREFIX} end: "
        f"name={tool_name} tool_call_id={tool_call_id} status={status} "
        f"in_flight={in_flight} duration_ms={_format_duration_ms(duration_ms)}"
    )
    if not was_parallel_batch_member:
        return
    logger.lifecycle(
        f"{PARALLEL_TOOL_CALLS_LIFECYCLE_PREFIX} update: "
        f"in_flight={in_flight} batch_size={len(state.batch_tool_call_ids)}"
    )
    if in_flight == 0:
        logger.lifecycle(f"{PARALLEL_TOOL_CALLS_LIFECYCLE_PREFIX} complete")


class EmptyResponseHandler:
    """Handles tracking and intervention for empty responses."""

    def __init__(
        self,
        state_manager: StateManagerProtocol,
        notice_callback: NoticeCallback | None,
    ) -> None:
        self.state_manager = state_manager
        self.notice_callback = notice_callback

    def track(self, is_empty: bool) -> None:
        runtime = self.state_manager.session.runtime
        runtime.consecutive_empty_responses = (
            runtime.consecutive_empty_responses + 1 if is_empty else 0
        )

    def should_intervene(self) -> bool:
        return self.state_manager.session.runtime.consecutive_empty_responses >= 1

    async def prompt_action(self, message: str, reason: str, iteration: int) -> None:
        logger = get_logger()
        logger.warning(f"Empty response: {reason}", iteration=iteration)
        notice = await ac.handle_empty_response(
            message,
            reason,
            iteration,
            _EmptyResponseStateView(
                sm=self.state_manager,
                show_thoughts=self.state_manager.session.show_thoughts,
            ),
        )
        if self.notice_callback is not None:
            self.notice_callback(notice)
        self.state_manager.session.runtime.consecutive_empty_responses = 0
