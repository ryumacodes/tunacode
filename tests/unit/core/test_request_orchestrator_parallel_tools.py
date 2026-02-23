"""RequestOrchestrator tool lifecycle tests for parallel tinyagent batches."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from tunacode.types.canonical import ToolCallStatus

from tunacode.core.agents import main as agent_main
from tunacode.core.agents.main import RequestContext, RequestOrchestrator, _TinyAgentStreamState
from tunacode.core.session import StateManager


def _build_orchestrator_harness(
    *,
    start_events: list[str] | None = None,
    result_events: list[tuple[str, str, dict[str, object], str | None, float | None]] | None = None,
) -> tuple[RequestOrchestrator, _TinyAgentStreamState, RequestContext, StateManager]:
    state_manager = StateManager()

    def _on_tool_start(tool_name: str) -> None:
        if start_events is not None:
            start_events.append(tool_name)

    def _on_tool_result(
        tool_name: str,
        status: str,
        args: dict[str, object],
        result: str | None,
        duration_ms: float | None,
    ) -> None:
        if result_events is not None:
            result_events.append((tool_name, status, args, result, duration_ms))

    orchestrator = RequestOrchestrator(
        message="test",
        model="openai/gpt-4o",
        state_manager=state_manager,
        tool_callback=None,
        streaming_callback=None,
        tool_result_callback=_on_tool_result if result_events is not None else None,
        tool_start_callback=_on_tool_start if start_events is not None else None,
    )
    state = _TinyAgentStreamState(
        runtime=state_manager.session.runtime,
        tool_start_times={},
        active_tool_call_ids=set(),
        batch_tool_call_ids=set(),
    )
    request_context = RequestContext(request_id="req-1", max_iterations=10, debug_metrics=False)
    return orchestrator, state, request_context, state_manager


@pytest.mark.asyncio
async def test_tool_handlers_preserve_registry_and_callbacks_for_parallel_batch() -> None:
    start_events: list[str] = []
    result_events: list[tuple[str, str, dict[str, object], str | None, float | None]] = []
    orchestrator, state, request_context, state_manager = _build_orchestrator_harness(
        start_events=start_events,
        result_events=result_events,
    )

    await orchestrator._handle_stream_tool_execution_start(
        SimpleNamespace(tool_call_id="tool-a", tool_name="read_file", args={"filepath": "a.py"}),
        agent=object(),
        state=state,
        request_context=request_context,
        baseline_message_count=0,
    )
    await orchestrator._handle_stream_tool_execution_start(
        SimpleNamespace(
            tool_call_id="tool-b",
            tool_name="grep",
            args='{"pattern": "TODO"}',
        ),
        agent=object(),
        state=state,
        request_context=request_context,
        baseline_message_count=0,
    )

    assert start_events == ["read_file", "grep"]
    assert state_manager.session.runtime.tool_registry.get_args("tool-a") == {"filepath": "a.py"}
    assert state_manager.session.runtime.tool_registry.get_args("tool-b") == {"pattern": "TODO"}

    await orchestrator._handle_stream_tool_execution_end(
        SimpleNamespace(
            tool_call_id="tool-a",
            tool_name="read_file",
            is_error=False,
            result={"content": [{"type": "text", "text": "read complete"}]},
        ),
        agent=object(),
        state=state,
        request_context=request_context,
        baseline_message_count=0,
    )
    await orchestrator._handle_stream_tool_execution_end(
        SimpleNamespace(
            tool_call_id="tool-b",
            tool_name="grep",
            is_error=False,
            result={"content": [{"type": "text", "text": "found"}]},
        ),
        agent=object(),
        state=state,
        request_context=request_context,
        baseline_message_count=0,
    )

    assert [(name, status) for name, status, *_ in result_events] == [
        ("read_file", "completed"),
        ("grep", "completed"),
    ]
    assert all(duration_ms is None for *_, duration_ms in result_events)

    registry = state_manager.session.runtime.tool_registry
    tool_a = registry.get("tool-a")
    tool_b = registry.get("tool-b")
    assert tool_a is not None
    assert tool_b is not None
    assert tool_a.status is ToolCallStatus.COMPLETED
    assert tool_b.status is ToolCallStatus.COMPLETED


@pytest.mark.asyncio
async def test_tool_start_rejects_malformed_args_payload() -> None:
    start_events: list[str] = []
    orchestrator, state, request_context, state_manager = _build_orchestrator_harness(
        start_events=start_events,
        result_events=[],
    )

    with pytest.raises(TypeError, match="tool_execution_start args must be a dict or JSON string"):
        await orchestrator._handle_stream_tool_execution_start(
            SimpleNamespace(tool_call_id="tool-a", tool_name="read_file", args=["bad"]),
            agent=object(),
            state=state,
            request_context=request_context,
            baseline_message_count=0,
        )

    assert start_events == []
    assert state_manager.session.runtime.tool_registry.get("tool-a") is None


@pytest.mark.asyncio
async def test_single_tool_duration_is_reported_when_not_in_parallel_batch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    result_events: list[tuple[str, str, dict[str, object], str | None, float | None]] = []
    orchestrator, state, request_context, _state_manager = _build_orchestrator_harness(
        start_events=[],
        result_events=result_events,
    )

    perf_counter_values = iter([100.0, 100.5])
    monkeypatch.setattr(agent_main.time, "perf_counter", lambda: next(perf_counter_values))

    await orchestrator._handle_stream_tool_execution_start(
        SimpleNamespace(tool_call_id="tool-a", tool_name="read_file", args={"filepath": "a.py"}),
        agent=object(),
        state=state,
        request_context=request_context,
        baseline_message_count=0,
    )
    await orchestrator._handle_stream_tool_execution_end(
        SimpleNamespace(
            tool_call_id="tool-a",
            tool_name="read_file",
            is_error=False,
            result={"content": [{"type": "text", "text": "done"}]},
        ),
        agent=object(),
        state=state,
        request_context=request_context,
        baseline_message_count=0,
    )

    assert len(result_events) == 1
    assert result_events[0][0] == "read_file"
    assert result_events[0][1] == "completed"
    assert result_events[0][4] == pytest.approx(500.0)
