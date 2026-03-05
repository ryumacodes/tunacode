---
title: Refactor RequestOrchestrator to typed tinyagent events
type: delta
link: request-orchestrator-typed-events
path: src/tunacode/core/agents/main.py
depth: 2
seams: [M]
ontological_relations:
  - affects: [[orchestrator]]
  - affects: [[tinyagent-events]]
  - affects: [[tool-lifecycle]]
  - affects: [[tests]]
tags:
  - tinyagent
  - typing
  - orchestrator
  - events
created_at: 2026-03-04T20:50:00+00:00
updated_at: 2026-03-04T20:50:00+00:00
uuid: 8da5ec6a-841d-4044-aa98-dfc1784c0425
---

# Refactor RequestOrchestrator to typed tinyagent events

## Summary

Converted RequestOrchestrator stream handling from dynamic `getattr`/string-dispatch patterns to typed tinyagent event handling.

### Core runtime changes

- `RequestOrchestrator` now dispatches `AgentEvent` via `_dispatch_stream_event(...)` using tinyagent type guards.
- Stream handlers now consume typed event classes directly:
  - `TurnEndEvent`
  - `MessageUpdateEvent`
  - `MessageEndEvent`
  - `ToolExecutionStartEvent`
  - `ToolExecutionEndEvent`
  - `AgentEndEvent`
- Removed dynamic field extraction (`getattr(...)`) and cast-heavy access for stream event fields.
- `_agent_error_text(...)` now reads typed state (`agent.state.error`) instead of map access.
- `_persist_agent_messages(...)` now reads typed state (`agent.state.messages`) instead of map access.
- Empty-response detection now uses `tinyagent.extract_text(...)` on typed assistant messages.

### Tool event argument contract

- Simplified tool-start args normalization:
  - accepts `None` -> `{}`
  - accepts object/dict payload
  - rejects non-object payloads with explicit `TypeError`
- Removed obsolete JSON-string argument parsing path from tool start events.

### Tool result text extraction

- `extract_tool_result_text(...)` now supports both:
  - legacy dict content blocks
  - typed content blocks (objects with `type`/`text` attributes)

## Test updates

Updated orchestrator tests to use typed tinyagent events instead of `SimpleNamespace`/dict event shims:

- `tests/unit/core/test_request_orchestrator_parallel_tools.py`
  - uses `ToolExecutionStartEvent` / `ToolExecutionEndEvent`
  - uses `AgentToolResult` + `TextContent`
- `tests/unit/core/test_thinking_stream_routing.py`
  - uses `MessageUpdateEvent` + `AssistantMessageEvent`

## Validation

- `uv run ruff check .` ✅
- `uv run pytest tests/unit/core/test_request_orchestrator_parallel_tools.py tests/unit/core/test_thinking_stream_routing.py -q` ✅
- `uv run pytest tests/unit/core/test_tinyagent_openrouter_model_config.py tests/integration/core/test_minimax_execution_path.py tests/unit/core/test_request_orchestrator_parallel_tools.py tests/unit/core/test_thinking_stream_routing.py -q` ✅ (23 passed)
