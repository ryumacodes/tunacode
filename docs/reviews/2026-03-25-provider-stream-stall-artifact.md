---
title: Provider Stream Stall Research Artifact
summary: Research notes about the remaining stream stall that occurs before provider events arrive.
when_to_read:
  - When investigating provider stream stalls
  - When reviewing the stream-stall research artifact
last_updated: "2026-04-04"
---

# Provider Stream Stall Research Artifact

Date: 2026-03-25
Repo: `tunacode`
Type: Research artifact
Status: Awaiting tinyagent feedback
Conclusion: The remaining stall is below TunaCode UI/request init and occurs before the first raw provider event is yielded

## Research Question

Why does the TunaCode input panel still become sluggish for about 1s during an active request even after request execution was moved off the main Textual UI loop into a real thread worker?

## Current Conclusion

The stall is not in the editor widget, loading indicator, queue handoff, request init, or TunaCode bridge flush path.

The strongest evidence points at the tinyagent alchemy provider stream boundary:

- provider stream open returns quickly
- the first raw provider event arrives about 1.1s later
- TunaCode sees the first parsed stream event at the same time
- UI timer drift lines up with that same dead zone

That means the remaining lag happens before TunaCode receives the first stream event, inside or below the provider stream implementation.

## What Was Ruled Out

The following were instrumented and are not the primary cause:

- submit to enqueue timing
- queue to request start timing
- request init and agent construction
- loading indicator show/hide work
- bridge backlog flush cost
- thinking/text callback cost on the TunaCode side

Representative warm-request numbers:

- `submit_to_start=9.4ms`
- `Init: pre_stream total=18.3ms`
- `Stream: provider_open attempt=1/10 dur=0.6ms`
- `UI: delta_timer_drift seq=2 drift=1077.6ms`
- `Stream: first_event type=AgentStartEvent since_start=1156.4ms`
- `Stream: provider_first_raw type=start since_open=1161.3ms since_response=1160.7ms`
- `Bridge: ... flush=0.6ms ... thinking_cb=0.5ms`

## Exact TunaCode Stream Consumer

Source: [src/tunacode/core/agents/main.py](/home/fabian/tunacode/src/tunacode/core/agents/main.py)

```python
    async def _run_stream(
        self,
        *,
        agent: Agent,
        max_iterations: int,
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
        stream_thread_id = threading.get_ident()
        event_count = 0
        first_event_ms: float | None = None
        last_event_at = started_at
        logger.lifecycle(f"Stream: start thread={stream_thread_id}")
        try:
            async for event in agent.stream(self.message):
                now = time.perf_counter()
                event_count += 1
                event_name = _describe_stream_event(event)
                if first_event_ms is None:
                    first_event_ms = (now - started_at) * MILLISECONDS_PER_SECOND
                    logger.lifecycle(
                        "Stream: "
                        f"first_event type={event_name} "
                        f"since_start={first_event_ms:.1f}ms "
                        f"thread={stream_thread_id}"
                    )
                else:
                    gap_ms = (now - last_event_at) * MILLISECONDS_PER_SECOND
                    if gap_ms >= STREAM_EVENT_GAP_WARN_MS:
                        logger.lifecycle(
                            "Stream: "
                            f"event_gap type={event_name} "
                            f"gap={gap_ms:.1f}ms "
                            f"count={event_count}"
                        )
                last_event_at = now
                should_stop = await self._dispatch_stream_event(
                    event=event,
                    agent=agent,
                    state=state,
                    max_iterations=max_iterations,
                    baseline_message_count=baseline_message_count,
                )
                if should_stop:
                    break
        finally:
            self._active_stream_state = None

        elapsed_ms = (time.perf_counter() - started_at) * MILLISECONDS_PER_SECOND
        if first_event_ms is None:
            end_message = f"Stream: end events={event_count} first_event=none"
        else:
            end_message = (
                "Stream: "
                f"end events={event_count} "
                f"first_event={first_event_ms:.1f}ms"
            )
        logger.lifecycle(end_message)
        logger.lifecycle(f"Request complete ({elapsed_ms:.0f}ms)")
```

## Exact TunaCode Provider Boundary

Source: [src/tunacode/core/agents/agent_components/agent_config.py](/home/fabian/tunacode/src/tunacode/core/agents/agent_components/agent_config.py)

```python
class _TracedStreamResponse:
    """Wrap provider StreamResponse with timing logs for /debug sessions."""

    def __init__(
        self,
        response: StreamResponse,
        *,
        logger: _LifecycleTraceLogger,
        opened_at: float,
        response_ready_at: float,
    ) -> None:
        self._response = response
        self._logger = logger
        self._opened_at = opened_at
        self._response_ready_at = response_ready_at
        self._event_count = 0
        self._last_event_at = response_ready_at

    def __aiter__(self) -> _TracedStreamResponse:
        return self

    async def __anext__(self) -> AssistantMessageEvent:
        event = await self._response.__anext__()
        now = time.perf_counter()
        self._event_count += 1
        event_type = event.type or "unknown"

        if self._event_count == 1:
            self._logger.lifecycle(
                "Stream: "
                f"provider_first_raw type={event_type} "
                f"since_open={(now - self._opened_at) * 1000.0:.1f}ms "
                f"since_response={(now - self._response_ready_at) * 1000.0:.1f}ms"
            )
        else:
            gap_ms = (now - self._last_event_at) * 1000.0
            if gap_ms >= STREAM_RAW_EVENT_GAP_WARN_MS:
                self._logger.lifecycle(
                    "Stream: "
                    f"provider_raw_gap type={event_type} "
                    f"gap={gap_ms:.1f}ms "
                    f"count={self._event_count}"
                )

        self._last_event_at = now
        return event

    async def result(self) -> AssistantMessage:
        started_at = time.perf_counter()
        result = await self._response.result()
        duration_ms = (time.perf_counter() - started_at) * 1000.0
        self._logger.lifecycle(f"Stream: provider_result dur={duration_ms:.1f}ms")
        return result
```

```python
def _build_stream_fn(
    *,
    request_delay: float,
    max_tokens: int | None,
    max_retries: int = 1,
) -> StreamFn:
    async def _stream(
        model: Model,
        context: Context,
        options: SimpleStreamOptions,
    ) -> StreamResponse:
        stream_options = _merge_stream_options(options=options, max_tokens=max_tokens)
        logger = get_logger()

        for attempt in range(1, max_retries + 1):
            if request_delay > 0:
                await _sleep_with_delay(request_delay)
            try:
                opened_at = time.perf_counter()
                response = await stream_alchemy_openai_completions(model, context, stream_options)
                response_ready_at = time.perf_counter()
                logger.lifecycle(
                    "Stream: "
                    f"provider_open attempt={attempt}/{max_retries} "
                    f"dur={(response_ready_at - opened_at) * 1000.0:.1f}ms"
                )
                if logger.debug_mode:
                    return _TracedStreamResponse(
                        response,
                        logger=logger,
                        opened_at=opened_at,
                        response_ready_at=response_ready_at,
                    )
                return response
            except Exception as exc:  # noqa: BLE001
                if attempt >= max_retries or not _is_retryable_stream_error(exc):
                    raise
                logger.warning(
                    "Retrying provider stream request after transient error: "
                    f"attempt={attempt}/{max_retries}, error={type(exc).__name__}"
                )
                await _sleep_with_delay(_compute_stream_retry_delay(attempt))

        raise RuntimeError("Unreachable stream retry exhaustion")

    return _stream
```

## Exact tinyagent Code Path

Source: `/home/fabian/tunacode/.venv/lib/python3.13/site-packages/tinyagent/alchemy_provider.py`

```python
@dataclass
class AlchemyStreamResponse:
    """StreamResponse backed by a Rust stream handle."""

    _handle: _AlchemyStreamHandle
    _final_message: AssistantMessage | None = None

    async def result(self) -> AssistantMessage:
        if self._final_message is not None:
            return self._final_message

        msg = await asyncio.to_thread(self._handle.result)
        final_message = _validate_assistant_message_contract(
            msg,
            where="result",
            require_usage=True,
        )
        self._final_message = final_message
        return final_message

    def __aiter__(self) -> AlchemyStreamResponse:
        return self

    async def __anext__(self) -> AssistantMessageEvent:
        ev = await asyncio.to_thread(self._handle.next_event)
        if ev is None:
            raise StopAsyncIteration
        if isinstance(ev, AssistantMessageEvent):
            return ev
        if not isinstance(ev, dict):
            raise RuntimeError("tinyagent._alchemy returned an invalid event")
        return AssistantMessageEvent.model_validate(ev)
```

## Exact Log Excerpt

Source: `/home/fabian/.local/share/tunacode/logs/tunacode.log`

```text
2026-03-25T16:18:45.453229+00:00 [DEBUG  ] [LIFECYCLE] Init: pre_stream total=18.3ms
2026-03-25T16:18:45.454246+00:00 [DEBUG  ] [LIFECYCLE] Stream: start thread=130074461500992
2026-03-25T16:18:45.462171+00:00 [DEBUG  ] [LIFECYCLE] Stream: provider_open attempt=1/10 dur=0.6ms
2026-03-25T16:18:46.610537+00:00 [DEBUG  ] [LIFECYCLE] UI: delta_timer_drift seq=2 drift=1077.6ms queue=0
2026-03-25T16:18:46.610675+00:00 [DEBUG  ] [LIFECYCLE] Stream: first_event type=AgentStartEvent since_start=1156.4ms thread=130074461500992
2026-03-25T16:18:46.622893+00:00 [DEBUG  ] [LIFECYCLE] Stream: provider_first_raw type=start since_open=1161.3ms since_response=1160.7ms
2026-03-25T16:18:47.060821+00:00 [DEBUG  ] [LIFECYCLE] Stream: provider_raw_gap type=thinking_delta gap=435.3ms count=4
2026-03-25T16:18:47.061642+00:00 [DEBUG  ] [LIFECYCLE] Bridge: seq=2 stream=0ch/0c thinking=1ch/4c backlog=435.5ms flush=0.6ms stream_cb=0.0ms thinking_cb=0.5ms
2026-03-25T16:18:47.061944+00:00 [DEBUG  ] [LIFECYCLE] Stream: event_gap type=message_update/thinking_delta gap=436.3ms count=8
2026-03-25T16:18:47.264967+00:00 [DEBUG  ] [LIFECYCLE] Stream: provider_result dur=5.8ms
2026-03-25T16:18:47.267173+00:00 [DEBUG  ] [LIFECYCLE] Stream: end events=16 first_event=1156.4ms
2026-03-25T16:18:47.268353+00:00 [DEBUG  ] [LIFECYCLE] Request complete (1813ms)
```

## Working Hypothesis

The most likely remaining cause is that `_handle.next_event` is blocking in a way that still starves Python scheduling, despite being called via `asyncio.to_thread(...)`.

Possible explanations:

- the Rust or PyO3 boundary is not releasing the GIL while waiting
- the underlying stream handle is doing blocking work that prevents other Python work from running smoothly
- event production is delayed before the first raw event is made visible to Python

## Open Questions For tinyagent

1. Does `_handle.next_event` release the GIL while waiting for stream data?
2. Is there any known issue in the alchemy stream path where the first event can be delayed by about 1.1s while starving unrelated Python/UI work?
3. Where is the best boundary for deeper instrumentation: before `_handle.next_event`, inside the Rust stream handle, or around event parsing/validation?

## Current Recommendation

Do not spend more time on TunaCode UI decoupling until the tinyagent stream-path question is answered.

The current evidence says the remaining stall is upstream of TunaCode's own stream handling.
