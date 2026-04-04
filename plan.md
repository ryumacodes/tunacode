---
title: TunaCode Headless RPC Rewrite Plan
summary: Implementation plan for replacing the current one-shot headless path with a long-lived RPC agent mode.
when_to_read:
  - When implementing the headless RPC rewrite
  - When reviewing the migration plan
last_updated: "2026-04-04"
---

# TunaCode headless RPC rewrite plan

## Goal
Replace the current one-shot headless path with a long-lived RPC agent mode.

## Why this shape
- Current headless is a `run` subcommand that makes exactly one `process_request(...)` call, passes `streaming_callback=None`, `tool_result_callback=None`, and `tool_start_callback=None`, then prints one final text result or one final JSON snapshot. See `src/tunacode/ui/main.py:192-259`.
- The TUI already uses the same `process_request(...)` core path with streaming/thinking/tool callbacks and saves the session after completion. See `src/tunacode/ui/app.py:328-420`.
- Session persistence is not automatic for headless today, and `StateManager.save_session()` no-ops if `project_id` is unset. See `src/tunacode/core/session/state.py:319-347`. The TUI initializes `project_id`, `working_directory`, and `created_at` in `src/tunacode/ui/lifecycle.py:56-65`.
- The existing callback API is too lossy for a protocol boundary:
  - `ToolStartCallback` only receives the tool name. See `src/tunacode/types/callbacks.py:62`.
  - `ToolResultCallback` does not include `tool_call_id`. See `src/tunacode/types/callbacks.py:63-65`.
  - `StreamingCallback` only receives a raw text delta. See `src/tunacode/types/callbacks.py:70` and `src/tunacode/core/agents/main.py:703-719`.
  - `ToolCallRegistry.to_legacy_records()` drops status/result and is not suitable as a protocol state model. See `src/tunacode/core/types/tool_registry.py:167-179`.
- PI RPC mode is the right reference shape: JSON commands on stdin, `type: "response"` responses, streamed events on stdout, and strict LF-delimited JSONL framing.

## Hard constraints
- Do not preserve `tunacode run`.
- Do not build the new protocol directly on the current callback signatures.
- Do not add TunaCode-owned wrappers around tinyagent message models in memory. If runtime events need to carry messages, carry tinyagent messages or their boundary dumps.
- Keep layer boundaries valid: new transport code belongs under `ui`, shared event protocols/types belong under `types`.
- Keep files split; do not create a new >600 line sinkhole.

## Public surface for v1
Use a new command:

```bash
tunacode rpc [--cwd PATH] [--model MODEL] [--baseurl URL] [--auto-approve]
```

### Protocol invariants
- stdout is protocol-only
- stderr is diagnostics-only
- exactly one JSON object per line
- LF (`\n`) is the record delimiter
- one active request at a time
- process stays alive across multiple commands

### v1 commands
- `prompt`
- `abort`
- `get_state`
- `get_messages`
- `set_model`
- `compact`

### v1 events
- `agent_start`
- `agent_end`
- `turn_start`
- `turn_end`
- `message_start`
- `message_update`
- `message_end`
- `tool_execution_start`
- `tool_execution_update`
- `tool_execution_end`

### Explicit v1 non-goals
- no `steer`
- no `follow_up`
- no multi-session switching
- no image input
- no extra RPC commands for bash/extensions
- no auto-compaction event payload until compaction emits richer metadata than a bool

## Required architecture

### 1) Add a normalized runtime event layer
Create a shared event contract that the orchestrator emits and both UI surfaces consume.

Proposed files:

```text
src/tunacode/types/runtime_events.py
src/tunacode/ui/rpc/protocol.py
src/tunacode/ui/rpc/transport.py
src/tunacode/ui/rpc/adapter.py
src/tunacode/ui/rpc/session.py
src/tunacode/ui/rpc/mode.py
src/tunacode/ui/session_metadata.py
```

### 2) Put the shared contract in `types`
`src/tunacode/types/runtime_events.py`
- define the runtime event union/dataclasses/protocols
- do not invent parallel TunaCode message models
- allow events to carry tinyagent message/event objects or pre-serialized boundary dicts
- include the data the current callbacks lose, especially `tool_call_id`

Minimum runtime event set:
- request lifecycle: `agent_start`, `agent_end`
- turn lifecycle: `turn_start`, `turn_end`
- message lifecycle: `message_start`, `message_update`, `message_end`
- tool lifecycle: `tool_execution_start`, `tool_execution_update`, `tool_execution_end`
- optional internal-only state flips: `streaming_state_changed`, `compaction_state_changed`

### 3) Refactor `RequestOrchestrator` to emit runtime events
`src/tunacode/core/agents/main.py`
- add a new `runtime_event_sink` parameter to `RequestOrchestrator` and `process_request(...)`
- emit normalized events from the orchestrator itself
- keep the TUI working by adapting it to the new sink
- only remove direct callback fan-out after TUI parity is proven

Important details:
- synthesize `agent_start` before streaming begins
- synthesize `turn_start` / `message_start` if tinyagent does not expose explicit start events in the current stream
- forward full `MessageUpdateEvent` information, not only text deltas
- include `tool_call_id`, `tool_name`, args, partial result, final result, and error flag on tool events
- emit `agent_end` with the newly produced messages for the completed run

### 4) Reuse session metadata initialization outside the TUI
Extract the logic in `src/tunacode/ui/lifecycle.py:56-65` into a reusable helper, e.g. `src/tunacode/ui/session_metadata.py`.

That helper must:
- set `project_id`
- set `working_directory`
- set `created_at` if absent

RPC mode must call it before the first prompt so `save_session()` actually persists.

### 5) Build the RPC session as a long-lived state machine
`src/tunacode/ui/rpc/session.py`

Responsibilities:
- own `StateManager`
- own the current request task
- track `is_streaming`
- track `is_compacting`
- serialize command handling so only one request runs at a time
- save session after terminal operations
- keep the process alive until stdin EOF or fatal startup error

Core rules:
- `prompt` while idle: start request task, return immediate success response, stream events asynchronously
- `prompt` while streaming: return structured error response in v1
- `abort`: cancel the active task and return structured success
- `get_state`: return session id, current model, `isStreaming`, `isCompacting`, `messageCount`, `pendingMessageCount`
- `get_messages`: return serialized conversation messages from `state_manager.session.conversation.messages`
- `set_model`: update `state_manager.session.current_model`; reject while streaming in v1
- `compact`: invoke compaction only when idle in v1

### 6) Keep protocol parsing and transport separate
`src/tunacode/ui/rpc/protocol.py`
- discriminated command/response/event schema
- explicit parse/validate helpers
- keep wire payloads as plain dicts at the boundary

`src/tunacode/ui/rpc/transport.py`
- read LF-delimited JSON lines from stdin
- accept `\r\n` by stripping trailing `\r`
- write exactly one compact JSON object plus `\n` to stdout
- write no banners, no prompts, no pretty-printed JSON
- send diagnostics only to stderr

### 7) Map runtime events to PI-style wire events
`src/tunacode/ui/rpc/adapter.py`
- convert runtime events into wire events
- use camelCase only at the protocol boundary if needed for PI-like event shapes
- do not use `ToolCallRegistry.to_legacy_records()` for live protocol data
- use `model_dump(exclude_none=True)` style serialization for tinyagent messages at the wire boundary

Suggested event examples:

```json
{"id":"1","type":"response","command":"prompt","success":true}
{"type":"agent_start"}
{"type":"message_update","message":{...},"assistantMessageEvent":{...}}
{"type":"tool_execution_start","toolCallId":"call_1","toolName":"bash","args":{"command":"pwd"}}
{"type":"tool_execution_end","toolCallId":"call_1","toolName":"bash","result":{...},"isError":false}
{"type":"agent_end","messages":[...]}
```

## File-by-file work list

### Delete
- `src/tunacode/ui/headless/__init__.py`
- `src/tunacode/ui/headless/output.py`
- old `run_headless` helpers in `src/tunacode/ui/main.py`:
  - `_build_trajectory_json`
  - `_print_headless_error`
  - `run_headless`

### Add
- `src/tunacode/types/runtime_events.py`
- `src/tunacode/ui/session_metadata.py`
- `src/tunacode/ui/rpc/protocol.py`
- `src/tunacode/ui/rpc/transport.py`
- `src/tunacode/ui/rpc/adapter.py`
- `src/tunacode/ui/rpc/session.py`
- `src/tunacode/ui/rpc/mode.py`
- new RPC-focused tests

### Modify
- `src/tunacode/core/agents/main.py`
- `src/tunacode/types/callbacks.py` if needed for the new event sink protocol
- `src/tunacode/ui/app.py` to consume runtime events through an adapter instead of relying on lossy callback signatures
- `src/tunacode/ui/lifecycle.py` to call the shared session metadata initializer
- `src/tunacode/ui/main.py` to register `tunacode rpc`
- `tests/system/cli/test_startup.py` to remove dead headless assumptions
- `docs/modules/ui/ui.md`
- `docs/codebase-map/structure/tree-structure.txt` if regenerated
- `AGENTS.md` date line

## Test plan

### New system tests
Create `tests/system/cli/test_rpc.py`.

Must cover:
1. `tunacode rpc` starts and emits no non-protocol stdout noise
2. `prompt` returns an immediate success response, then streamed events
3. `get_state` reports `isStreaming=true` while a request is active
4. second `prompt` during streaming returns a structured error response
5. `abort` cancels an active request without killing the process
6. `get_messages` returns the updated conversation after completion
7. tool execution events preserve a stable `toolCallId` across start/update/end
8. stdout framing is strict JSONL: one object per line, no pretty-printed multi-line payloads
9. invalid JSON or unknown command yields a structured error and the process remains alive
10. session is saved after a completed turn when session metadata is initialized

### New unit tests
Create focused tests for:
- protocol parsing/validation
- JSONL transport framing
- runtime-event -> RPC-event mapping
- session state transitions (`idle -> streaming -> idle`, abort path, set_model rejection while streaming)

### Existing tests to update/remove
- remove the current headless-mode assumptions from `tests/system/cli/test_startup.py`
- remove resolver tests that target `tunacode.ui.headless.resolve_output`
- keep version/help/startup tests intact

## Definition of done
The change is done when all of the following are true:
- `tunacode run` is gone
- `tunacode rpc` exists and stays alive across multiple commands
- protocol stdout is strict JSONL only
- live message and tool events are streamed with stable correlation ids
- session persistence works in RPC mode
- TUI still works through the same core request engine
- docs mention RPC mode instead of the deleted headless resolver path
- architecture tests still pass

## Validation commands
Run at minimum:

```bash
uv run pytest tests/system/cli/test_rpc.py -v
uv run pytest tests/test_dependency_layers.py -v
uv run pytest tests/architecture/test_import_order.py
uv run pytest tests/architecture/test_init_bloat.py
uv run python scripts/check_agents_freshness.py
uv run python scripts/generate_structure_tree.py
```

If the change touches broader behavior, also run:

```bash
uv run pytest
uv run pre-commit run --all-files
```

## Implementation order
1. Add runtime event types and sink protocol.
2. Refactor `RequestOrchestrator` to emit runtime events.
3. Extract shared session metadata initialization.
4. Adapt the TUI to the new runtime event flow and keep it green.
5. Add `ui/rpc/*` transport/session/protocol.
6. Replace the old headless tests with RPC tests.
7. Remove `tunacode run` and `ui/headless/*`.
8. Update docs and `AGENTS.md`.

## One explicit warning
Do not delete the old headless code in a standalone commit and then try to get back to green later. `src/tunacode/ui/main.py`, `tests/system/cli/test_startup.py`, and `docs/modules/ui/ui.md` all currently depend on that surface, so removal and replacement should happen in the same branch and the same validation pass.
