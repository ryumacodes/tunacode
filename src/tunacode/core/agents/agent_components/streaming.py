"""Streaming instrumentation and handling for agent model request nodes.

This module encapsulates verbose streaming logic used during
token-level streaming from the LLM provider. It updates session debug fields
and streams deltas to the provided callback while being resilient to errors.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import Any

from pydantic_ai.messages import PartDeltaEvent, TextPartDelta

from tunacode.types.callbacks import StreamingCallback

from tunacode.core.logging import get_logger
from tunacode.core.types import StateManagerProtocol

from .streaming_debug import (
    DEBUG_STREAM_EVENT_CONTENT_PREVIEW_LEN,
    DEBUG_STREAM_EVENT_LOG_LIMIT,
    DEBUG_STREAM_EVENT_SHORT_PREVIEW_LEN,
    DEBUG_STREAM_PREFIX_MAX_LEN,
    _append_debug_event,
    _append_raw_stream,
    _capture_pre_first_delta_text,
    _format_stream_preview,
    _log_seed_prefix_skip,
    _log_stream_event_debug,
    _log_stream_init,
    _log_stream_open,
    _maybe_log_final_text_debug,
)

MILLISECONDS_PER_SECOND: int = 1000


@dataclass(slots=True)
class _StreamState:
    """Local stream tracking state."""

    debug_event_count: int = 0
    first_delta_logged: bool = False
    first_delta_seen: bool = False
    seeded_prefix_sent: bool = False
    pre_first_delta_text: str | None = None


def _find_overlap_length(pre_text: str, delta_text: str) -> int:
    """Find length of longest pre_text suffix that equals delta_text prefix.

    This detects when delta_text starts with content already in pre_text,
    so we can avoid emitting duplicate text.

    Returns:
        Number of characters that overlap (0 if no overlap).
    """
    if not pre_text or not delta_text:
        return 0

    max_check = min(len(pre_text), len(delta_text))
    for overlap_len in range(max_check, 0, -1):
        if delta_text[:overlap_len] == pre_text[-overlap_len:]:
            return overlap_len
    return 0


def _initialize_stream_state(state_manager: StateManagerProtocol) -> _StreamState:
    state_manager.session._debug_raw_stream_accum = ""
    state_manager.session._debug_events = []
    return _StreamState()


async def _seed_prefix_if_needed(
    state: _StreamState,
    delta_text: str,
    streaming_callback: StreamingCallback,
    debug_mode: bool,
    state_manager: StateManagerProtocol,
) -> None:
    if state.first_delta_seen:
        return

    state.first_delta_seen = True
    try:
        pre_text = state.pre_first_delta_text
        if pre_text is None:
            return

        prefix_len_ok = len(pre_text) <= DEBUG_STREAM_PREFIX_MAX_LEN
        should_seed = prefix_len_ok and not state.seeded_prefix_sent
        if not should_seed:
            return

        overlap_len = _find_overlap_length(pre_text, delta_text)
        prefix_len = len(pre_text) - overlap_len
        prefix_to_emit = pre_text[:prefix_len]
        should_emit = bool(prefix_to_emit.strip())
        if should_emit:
            await streaming_callback(prefix_to_emit)
            state.seeded_prefix_sent = True
            if debug_mode:
                preview_text = prefix_to_emit[:DEBUG_STREAM_EVENT_SHORT_PREVIEW_LEN]
                preview_msg = (
                    f"[src] seeded_prefix overlap={overlap_len} "
                    f"len={len(prefix_to_emit)} preview={repr(preview_text)}"
                )
                _append_debug_event(state_manager, preview_msg)
            return

        if debug_mode:
            _log_seed_prefix_skip(
                state_manager,
                overlap_len,
                delta_text,
                pre_text,
            )
    except Exception:
        pass
    finally:
        state.pre_first_delta_text = None


def _log_first_delta_received(
    state: _StreamState,
    delta_text: str,
    debug_mode: bool,
    state_manager: StateManagerProtocol,
) -> None:
    should_log = debug_mode and not state.first_delta_logged
    if not should_log:
        return

    try:
        import time as _t

        ts_ns = _t.perf_counter_ns()
    except Exception:
        ts_ns = 0

    preview_text = delta_text[:DEBUG_STREAM_EVENT_CONTENT_PREVIEW_LEN] if delta_text else ""
    chunk_preview = repr(preview_text)
    chunk_len = len(delta_text)
    delta_msg = (
        f"[src] first_delta_received ts_ns={ts_ns} chunk_repr={chunk_preview} len={chunk_len}"
    )
    _append_debug_event(state_manager, delta_msg)
    state.first_delta_logged = True


async def _handle_text_delta_event(
    state: _StreamState,
    delta_text: str,
    streaming_callback: StreamingCallback,
    debug_mode: bool,
    state_manager: StateManagerProtocol,
) -> None:
    await _seed_prefix_if_needed(
        state,
        delta_text,
        streaming_callback,
        debug_mode,
        state_manager,
    )
    _log_first_delta_received(state, delta_text, debug_mode, state_manager)
    _append_raw_stream(state_manager, delta_text)
    await streaming_callback(delta_text)


async def _handle_part_delta_event(
    event: PartDeltaEvent,
    state: _StreamState,
    streaming_callback: StreamingCallback,
    debug_mode: bool,
    state_manager: StateManagerProtocol,
) -> None:
    if not isinstance(event.delta, TextPartDelta):
        if debug_mode:
            _append_debug_event(
                state_manager,
                "[src] empty_or_nontext_delta_skipped",
            )
        return

    delta_content = event.delta.content_delta
    if delta_content is None:
        if debug_mode:
            _append_debug_event(
                state_manager,
                "[src] empty_or_nontext_delta_skipped",
            )
        return

    delta_text = delta_content or ""
    await _handle_text_delta_event(
        state,
        delta_text,
        streaming_callback,
        debug_mode,
        state_manager,
    )


async def _consume_request_stream(
    request_stream: Any,
    state: _StreamState,
    streaming_callback: StreamingCallback,
    debug_mode: bool,
    state_manager: StateManagerProtocol,
    logger: Any,
) -> None:
    async for event in request_stream:
        state.debug_event_count += 1
        event_index = state.debug_event_count

        should_log_event = debug_mode and event_index <= DEBUG_STREAM_EVENT_LOG_LIMIT
        if should_log_event:
            _log_stream_event_debug(logger, state_manager, event, event_index)

        state.pre_first_delta_text = _capture_pre_first_delta_text(
            event,
            state.first_delta_seen,
            state.pre_first_delta_text,
        )

        if isinstance(event, PartDeltaEvent):
            await _handle_part_delta_event(
                event,
                state,
                streaming_callback,
                debug_mode,
                state_manager,
            )
            continue

        _maybe_log_final_text_debug(event, debug_mode, state_manager)


async def stream_model_request_node(
    node: Any,
    agent_run_ctx: Any,
    state_manager: StateManagerProtocol,
    streaming_callback: StreamingCallback | None,
    request_id: str,
    iteration_index: int,
) -> None:
    """Stream token deltas for a model request node with detailed instrumentation.

    This function mirrors the prior inline logic in main.py but is extracted to
    keep main.py lean. On streaming failure, it degrades gracefully to allow
    non-streaming processing of the node.
    """
    if streaming_callback is None:
        return

    logger = get_logger()
    stream_start = time.perf_counter()
    debug_mode = bool(getattr(state_manager.session, "debug_mode", False))
    node_type = type(node).__name__
    _log_stream_init(logger, node, node_type, request_id, iteration_index, debug_mode)

    try:
        async with node.stream(agent_run_ctx) as request_stream:
            stream_state = _initialize_stream_state(state_manager)
            _log_stream_open(
                state_manager,
                logger,
                node_type,
                request_id,
                iteration_index,
                debug_mode,
            )

            await _consume_request_stream(
                request_stream,
                stream_state,
                streaming_callback,
                debug_mode,
                state_manager,
                logger,
            )
            stream_elapsed_ms = (time.perf_counter() - stream_start) * MILLISECONDS_PER_SECOND
            logger.lifecycle(
                f"Stream: {stream_state.debug_event_count} events, {stream_elapsed_ms:.0f}ms"
            )
            if debug_mode:
                raw_stream = state_manager.session._debug_raw_stream_accum
                raw_preview, raw_len = _format_stream_preview(raw_stream)
                logger.debug(
                    f"Stream done: events={stream_state.debug_event_count} "
                    f"raw_len={raw_len} preview={raw_preview}"
                )
    except asyncio.CancelledError:
        logger.lifecycle("Stream cancelled")
        raise
    except Exception as e:
        # Log and re-raise - no silent fallbacks
        logger.lifecycle(f"Stream failed: {type(e).__name__}: {e}")
        raise
