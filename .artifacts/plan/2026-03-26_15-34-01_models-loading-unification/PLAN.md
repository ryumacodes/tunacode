---
title: "models-loading-unification implementation plan"
link: "models-loading-unification-plan"
type: implementation_plan
ontological_relations:
  - relates_to: [[models-loading-conflict-map-research]]
tags: [plan, models-loading-unification, coding]
uuid: "b6aa9eea-3a21-4a1f-a083-2c14e0c1ccdc"
created_at: "2026-03-26T20:34:05.921350+00:00"
parent_research: ".artifacts/research/2026-03-26_15-29-02_models-loading-conflict-map.md"
git_commit_at_plan: "3dc47ef3"
---

## Goal

Unify model-registry loading so all metadata lookups (env var, base URL, alchemy API, pricing, context window) behave consistently on cold cache without requiring call-site preloads.

Out of scope: deployment workflow changes, provider contract redesign, broad refactors outside model-registry access paths, or multi-provider feature additions.

## Scope & Assumptions

- IN scope:
  - Add a single internal loading mechanism for registry-backed reads.
  - Define a typed schema for the bundled `models_registry.json` document and use it for registry loader/cache signatures.
  - Refactor cache-only accessors to use the unified mechanism.
  - Remove redundant explicit `load_models_registry()` preloads where no longer needed.
  - Add focused regression tests for cold-cache behavior.
- OUT of scope:
  - Changing bundled registry source generation logic in `scripts/update_models_registry.sh`.
  - UI redesign or command UX changes.
  - Performance benchmarking beyond existing unit-level assertions.
- Assumptions:
  - `models_registry.json` remains bundled and valid JSON dict.
  - Existing cache manager semantics (`clear_all`) remain authoritative.
  - Normal metadata reads should lazy-load registry data on demand.
  - `get_cached_models_registry()` remains cache-only and must not trigger a load.
  - `DEFAULT_CONTEXT_WINDOW` remains the fallback only for invalid model strings/missing model metadata.

## Deliverables

- Typed registry schema in the `types` layer for `models_registry.json`.
- Unified registry-read path in configuration modules.
- Updated runtime call sites aligned with unified loading semantics.
- Regression tests proving cold-cache consistency.
- Minimal developer-facing notes inline in code comments/docstrings where behavior changes.

## Implementation Contract

- Registry shape must be typed:
  - add a dedicated registry schema type for the bundled JSON document
  - use typed registry return values for loader/cache/facade functions instead of `dict[str, Any]`
  - do not add new ad-hoc `Any`-based wrappers around registry payloads
- Normal read paths must auto-load:
  - `get_provider_env_var`
  - `get_provider_base_url`
  - `get_provider_alchemy_api`
  - `get_model_context_window`
  - `get_model_pricing`
- Cache inspection stays cache-only:
  - `get_cached_models_registry()` must not load the registry.
- Preserve fallback behavior:
  - unknown provider env var -> derive `PROVIDER_API_KEY` from provider id
  - missing provider base URL -> `None`
  - missing provider alchemy API -> `None`
  - invalid model string or missing context limit -> `DEFAULT_CONTEXT_WINDOW`
  - missing pricing data -> `None`
- Explicit preload cleanup decision:
  - remove correctness preloads from `agent_config._resolve_base_url`
  - remove correctness preloads from `CompactionController._resolve_base_url`
  - remove correctness preloads from `CompactionController._resolve_api_key`
  - remove correctness preloads from `ModelCommand._handle_direct_model_selection`
  - keep `load_models_registry()` in `agent_config.get_or_create_agent()` for now; it remains an intentional init warmup/logging hook and is not part of this cleanup

## Readiness

- Preconditions:
  - Research artifact exists: `.artifacts/research/2026-03-26_15-29-02_models-loading-conflict-map.md`.
  - Bundled registry file exists: `src/tunacode/configuration/models_registry.json`.
  - Unit test suite runnable via `uv run pytest`.
- Must exist before start:
  - Current cache API in `src/tunacode/infrastructure/cache/caches/models_registry.py`.
  - Current accessors in `src/tunacode/configuration/models.py` and `src/tunacode/configuration/pricing.py`.

## Milestones

- M1: Keep a single unified registry access helper for normal read paths, add typed registry schema, and preserve cache semantics.
- M2: Migrate metadata/pricing/context accessors to unified helper.
- M3: Align runtime call sites and remove redundant preload coupling.
- M4: Add regression tests for cold-cache correctness and integration touchpoints.

## Ticket Index

<!-- TICKET_INDEX:START -->

| Task | Title | Ticket |
|---|---|---|
| T001 | Add a single internal registry accessor for read paths | [tickets/T001.md](tickets/T001.md) |
| T002 | Refactor registry-dependent metadata and pricing lookups to the unified loader | [tickets/T002.md](tickets/T002.md) |
| T003 | Remove redundant preload coupling from runtime call sites | [tickets/T003.md](tickets/T003.md) |
| T004 | Add targeted cold-cache regression coverage for session and pricing paths | [tickets/T004.md](tickets/T004.md) |

<!-- TICKET_INDEX:END -->

## Work Breakdown (Tasks)

### T001: Add a single internal registry accessor for read paths

**Summary**: Use the private helper in `models.py` as the only internal load-backed registry accessor for normal read operations, and formalize the registry JSON shape with typed schema definitions.

**Owner**: backend

**Estimate**: 1.5h

**Dependencies**: none

**Target milestone**: M1

**Acceptance test**: `uv run pytest tests/unit/infrastructure/test_migrated_lru_cache_replacements.py::test_models_registry_cache_clears_via_clear_all -q`

**Files/modules touched**:
- src/tunacode/configuration/models.py
- src/tunacode/infrastructure/cache/caches/models_registry.py
- src/tunacode/types/models_registry.py
- src/tunacode/types/__init__.py
- src/tunacode/types/dataclasses.py

**Steps**:
1. Use the existing private helper `_get_registry_for_read()` in `models.py` as the single internal load-backed entry point for normal registry reads. Do not add a second helper.
2. Add a dedicated typed schema for the bundled registry document in the `types` layer. The schema should represent the real JSON structure used by provider and model entries, including `models`, `env`, `api`, `alchemy_api`, `limit`, and `cost`.
3. Update registry cache and loader signatures to return the typed registry document instead of `dict[str, Any]`.
4. Remove the stale unused `ModelRegistry` alias that does not describe the real bundled JSON document.
5. Keep `get_cached_models_registry()` behavior unchanged for explicit cache-only callers.
6. Keep cache clearing semantics unchanged: `clear_all()` must still empty the models registry cache.

### T002: Refactor registry-dependent metadata and pricing lookups to the unified loader

**Summary**: Migrate cache-dependent accessors so cold-cache reads return registry-backed values instead of fallback-only values when registry data exists.

**Owner**: backend

**Estimate**: 2h

**Dependencies**: T001

**Target milestone**: M2

**Acceptance test**: `uv run pytest tests/unit/configuration/test_models_registry_minimax_contract.py tests/unit/configuration/test_models_registry_loading_behavior.py -q`

**Files/modules touched**:
- src/tunacode/configuration/models.py
- src/tunacode/configuration/pricing.py
- src/tunacode/core/ui_api/configuration.py
- tests/unit/configuration/test_provider_api_key_env_fallback.py
- tests/unit/configuration/test_models_registry_minimax_contract.py
- tests/unit/configuration/test_models_registry_loading_behavior.py

**Steps**:
1. Refactor `get_provider_env_var`, `get_provider_base_url`, `get_provider_alchemy_api`, and `get_model_context_window` to use `_get_registry_for_read()`.
2. Refactor `get_model_pricing` in `pricing.py` to use the same load-backed contract. Do not add a second registry-loading implementation.
3. Use the typed registry schema in these accessors instead of raw `dict[str, Any]` access where practical. Helper functions for looking up provider/model entries are acceptable if they keep the code smaller and clearer.
4. Preserve fallback behavior exactly:
   - unknown provider env var still derives from provider id
   - missing base URL or alchemy API still returns `None`
   - invalid model string or missing context limit still returns `DEFAULT_CONTEXT_WINDOW`
   - missing pricing still returns `None`
5. Create `tests/unit/configuration/test_models_registry_loading_behavior.py` and add explicit cold-cache assertions:
   - `get_provider_env_var("minimax-coding-plan") == "MINIMAX_API_KEY"`
   - `get_provider_alchemy_api("minimax-coding-plan") == "minimax-completions"`
   - `get_model_context_window("minimax-coding-plan:MiniMax-M2.1") == 204800`
   - `get_model_pricing("openrouter:openai/gpt-4.1")` returns `input=2`, `cached_input=0.5`, `output=8`
6. Keep `tests/unit/configuration/test_models_registry_minimax_contract.py` as the normalized-contract test and use the new file for cold-cache behavior.

### T003: Remove redundant preload coupling from runtime call sites

**Summary**: Simplify runtime paths by removing explicit preload calls that were previously required for correctness, while keeping behavior stable.

**Owner**: backend

**Estimate**: 1.5h

**Dependencies**: T002

**Target milestone**: M3

**Acceptance test**: `uv run pytest tests/unit/core/test_tinyagent_openrouter_model_config.py -q`

**Files/modules touched**:
- src/tunacode/core/agents/agent_components/agent_config.py
- src/tunacode/core/compaction/controller.py
- src/tunacode/ui/commands/model.py

**Steps**:
1. Remove `load_models_registry()` from `agent_config._resolve_base_url()`.
2. Remove `load_models_registry()` from `CompactionController._resolve_base_url()` and `CompactionController._resolve_api_key()`.
3. Remove `load_models_registry()` from `ModelCommand._handle_direct_model_selection()`.
4. Keep `load_models_registry()` in `agent_config.get_or_create_agent()` for now. It remains an intentional init warmup/logging hook and is not part of this cleanup.
5. Do not add any new preload to `StateManager`; first-read correctness there must come from load-backed accessors, not caller preloading.
6. Update any affected inline comments to describe the lazy-load contract.

### T004: Add targeted cold-cache regression coverage for session and pricing paths

**Summary**: Add focused tests proving that first-read behavior is correct without manual preload in state initialization and pricing lookup.

**Owner**: backend

**Estimate**: 2h

**Dependencies**: T002,T003

**Target milestone**: M4

**Acceptance test**: `uv run pytest tests/unit/core/test_session_state_model_registry_loading.py tests/unit/configuration/test_pricing_registry_loading.py -q`

**Files/modules touched**:
- tests/unit/core/test_session_state_model_registry_loading.py
- tests/unit/configuration/test_pricing_registry_loading.py

**Steps**:
1. Create `tests/unit/core/test_session_state_model_registry_loading.py`.
2. In the session test, isolate user config by patching `HOME` to a temp directory before constructing `StateManager()`. `Path.home() / ".config"` is the config source used by `ApplicationSettings`, so patching `XDG_DATA_HOME` alone is not sufficient.
3. In the session test, call `clear_all()` before construction and assert:
   - `state_manager.session.current_model == "openrouter:openai/gpt-4.1"`
   - `state_manager.session.conversation.max_tokens == 1047576`
4. Create `tests/unit/configuration/test_pricing_registry_loading.py`.
5. In the pricing test, call `clear_all()` and assert `get_model_pricing("openrouter:openai/gpt-4.1")` succeeds on cold cache with `input=2`, `cached_input=0.5`, `output=8`.
6. Keep both tests isolated with explicit cache clearing before and after to avoid order-dependent behavior.
7. Do not modify source files in this ticket unless a failing test proves an unresolved T002/T003 bug.

## Risks & Mitigations

- Risk: eager loading in new paths could mask invalid registry file errors at different call timing.
  - Mitigation: keep failure mode explicit via existing `TypeError`/JSON loading behavior and test first-read paths.
- Risk: typed schema drifts from the real bundled JSON shape.
  - Mitigation: define the schema from the actual `models_registry.json` fields used in production code and keep it scoped to the fields TunaCode actually reads.
- Risk: hidden callers may rely on previous fallback strings/`None` values when cache is empty.
  - Mitigation: constrain change to the accessors listed in the implementation contract and keep fallback behavior explicit in tests.
- Risk: cache lifecycle regressions after refactor.
  - Mitigation: keep `clear_all` regression test as gate and avoid cache-manager API changes.
- Risk: junior implementer removes the wrong preload.
  - Mitigation: T003 now names each preload call to remove and the one preload to keep.
- Risk: session-state test reads the real user config.
  - Mitigation: T004 requires patching `HOME` to a temp directory before constructing `StateManager()`.

## Test Strategy

- One primary validation per task (as listed in each ticket acceptance test).
- Add at most one new focused test file per subsystem touched (configuration, core/session).
- Prioritize cold-cache first-read behavior and deterministic results for known MiniMax/openrouter fixtures.
- Use exact assertion values for MiniMax env/alchemy/context and OpenRouter pricing/context so the tests do not depend on vague “truthy” checks.
- After touching `src/`, run `uv run python scripts/check_agents_freshness.py`.

## References

- `.artifacts/research/2026-03-26_15-29-02_models-loading-conflict-map.md`
- `src/tunacode/configuration/models.py` (`load_models_registry`, `_get_registry_for_read`, provider/context accessors)
- `src/tunacode/configuration/pricing.py` (`get_model_pricing`)
- `src/tunacode/types/models_registry.py` (typed registry document schema)
- `src/tunacode/core/session/state.py` (`_load_user_configuration`, `load_session`)
- `src/tunacode/core/agents/agent_components/agent_config.py` (`_resolve_base_url`, `get_or_create_agent`)
- `src/tunacode/core/compaction/controller.py` (`_resolve_base_url`, `_resolve_api_key`)
- `src/tunacode/ui/commands/model.py` (`_handle_direct_model_selection`)
- `src/tunacode/configuration/settings.py` (`ApplicationSettings.paths.config_file`)

## Final Gate

- **Output summary**: `.artifacts/plan/2026-03-26_15-34-01_models-loading-unification/`, milestones=4, tickets=4
- **Required checks before handoff**:
  - `uv run pytest tests/unit/infrastructure/test_migrated_lru_cache_replacements.py::test_models_registry_cache_clears_via_clear_all -q`
  - task acceptance tests listed in each ticket
  - `uv run python scripts/check_agents_freshness.py`
- **Next step**: proceed to execute-phase with `.artifacts/plan/2026-03-26_15-34-01_models-loading-unification/PLAN.md`
