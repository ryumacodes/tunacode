---
title: Type tinyagent stream_fn contract in agent config
type: delta
link: typed-stream-fn-contract
path: src/tunacode/core/agents/agent_components/agent_config.py
depth: 2
seams: [M]
ontological_relations:
  - affects: [[agent-config]]
  - affects: [[tinyagent-streaming]]
  - affects: [[tests]]
tags:
  - tinyagent
  - typing
  - stream-fn
  - provider
created_at: 2026-03-04T20:39:00+00:00
updated_at: 2026-03-04T20:39:00+00:00
uuid: 53336f15-6e33-4540-adad-7f2a819ecc39
---

# Type tinyagent stream_fn contract in agent config

## Summary

Updated agent stream wiring to use tinyagent's typed stream contracts end-to-end.

- `_build_stream_fn` now returns `StreamFn` instead of a variadic `Callable[..., Awaitable[Any]]`.
- Stream callback parameters are typed as `Model`, `Context`, and `SimpleStreamOptions`.
- Added `_merge_stream_options(...)` to copy options with `model_copy(update={...})` when applying TunaCode `max_tokens`.
- Removed dict-based options mutation from the agent stream path.

## Test updates

Aligned stream mocks with tinyagent's typed contracts in tests:

- `tests/unit/core/test_tinyagent_openrouter_model_config.py`
  - `_build_stream_fn` test now passes/inspects `SimpleStreamOptions` models.
- `tests/integration/core/test_minimax_execution_path.py`
  - Mock stream now yields `AssistantMessageEvent(type="done")` and returns `AssistantMessage`.
  - Options assertion now checks typed `SimpleStreamOptions.api_key`.

## Validation

- `uv run ruff check .` ✅
- `uv run pytest tests/unit/core/test_tinyagent_openrouter_model_config.py tests/integration/core/test_minimax_execution_path.py -q` ✅ (16 passed)
