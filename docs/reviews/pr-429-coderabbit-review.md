---
title: PR 429 CodeRabbit Review Notes
summary: Review notes and merge recommendation for PR 429 and its CodeRabbit feedback.
when_to_read:
  - When reviewing PR 429 feedback
  - When checking the historical review outcome
last_updated: "2026-04-04"
---

# PR 429 CodeRabbit Review Notes

Date: 2026-03-16
PR: `#429 Refactor typed core agents boundaries`
Branch reviewed: `any-cleanup`
Source: local review of the PR diff and CodeRabbit comments

## Merge Recommendation

Do not merge in the current state.

## Blocking Issue

### Session-bound `Agent` is stored in the module-level cache

The refactor still stores a fully constructed `tinyagent.Agent` in the shared process cache keyed only by `model` and `agent_version`.

Relevant code:
- `src/tunacode/core/agents/agent_components/agent_config.py:471`
- `src/tunacode/core/agents/agent_components/agent_config.py:531`
- `src/tunacode/infrastructure/cache/caches/agents.py:16`

Why this blocks merge:
- `_build_agent_options()` captures `session.session_id`.
- `_build_agent_options()` captures `get_api_key=_build_api_key_resolver(config.env)`.
- `_build_agent_options()` captures `transform_context=_build_transform_context(state_manager)`.
- Those values are session-specific.
- `agents_cache` is still keyed only by `model` and `expected_version`.
- A later session can therefore reuse an `Agent` that was created for a different session.

Observed risk:
- wrong session ID attached to later requests
- wrong env/API-key resolution reused across sessions
- compaction context bound to the wrong `state_manager`

Required fix direction:
- either stop caching fully constructed session-bound `Agent` instances at module scope
- or include session identity and equivalent config identity in the cache key
- preferably cache only session-independent artifacts and instantiate the final `Agent` per session

## Non-Blocking But Real Issue

### `max_retries` and `tool_strict_validation` are dead config

The new typed config normalization introduces `AgentSettings.max_retries` and `AgentSettings.tool_strict_validation`, and both fields are included in `agent_version`.

Relevant code:
- `src/tunacode/core/agents/agent_components/agent_config.py:83`
- `src/tunacode/core/agents/agent_components/agent_config.py:168`
- `src/tunacode/core/agents/agent_components/agent_config.py:189`

Why this matters:
- changing these settings invalidates the cache
- but neither setting currently changes runtime behavior
- that creates config churn without semantic effect

Recommended follow-up:
- wire both settings into actual runtime behavior
- or remove them from the normalized config surface and `agent_version`

## Reviewed Comments I Would Not Block On

### `tool_callback` no-op

This is real API drift, but it appears to be pre-existing behavior rather than a regression introduced by this PR. The branch makes the no-op explicit by discarding the parameter in `src/tunacode/core/agents/main.py:117`.

### Abort cleanup / dangling tool state

The abort path still does not reconcile started tool calls before re-raising from `src/tunacode/core/agents/main.py:175`. That is worth addressing separately, but I would not attribute it specifically to this refactor without a dedicated reproducer.

## Validation Performed

The following checks passed on the PR branch during review:

- `uv run mypy src/tunacode/core/agents --show-error-codes --hide-error-context --no-error-summary`
- `uv run pytest tests/unit/test_sanitize_canonicalization.py tests/unit/core/test_thinking_stream_routing.py tests/unit/core/test_request_orchestrator_parallel_tools.py -q`
- `uv run pytest tests/test_dependency_layers.py tests/architecture/test_import_order.py tests/architecture/test_init_bloat.py -q`
