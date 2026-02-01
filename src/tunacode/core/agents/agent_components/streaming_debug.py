"""Debug helpers for streaming instrumentation."""

from __future__ import annotations

from typing import Any

from tunacode.core.logging import get_logger
from tunacode.core.types import StateManagerProtocol

DEBUG_STREAM_EVENT_LOG_LIMIT: int = 5
DEBUG_STREAM_EVENT_HISTORY_LIMIT: int = 200
DEBUG_STREAM_RAW_STREAM_MAX_CHARS: int = 20_000
DEBUG_STREAM_TEXT_PREVIEW_LEN: int = 120
DEBUG_STREAM_NEWLINE_REPLACEMENT: str = "\\n"
DEBUG_STREAM_PREVIEW_SUFFIX: str = "..."
DEBUG_STREAM_EVENT_CONTENT_PREVIEW_LEN: int = 5
DEBUG_STREAM_EVENT_SHORT_PREVIEW_LEN: int = 20
DEBUG_STREAM_PREFIX_MAX_LEN: int = 100
STREAM_TEXT_ATTRIBUTES: tuple[str, ...] = ("output", "text", "content", "message")
STREAM_NESTED_TEXT_ATTRIBUTES: tuple[str, ...] = ("result", "response", "final")


def _format_stream_preview(value: Any) -> tuple[str, int]:
    """Return a truncated preview for debug logging."""
    if value is None:
        return "", 0

    value_text = value if isinstance(value, str) else str(value)
    value_len = len(value_text)
    preview_len = min(DEBUG_STREAM_TEXT_PREVIEW_LEN, value_len)
    preview = value_text[:preview_len]
    if value_len > preview_len:
        preview = f"{preview}{DEBUG_STREAM_PREVIEW_SUFFIX}"
    preview = preview.replace("\n", DEBUG_STREAM_NEWLINE_REPLACEMENT)
    return preview, value_len


def _format_request_part_debug(part: Any) -> str:
    """Format a model request part for debug logging."""
    part_kind_value = getattr(part, "part_kind", None)
    part_kind = part_kind_value if part_kind_value is not None else "unknown"
    tool_name = getattr(part, "tool_name", None)
    tool_call_id = getattr(part, "tool_call_id", None)
    content = getattr(part, "content", None)
    args = getattr(part, "args", None)

    segments = [f"kind={part_kind}"]
    if tool_name:
        segments.append(f"tool={tool_name}")
    if tool_call_id:
        segments.append(f"id={tool_call_id}")

    content_preview, content_len = _format_stream_preview(content)
    if content_preview:
        segments.append(f"content={content_preview} ({content_len} chars)")

    args_preview, args_len = _format_stream_preview(args)
    if args_preview:
        segments.append(f"args={args_preview} ({args_len} chars)")

    return " ".join(segments)


def _log_stream_request_parts(node: Any, debug_mode: bool) -> None:
    """Log the request parts just before opening a stream."""
    if not debug_mode:
        return

    logger = get_logger()
    request = getattr(node, "request", None)
    if request is None:
        logger.debug("Stream request: none")
        return

    request_type = type(request).__name__
    request_parts = getattr(request, "parts", None)
    if request_parts is None:
        logger.debug(f"Stream request parts: count=0 type={request_type} parts=None")
        return
    if not isinstance(request_parts, list):
        preview, preview_len = _format_stream_preview(request_parts)
        logger.debug(
            f"Stream request parts: type={request_type} "
            f"parts_type={type(request_parts).__name__} preview={preview} "
            f"({preview_len} chars)"
        )
        return
    if not request_parts:
        logger.debug(f"Stream request parts: count=0 type={request_type}")
        return

    request_part_count = len(request_parts)
    logger.debug(f"Stream request parts: count={request_part_count} type={request_type}")
    for part_index, part in enumerate(request_parts):
        part_summary = _format_request_part_debug(part)
        logger.debug(f"Stream request part[{part_index}]: {part_summary}")


def _append_debug_event(state_manager: StateManagerProtocol, entry: str) -> None:
    debug_events = state_manager.session._debug_events
    debug_events.append(entry)
    if len(debug_events) <= DEBUG_STREAM_EVENT_HISTORY_LIMIT:
        return
    overflow = len(debug_events) - DEBUG_STREAM_EVENT_HISTORY_LIMIT
    del debug_events[:overflow]


def _append_raw_stream(state_manager: StateManagerProtocol, delta_text: str) -> None:
    if not delta_text:
        return

    session = state_manager.session
    current_stream = session._debug_raw_stream_accum
    updated_stream = f"{current_stream}{delta_text}"
    if len(updated_stream) > DEBUG_STREAM_RAW_STREAM_MAX_CHARS:
        updated_stream = updated_stream[-DEBUG_STREAM_RAW_STREAM_MAX_CHARS:]
    session._debug_raw_stream_accum = updated_stream


def _format_debug_preview(value: str, preview_len: int) -> tuple[str, int]:
    preview = repr(value[:preview_len])
    return preview, len(value)


def _extract_first_part_text(parts: Any) -> str | None:
    if not isinstance(parts, list | tuple):
        return None

    for part in parts:
        content = getattr(part, "content", None)
        if isinstance(content, str) and content:
            return content
    return None


def _extract_text_from_parts(parts: Any) -> str | None:
    if not isinstance(parts, list | tuple) or not parts:
        return None

    texts: list[str] = []
    for part in parts:
        content = getattr(part, "content", None)
        if isinstance(content, str) and content:
            texts.append(content)

    if not texts:
        return None

    return "".join(texts)


def _extract_stream_result_text(obj: Any) -> str | None:
    try:
        if obj is None:
            return None
        if isinstance(obj, str):
            return obj

        for attr in STREAM_TEXT_ATTRIBUTES:
            attr_value = getattr(obj, attr, None)
            if isinstance(attr_value, str) and attr_value:
                return attr_value

        parts = getattr(obj, "parts", None)
        parts_text = _extract_text_from_parts(parts)
        if parts_text:
            return parts_text

        for attr in STREAM_NESTED_TEXT_ATTRIBUTES:
            nested = getattr(obj, attr, None)
            nested_text = _extract_stream_result_text(nested)
            if nested_text:
                return nested_text
    except Exception:
        return None

    return None


def _extract_result_preview(result: Any) -> tuple[str | None, int | None]:
    try:
        if isinstance(result, str):
            return _format_debug_preview(result, DEBUG_STREAM_EVENT_SHORT_PREVIEW_LEN)

        output = getattr(result, "output", None)
        if isinstance(output, str):
            return _format_debug_preview(output, DEBUG_STREAM_EVENT_SHORT_PREVIEW_LEN)

        text = getattr(result, "text", None)
        if isinstance(text, str):
            return _format_debug_preview(text, DEBUG_STREAM_EVENT_SHORT_PREVIEW_LEN)

        parts = getattr(result, "parts", None)
        first_part_text = _extract_first_part_text(parts)
        if first_part_text:
            return _format_debug_preview(
                first_part_text,
                DEBUG_STREAM_EVENT_SHORT_PREVIEW_LEN,
            )
    except Exception:
        return None, None

    return None, None


def _get_delta_debug_data(event: Any) -> tuple[str | None, int | None, str | None]:
    delta = getattr(event, "delta", None)
    delta_type = type(delta).__name__ if delta is not None else None
    if delta is None:
        return delta_type, None, None

    content = getattr(delta, "content_delta", None)
    if not isinstance(content, str):
        return delta_type, None, None

    preview, content_len = _format_debug_preview(content, DEBUG_STREAM_EVENT_CONTENT_PREVIEW_LEN)
    return delta_type, content_len, preview


def _get_result_debug_data(event: Any) -> tuple[str | None, str | None, int | None]:
    result = getattr(event, "result", None)
    result_type = type(result).__name__ if result is not None else None
    if result is None:
        return result_type, None, None

    preview, length = _extract_result_preview(result)
    return result_type, preview, length


def _get_part_debug_data(event: Any) -> tuple[str | None, Any, str | None, int | None]:
    part = getattr(event, "part", None)
    part_type = type(part).__name__ if part is not None else None
    part_kind = getattr(part, "part_kind", None) if part is not None else None
    part_content = getattr(part, "content", None) if part is not None else None
    if isinstance(part_content, str):
        preview, length = _format_debug_preview(
            part_content,
            DEBUG_STREAM_EVENT_SHORT_PREVIEW_LEN,
        )
        return part_type, part_kind, preview, length

    return part_type, part_kind, None, None


def _build_stream_event_debug_info(event: Any, event_index: int) -> str:
    event_type = type(event).__name__
    delta_type, content_len, content_preview = _get_delta_debug_data(event)
    result_type, result_preview, result_len = _get_result_debug_data(event)
    part_type, part_kind, part_preview, part_len = _get_part_debug_data(event)
    return (
        f"[src] event[{event_index}] etype={event_type} d={delta_type} "
        f"clen={content_len} cprev={content_preview} rtype={result_type} "
        f"rprev={result_preview} rlen={result_len} ptype={part_type} "
        f"pkind={part_kind} pprev={part_preview} plen={part_len}"
    )


def _log_stream_event_debug(
    logger: Any,
    state_manager: StateManagerProtocol,
    event: Any,
    event_index: int,
) -> None:
    try:
        event_info = _build_stream_event_debug_info(event, event_index)
    except Exception:
        return

    _append_debug_event(state_manager, event_info)
    logger.debug(event_info)


def _log_stream_init(
    logger: Any,
    node: Any,
    node_type: str,
    request_id: str,
    iteration_index: int,
    debug_mode: bool,
) -> None:
    if not debug_mode:
        return

    logger.debug(
        f"Stream init: node={node_type} request_id={request_id} iteration={iteration_index}"
    )
    _log_stream_request_parts(node, debug_mode)


def _log_stream_open(
    state_manager: StateManagerProtocol,
    logger: Any,
    node_type: str,
    request_id: str,
    iteration_index: int,
    debug_mode: bool,
) -> None:
    if not debug_mode:
        return

    try:
        import time as _t

        _append_debug_event(
            state_manager,
            f"[src] stream_opened ts_ns={_t.perf_counter_ns()}",
        )
    except Exception:
        pass

    logger.debug(
        f"Stream opened: node={node_type} request_id={request_id} iteration={iteration_index}"
    )


def _truncate_prefix(text: str) -> str:
    if len(text) <= DEBUG_STREAM_PREFIX_MAX_LEN:
        return text

    return text[:DEBUG_STREAM_PREFIX_MAX_LEN]


def _capture_pre_first_delta_text(
    event: Any,
    first_delta_seen: bool,
    existing_text: str | None,
) -> str | None:
    if first_delta_seen:
        return existing_text

    try:
        part = getattr(event, "part", None)
        part_content = getattr(part, "content", None) if part is not None else None
        is_text = isinstance(part_content, str)
        if not is_text or not part_content:
            return existing_text

        trimmed = part_content.lstrip()
        if trimmed.startswith("\n"):
            return existing_text

        return _truncate_prefix(part_content)
    except Exception:
        return existing_text


def _log_seed_prefix_skip(
    state_manager: StateManagerProtocol,
    overlap_len: int,
    delta_text: str,
    pre_text: str,
) -> None:
    skip_msg = (
        f"[src] seed_skip overlap={overlap_len} delta_len={len(delta_text)} pre_len={len(pre_text)}"
    )
    _append_debug_event(state_manager, skip_msg)


def _maybe_log_final_text_debug(
    event: Any,
    debug_mode: bool,
    state_manager: StateManagerProtocol,
) -> None:
    try:
        final_text = _extract_stream_result_text(getattr(event, "result", None))
    except Exception:
        return

    if debug_mode and final_text:
        preview_text = final_text[:DEBUG_STREAM_EVENT_SHORT_PREVIEW_LEN]
        final_msg = f"[src] final_text_preview len={len(final_text)} preview={repr(preview_text)}"
        _append_debug_event(state_manager, final_msg)
