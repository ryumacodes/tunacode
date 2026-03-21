# Model Registry Refresh And Release Blocker Report

Created: 2026-03-21
Scope: `src/tunacode/configuration/models_registry.json` refresh, release preflight, and follow-up fix.

## Summary

A fresh pull from `models.dev` regenerated TunaCode's bundled model registry, but the raw upstream data drifted from TunaCode's MiniMax routing contract.

The refresh script preserved Anthropic-style MiniMax provider base URLs:

- `https://api.minimax.io/anthropic/v1`
- `https://api.minimaxi.com/anthropic/v1`

TunaCode's runtime expects MiniMax providers to use:

- OpenAI-compatible `api` routing via `alchemy_api = "minimax-completions"`
- OpenAI-compatible chat completions base URLs:
  - `https://api.minimax.io/v1`
  - `https://api.minimaxi.com/v1`

That mismatch caused the refreshed registry to generate incorrect chat-completions endpoints such as:

- `https://api.minimax.io/anthropic/v1/chat/completions`

instead of:

- `https://api.minimax.io/v1/chat/completions`

## What Failed

### 1. Real regression from the registry refresh

Release preflight exposed a MiniMax execution-path failure:

- Test: `tests/integration/core/test_minimax_execution_path.py`
- Failure: expected MiniMax chat completions URL did not match the regenerated registry output

Observed mismatch:

- actual: `https://api.minimax.io/anthropic/v1/chat/completions`
- expected: `https://api.minimax.io/v1/chat/completions`

### 2. Release gate remained unsafe

After fixing the MiniMax contract and regenerating the registry, targeted validation passed, but the mandatory full release gate still was not clean in full-suite execution.

Persistent blocker seen during the full-suite run:

- `tests/system/cli/test_tmux_tools.py::test_loaded_skill_is_used_via_absolute_referenced_path`

Important detail:

- the tmux test file passes in isolation
- the failure appears in full-suite context, which makes it a flaky or suite-interaction problem
- because the release skill requires a clean validation gate, the PyPI release was intentionally not executed

## Root Cause

The refresh workflow only normalized MiniMax `env` and `alchemy_api` fields. It did not also normalize MiniMax `api` fields back to TunaCode's OpenAI-compatible `/v1` endpoints after the upstream registry changed shape.

In short:

1. upstream registry changed MiniMax provider `api` values
2. TunaCode refresh script downloaded those values
3. TunaCode kept `alchemy_api = "minimax-completions"`
4. runtime appended `/chat/completions` to the upstream Anthropic-style base URL
5. resulting request URL no longer matched TunaCode's MiniMax contract

## Fix Applied

Updated `scripts/update_models_registry.sh` so `MINIMAX_PROVIDER_CONTRACTS` now pins all MiniMax variants to three required fields together:

- `env`
- `alchemy_api`
- OpenAI-compatible `api`

Updated documentation in:

- `docs/modules/configuration/models-registry.md`

Regenerated:

- `src/tunacode/configuration/models_registry.json`

## Validation Run

Passed:

- `uv run ruff check .`
- `uv run python scripts/check_agents_freshness.py`
- `uv run pytest tests/integration/core/test_minimax_execution_path.py -q`
- `uv run pytest tests/unit/configuration/test_models_registry_minimax_contract.py tests/unit/core/test_tinyagent_openrouter_model_config.py -q`
- `uv run pytest tests/system/cli/test_startup.py -vv`
- `uv run pytest tests/system/cli/test_tmux_tools.py -v -m tmux --timeout=0`

Blocked full release gate:

- `uv run pytest tests/ -q --timeout=0`
- failure observed at `tests/system/cli/test_tmux_tools.py::test_loaded_skill_is_used_via_absolute_referenced_path`

## Why No PyPI Release Was Cut

The release skill requires a clean validation run before version bump, tag, push, GitHub release, and publish.

Because the full release gate still showed a tmux-system-test failure in suite context, the release was stopped before:

- version bump
- changelog entry
- tag creation
- GitHub release
- PyPI publication

## Secret Handling

No API keys, tokens, or secret values are included in this artifact.

This report intentionally omits:

- real environment variable contents
- API key values used in local validation
- any serialized secret-bearing session data

Only symbolic env-var names are referenced, for example `MINIMAX_API_KEY`.

## Files Changed In The Follow-Up Fix

- `scripts/update_models_registry.sh`
- `docs/modules/configuration/models-registry.md`
- `src/tunacode/configuration/models_registry.json`

## Recommended Next Step

Investigate the full-suite-only tmux failure in `test_loaded_skill_is_used_via_absolute_referenced_path` before attempting the PyPI release flow again.
