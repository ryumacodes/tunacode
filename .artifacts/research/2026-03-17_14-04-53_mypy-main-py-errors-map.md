---
title: "mypy main.py errors map"
link: "mypy-main-py-errors-map"
type: research
ontological_relations:
  - relates_to: [[REQUEST_CONTEXT_CUTOVER_LESSON]]
  - relates_to: [[postmortem-defensive-message-typing-2026-03-17]]
tags: [research, mypy, core-agents]
uuid: "2026-03-17-mypy-main-py-errors-map"
created_at: "2026-03-17T14:04:53-05:00"
---

## Scope
- Command reported by user: `uv run mypy src/tunacode/`
- Reported file: `src/tunacode/core/agents/main.py`
- Reported error lines: `82`, `470`

## Strict mypy context
- `pyproject.toml:222-230` defines base mypy settings.
- `pyproject.toml:233-237` applies stricter overrides to `tunacode.core.agents` and `tunacode.core.agents.*`:
  - `warn_return_any = true`
  - `disallow_any_expr = true`
  - `disallow_any_explicit = true`
  - `disallow_any_generics = true`

## Error group 1: max iterations coercion

### Location
- `src/tunacode/core/agents/main.py:79-82`

### Code present
- `src/tunacode/core/agents/main.py:79-82` defines:
  - `_coerce_max_iterations(session: SessionStateProtocol) -> int`
  - local assignments:
    - `user_config = cast(dict[str, object], cast(object, session.user_config))`
    - `settings = cast(dict[str, object], user_config["settings"])`
    - `return int(settings["max_iterations"])`

### Mypy output attached to this location
- `src/tunacode/core/agents/main.py:82: error: Returning Any from function declared to return "int"  [no-any-return]`
- `src/tunacode/core/agents/main.py:82: error: No overload variant of "int" matches argument type "object"  [call-overload]`
- `src/tunacode/core/agents/main.py:82: error: Expression has type "Any"  [misc]`

### Related type sources
- `src/tunacode/core/types/state.py:22-25`
  - `SessionStateProtocol.user_config: dict[str, Any]`
- `src/tunacode/core/agents/main.py:203-215`
  - `_initialize_request()` returns `_coerce_max_iterations(session)`

### Existing config-normalization code elsewhere
- `src/tunacode/core/agents/agent_components/agent_session_config.py:30-47`
  - `_coerce_int_setting(settings: Mapping[str, object], key: str, default: int) -> int`
- `src/tunacode/core/agents/agent_components/agent_session_config.py:78-99`
  - `_normalize_session_config(session: SessionStateProtocol) -> SessionConfig`
  - reads `session.user_config`, coerces `settings`, and derives typed values including `max_retries`

## Error group 2: tool callback args typing

### Location
- `src/tunacode/core/agents/main.py:469-470`

### Code present
- `src/tunacode/core/agents/main.py:469-470` defines:
  - `raw_callback_args = cast(object, state.runtime.tool_registry.get_args(tool_call_id))`
  - `callback_args = cast(dict[str, object], raw_callback_args or {})`

### Mypy output attached to this location
- `src/tunacode/core/agents/main.py:470: error: Expression type contains "Any" (has type "dict[Any, Any]")  [misc]`

### Immediate usage
- `src/tunacode/core/agents/main.py:471-476`
  - `callback_args` is passed to `self.tool_result_callback(...)`

### Related type sources
- `src/tunacode/core/types/tool_registry.py:121-125`
  - `get_args(self, tool_call_id: ToolCallId) -> ToolArgs | None`
- `src/tunacode/types/base.py:35`
  - `ToolArgs = dict[str, Any]`
- `src/tunacode/types/callbacks.py:55-58`
  - `ToolResultCallback` signature includes `ToolArgs`

### Related runtime flow
- `src/tunacode/core/agents/main.py:433-437`
  - tool start path registers args via `state.runtime.tool_registry.register(..., cast(dict[str, object], args))`
- `src/tunacode/core/agents/main.py:443-476`
  - tool end path reads args from `tool_registry.get_args(tool_call_id)` and forwards them to the callback

## Current error count summary
- 4 total mypy errors reported
- All 4 are in `src/tunacode/core/agents/main.py`
- Reported line grouping:
  - line `82`: 3 errors
  - line `470`: 1 error
