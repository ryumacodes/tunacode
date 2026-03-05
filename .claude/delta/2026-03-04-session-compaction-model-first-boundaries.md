---
title: Migrate session and compaction flows to model-first tinyagent messages
type: delta
link: session-compaction-model-first-boundaries
path: src/tunacode/core/session/state.py
depth: 2
seams: [M]
ontological_relations:
  - affects: [[session-state]]
  - affects: [[compaction-controller]]
  - affects: [[compaction-summarizer]]
  - affects: [[ui-message-rendering]]
  - affects: [[headless-output]]
tags:
  - tinyagent
  - typing
  - session
  - compaction
  - boundaries
created_at: 2026-03-04T21:55:00+00:00
updated_at: 2026-03-04T21:55:00+00:00
uuid: 1e900ce3-cd9f-4359-a445-c6a41e6fed40
---

# Migrate session and compaction flows to model-first tinyagent messages

## Summary

Completed the session + compaction message boundary migration so runtime paths use typed tinyagent message models, while persistence remains explicit JSON serialization/deserialization.

## Runtime typing changes

### Session state boundary (`src/tunacode/core/session/state.py`)

- Session conversation history is now treated as **tinyagent message models** in memory.
- Added explicit serialization boundary:
  - `_serialize_messages()` validates model instances and serializes via `model_dump(exclude_none=True)`.
- Added explicit deserialization boundary:
  - `_deserialize_message()` role-dispatches to `UserMessage` / `AssistantMessage` / `ToolResultMessage` / `CustomAgentMessage`.
  - raises structured `TypeError` on invalid payloads or validation failures.
- Moved thought extraction to raw JSON phase:
  - split legacy thought entries from raw persisted message list before model validation.
- Added explicit persisted thoughts validation (`_deserialize_thoughts`).

### Orchestrator compaction path (`src/tunacode/core/agents/main.py`)

- Compaction/retry history APIs now use `list[AgentMessage]` (not `list[dict[str, Any]]`):
  - `_compact_history_for_request(...)`
  - `_force_compact_history(...)`
  - `_retry_after_context_overflow_if_needed(...)`
- Removed dict casts in compaction return path.
- Abort cleanup now appends typed `AssistantMessage` with `TextContent`, not dict payload.

### Compaction internals (`src/tunacode/core/compaction/*`)

- `CompactionController._generate_summary(...)` now builds typed `UserMessage` + `TextContent` prompt context and typed `SimpleStreamOptions`.
- Summary marker handling is model-first:
  - `_is_compaction_summary_message(...)` works with typed `UserMessage`/`TextContent`.
  - `_build_summary_user_message(...)` returns `UserMessage` with `compaction_summary=True` extra field.
- `ContextSummarizer` now operates on typed tinyagent message models for:
  - boundary detection,
  - tool/result pairing checks,
  - serialization for summary prompting.

### Messaging utilities and UI consumers

- `utils.messaging.adapter.to_canonical(...)` now accepts tinyagent message models (serializing to dict via `model_dump(...)` internally).
- Token counter docs updated to reflect model-first runtime and JSON boundary support.
- UI and headless paths now consume typed models:
  - `ui/app.py` latest-response extraction and session replay
  - `ui/headless/output.py` assistant fallback extraction
  - `ui/commands/compact.py` history coercion
  - `ui/main.py` headless trajectory serialization via model dump

## Validation

- `uv run ruff check .` ✅
- `uv run pytest tests/unit/core/test_compaction_summarizer.py tests/unit/core/test_compaction_controller_outcomes.py tests/test_compaction.py tests/unit/core/test_session_usage_schema.py tests/unit/core/test_tinyagent_openrouter_model_config.py tests/unit/types/test_adapter.py tests/unit/ui/test_app_latest_response_text.py tests/system/cli/test_startup.py tests/unit/core/test_request_orchestrator_parallel_tools.py tests/unit/core/test_thinking_stream_routing.py tests/integration/core/test_minimax_execution_path.py -q` ✅ (71 passed, 1 skipped)

## Notes

- Persistence remains a strict boundary (JSON in/out), but runtime now treats conversation and compaction flow as typed tinyagent models.
- No pydantic-ai compatibility paths were reintroduced.
