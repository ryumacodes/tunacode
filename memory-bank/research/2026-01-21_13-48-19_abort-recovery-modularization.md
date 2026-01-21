# Research - Abort Recovery Modularization

**Date:** 2026-01-21
**Owner:** claude
**Phase:** Research

## Goal

Map out commit `ad53e0b` (abort recovery fix) and plan clean modular extraction of the hastily-added code.

## Findings

### Commit Stats
- **+1,374 lines / -36 lines** across 10 files
- Main changes in `src/tunacode/core/agents/main.py` (+610 lines)
- Secondary changes in `streaming.py` (+136 lines)

### Root Causes Fixed

| Issue | Cause | Fix |
|-------|-------|-----|
| CancelledError not caught | Python 3.8+ inherits from `BaseException` | `except asyncio.CancelledError` handler |
| Empty responses | Abort during response generation | `_remove_empty_responses()` |
| Consecutive requests | Abort before model responds | `_remove_consecutive_requests()` |

### Functions Added to main.py

**Core Cleanup (4 functions, ~150 lines)**
- `_remove_consecutive_requests()` - removes duplicate request messages
- `_remove_empty_responses()` - removes `kind=response parts=0`
- `_find_dangling_tool_call_ids()` - detects orphaned tool calls
- `_remove_dangling_tool_calls()` - refactored to use new helpers

**Message Accessors (12 functions, ~200 lines)**
- `_get_attr_value()` - generic attribute getter (dict or object)
- `_normalize_list()` - coerce to list
- `_get_message_parts()` / `_set_message_parts()`
- `_get_message_tool_calls()` / `_set_message_tool_calls()`
- `_collect_tool_call_ids_from_parts()`
- `_collect_tool_call_ids_from_tool_calls()`
- `_collect_tool_return_ids_from_parts()`
- `_collect_message_tool_call_ids()`
- `_collect_message_tool_return_ids()`
- `_filter_dangling_tool_calls_from_parts()`
- `_filter_dangling_tool_calls_from_tool_calls()`
- `_strip_dangling_tool_calls_from_message()`

**Debug Logging (4 functions, ~100 lines)**
- `_format_debug_preview()` - truncate with length metadata
- `_format_part_debug()` - format message part for logging
- `_format_tool_call_debug()` - format tool call for logging
- `_log_message_history_debug()` - full history dump

**Stream Timeout (1 function + handler, ~50 lines)**
- `_coerce_stream_watchdog_timeout()` - compute timeout from global
- `asyncio.CancelledError` handler in streaming.py

### Cleanup Order (Critical)

```
dangling_tool_calls -> empty_responses -> consecutive_requests
```

Empty response removal can expose consecutive requests, so order matters.

## Key Patterns / Solutions Found

- **CancelledError is BaseException**: In Python 3.8+, `except Exception` does NOT catch `asyncio.CancelledError`. Must catch explicitly.
- **Message structure validation**: API expects alternating request/response. Validate structure, not just content.
- **Agent cache invalidation**: HTTP client can be in bad state after abort/timeout. Invalidate cache to force fresh connection.

## Proposed Modular Structure

```
src/tunacode/core/agents/agent_components/
├── message_utils.py       (12 accessor helpers)
├── message_validation.py  (4 cleanup functions, uses message_utils)
├── debug_history.py       (4 debug logging functions)
└── streaming.py           (existing + CancelledError + timeout)
```

## Knowledge Gaps

- Should `message_utils.py` be in `agent_components/` or `core/`?
- Are there other message validation scenarios to add?
- Should debug logging be behind a flag or always available?

## References

- Commit: `ad53e0b`
- GitHub Issue: #269
- Journal: `.claude/JOURNAL.md` (2026-01-21 entry)
- Skill: `~/.claude/skills/llm-agent-abort-recovery/SKILL.md`
- Tests: `tests/unit/core/test_agent_cache_abort.py`, `tests/integration/core/test_tool_call_lifecycle.py`
