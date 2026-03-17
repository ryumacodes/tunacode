---
title: Consolidate main_support.py into main.py
type: plan
ontological_relations:
  - relation: depends_on
    target: agents-core-module
    note: Changes are localized to the agents/core package.
  - relation: validated_by
    target: test-request-orchestrator
    note: Tests in test_request_orchestrator_parallel_tools.py cover the affected code.
tags:
  - refactor
  - maintainability
  - code-health
  - consolidation
  - cleanup
created_at: 2026-03-17T11:40:00-05:00
updated_at: 2026-03-17T11:40:00-05:00
uuid: 8a2f3b4c-5d6e-7f8a-9b0c-1d2e3f4a5b6c
---

# Goal
Move all functionality from deleted `main_support.py` into appropriate locations, eliminating the unnecessary module boundary since `main_support.py` was only used by `main.py`.

## Items to relocate from main_support.py

| Item | Type | Purpose | Target Location |
|------|------|---------|-----------------|
| `EmptyResponseHandler` | Class | Handles empty response tracking/intervention | `main.py` (private class) |
| `coerce_runtime_config()` | Function | Gets max_iterations, debug_metrics from user config | `main.py` (private function) |
| `coerce_tool_callback_args()` | Function | Validates tool callback args | `main.py` (private function) |
| `log_tool_execution_end()` | Function | Logs tool completion | `main.py` (private function) |
| `log_tool_execution_start()` | Function | Logs tool start | `main.py` (private function) |
| `normalize_tool_event_args()` | Function | Validates tool event args | `main.py` (private function) |
| `StreamLifecycleState` | Protocol | Type for stream lifecycle state | `core/types/state.py` or `main.py` |
| `_EmptyResponseStateView` | Class | Internal view for empty response handling | `main.py` (private class) |
| `TOOL_EXECUTION_LIFECYCLE_PREFIX` | Constant | Log prefix for tool execution | `main.py` (local constant) |
| `PARALLEL_TOOL_CALLS_LIFECYCLE_PREFIX` | Constant | Log prefix for parallel calls | `main.py` (local constant) |
| `DURATION_NOT_AVAILABLE_LABEL` | Constant | "n/a" label for missing duration | `main.py` (local constant) |

## Plan

1. **Remove broken import**
   - Delete the `from .main_support import (...)` line in `main.py`

2. **Inline helper functions into main.py**
   - Add all functions as private helpers (prefixed with `_`)
   - Keep `coerce_runtime_config()` returning `tuple[int, bool]`
   - Keep constants as module-level constants in `main.py`

3. **Move StreamLifecycleState**
   - Option A: Add to `main.py` as `_StreamLifecycleState`
   - Option B: Move to `tunacode/core/types/state.py` if used elsewhere

4. **Update EmptyResponseHandler**
   - Inline the class into `main.py` as `_EmptyResponseHandler`
   - Inline `_EmptyResponseStateView` as well

5. **Validate**
   - Run tests: `tests/unit/core/test_request_orchestrator_parallel_tools.py`
   - Run tests: `tests/unit/core/test_thinking_stream_routing.py`
   - Ensure no regressions

## Implementation rules
- Keep all functions private (underscore prefix) since they're implementation details
- Preserve existing behavior exactly
- Do not increase public API surface
- File will exceed 600 lines (already 729 lines) — acceptable as temporary debt

## Done criteria
- `main_support.py` is deleted (already done)
- `main.py` imports work correctly
- All 6 functions/classes are available in `main.py`
- Tests pass
- No `ModuleNotFoundError` for main_support
