---
title: "models loading conflict map research findings"
link: "models-loading-conflict-map-research"
type: research
ontological_relations:
  - relates_to: [[configuration]]
tags: [research, models-loading, configuration]
uuid: "ae8023dd-5fc6-4613-8684-f6046e81a089"
created_at: "2026-03-26T20:29:05.588172+00:00"
---

## Structure

- Relevant directories and file counts (maxdepth=1):
  - `src/tunacode/configuration` (10 files)
  - `src/tunacode/core/ui_api` (10 files)
  - `src/tunacode/core/agents/agent_components` (4 files)
  - `src/tunacode/core/compaction` (5 files)
  - `src/tunacode/core/session` (2 files)
  - `src/tunacode/infrastructure/cache/caches` (6 files)
  - `src/tunacode/ui/commands` (14 files)
  - `src/tunacode/ui/screens` (7 files)
  - `tests/unit/configuration` (5 files)
  - `tests/unit/infrastructure` (4 files)
  - `tests/unit/core` (20 files)

- Research script availability check:
  - `scripts/structure-map.sh` -> missing (`/bin/bash: ... No such file or directory`)
  - `scripts/ast-scan.sh` -> missing (`/bin/bash: ... No such file or directory`)
  - `scripts/symbol-index.sh` -> missing (`/bin/bash: ... No such file or directory`)

## Key Files

- Registry loader and accessor module:
  - `src/tunacode/configuration/models.py:69` → `load_models_registry()`
  - `src/tunacode/configuration/models.py:75` → reads cache via `models_registry_cache.get_registry()`
  - `src/tunacode/configuration/models.py:82` → registry path resolved to `models_registry.json`
  - `src/tunacode/configuration/models.py:89` → writes cache via `models_registry_cache.set_registry(...)`
  - `src/tunacode/configuration/models.py:93` → `get_cached_models_registry()`
  - `src/tunacode/configuration/models.py:207` → `get_provider_env_var()` (cache-dependent fallback)
  - `src/tunacode/configuration/models.py:250` → `get_provider_base_url()` (cache-dependent)
  - `src/tunacode/configuration/models.py:267` → `get_provider_alchemy_api()` (cache-dependent)
  - `src/tunacode/configuration/models.py:285` → `get_model_context_window()` (cache-dependent with default fallback)

- Cache registration and storage:
  - `src/tunacode/infrastructure/cache/caches/models_registry.py:7` → cache name `tunacode.models.registry`
  - `src/tunacode/infrastructure/cache/caches/models_registry.py:10` → cache registered with `ManualStrategy`
  - `src/tunacode/infrastructure/cache/caches/models_registry.py:13` → typed `get_registry()`
  - `src/tunacode/infrastructure/cache/caches/models_registry.py:23` → typed `set_registry()`
  - `src/tunacode/infrastructure/cache/manager.py:115` → `CacheManager.clear_all()` clears all registered caches

- UI/core facade wrappers:
  - `src/tunacode/core/ui_api/configuration.py:68` → wrapper `load_models_registry()`
  - `src/tunacode/core/ui_api/configuration.py:58` → wrapper `get_provider_env_var()`
  - `src/tunacode/core/ui_api/configuration.py:73` → wrapper `get_model_context_window()`

- Runtime call sites that explicitly load registry before provider metadata lookup:
  - `src/tunacode/core/agents/agent_components/agent_config.py:276` → `_resolve_base_url()` calls `load_models_registry()` before `get_provider_base_url(...)`
  - `src/tunacode/core/agents/agent_components/agent_config.py:529` → `get_or_create_agent()` calls `load_models_registry()` during init
  - `src/tunacode/core/compaction/controller.py:400` → `_resolve_base_url()` calls `load_models_registry()`
  - `src/tunacode/core/compaction/controller.py:427` → `_resolve_api_key()` calls `load_models_registry()`
  - `src/tunacode/ui/commands/model.py:77` → `_handle_direct_model_selection()` calls `load_models_registry()`

- Runtime call sites using cache-dependent context lookup without local `load_models_registry()` call:
  - `src/tunacode/core/session/state.py:99` → initialization path uses `get_model_context_window(...)`
  - `src/tunacode/core/session/state.py:383` → session-load path uses `get_model_context_window(...)`
  - `src/tunacode/configuration/pricing.py:19` → `get_model_pricing(...)` starts from `get_cached_models_registry()`

- Registry source and normalization script:
  - `scripts/update_models_registry.sh:7` → downloads from `https://models.dev/api.json`
  - `scripts/update_models_registry.sh:56` → `MINIMAX_PROVIDER_CONTRACTS`
  - `scripts/update_models_registry.sh:128` → sets provider `env`
  - `scripts/update_models_registry.sh:129` → sets provider `alchemy_api`
  - `scripts/update_models_registry.sh:130` → sets provider `api`

- Bundled registry entries (MiniMax contract lines):
  - `src/tunacode/configuration/models_registry.json:18253` → `minimax-cn-coding-plan`
  - `src/tunacode/configuration/models_registry.json:18256` → env `MINIMAX_CN_API_KEY`
  - `src/tunacode/configuration/models_registry.json:18440` → alchemy_api `minimax-completions`
  - `src/tunacode/configuration/models_registry.json:28805` → `minimax-cn`
  - `src/tunacode/configuration/models_registry.json:28808` → env `MINIMAX_CN_API_KEY`
  - `src/tunacode/configuration/models_registry.json:28992` → alchemy_api `minimax-completions`
  - `src/tunacode/configuration/models_registry.json:37126` → `minimax-coding-plan`
  - `src/tunacode/configuration/models_registry.json:37129` → env `MINIMAX_API_KEY`
  - `src/tunacode/configuration/models_registry.json:37313` → alchemy_api `minimax-completions`
  - `src/tunacode/configuration/models_registry.json:78438` → `minimax`
  - `src/tunacode/configuration/models_registry.json:78441` → env `MINIMAX_API_KEY`
  - `src/tunacode/configuration/models_registry.json:78625` → alchemy_api `minimax-completions`

- Test coverage around registry/cache/env-var behavior:
  - `tests/unit/configuration/test_models_registry_minimax_contract.py:14` → env contract assertions (after load)
  - `tests/unit/configuration/test_models_registry_minimax_contract.py:23` → alchemy contract assertions (after load)
  - `tests/unit/configuration/test_provider_api_key_env_fallback.py:8` → config/env fallback behavior
  - `tests/unit/infrastructure/test_migrated_lru_cache_replacements.py:23` → registry cache clears with `clear_all()`
  - `tests/unit/core/test_tinyagent_openrouter_model_config.py:141` → api-key resolver MiniMax CN behavior

## Patterns Found

- Pattern: cache-first registry load in configuration module
  - `src/tunacode/configuration/models.py:69-90`
  - `src/tunacode/infrastructure/cache/caches/models_registry.py:13-24`

- Pattern: load-on-read accessors
  - `get_providers()` -> `load_models_registry()` at `src/tunacode/configuration/models.py:99-106`
  - `get_models_for_provider()` -> `load_models_registry()` at `src/tunacode/configuration/models.py:109-122`
  - `get_model_picker_entries()` -> `load_models_registry()` at `src/tunacode/configuration/models.py:125-153`

- Pattern: cache-only accessors with fallback behavior when cache is empty
  - `get_provider_env_var()` fallback string at `src/tunacode/configuration/models.py:216-224`
  - `get_provider_base_url()` returns `None` when cache is empty at `src/tunacode/configuration/models.py:259-264`
  - `get_provider_alchemy_api()` returns `None` when cache is empty at `src/tunacode/configuration/models.py:269-282`
  - `get_model_context_window()` returns `DEFAULT_CONTEXT_WINDOW` when cache is empty at `src/tunacode/configuration/models.py:295-297`

- Pattern: wrapper pass-through layer
  - `src/tunacode/core/ui_api/configuration.py:43-100` re-exports/wraps configuration functions

- Pattern: explicit preload before provider resolution in agent and compaction paths
  - `src/tunacode/core/agents/agent_components/agent_config.py:269-277`
  - `src/tunacode/core/agents/agent_components/agent_config.py:527-529`
  - `src/tunacode/core/compaction/controller.py:387-401`
  - `src/tunacode/core/compaction/controller.py:426-428`

- Pattern: state initialization uses context-window lookup directly
  - `src/tunacode/core/session/state.py:83-100`
  - `src/tunacode/core/session/state.py:348-384`

- Observed runtime probe (cache-cleared vs loaded; command run via `uv run python`):
  - before load:
    - `get_provider_env_var("minimax-coding-plan")` -> `MINIMAX_CODING_PLAN_API_KEY`
    - `get_provider_env_var("minimax-cn-coding-plan")` -> `MINIMAX_CN_CODING_PLAN_API_KEY`
    - `get_model_context_window("minimax-coding-plan:MiniMax-M2.1")` -> `200000`
  - after `load_models_registry()`:
    - `get_provider_env_var("minimax-coding-plan")` -> `MINIMAX_API_KEY`
    - `get_provider_env_var("minimax-cn-coding-plan")` -> `MINIMAX_CN_API_KEY`
    - `get_model_context_window("minimax-coding-plan:MiniMax-M2.1")` -> `204800`

- Observed runtime probe for default model context value:
  - model from defaults: `openrouter:openai/gpt-4.1`
  - before load: `200000`
  - after `load_models_registry()`: `1047576`

## Dependencies

- `src/tunacode/configuration/models.py` direct imports:
  - `src/tunacode/configuration/models.py:10` -> `tunacode.constants` (`DEFAULT_CONTEXT_WINDOW`, `MODEL_PICKER_UNFILTERED_LIMIT`)
  - `src/tunacode/configuration/models.py:12` -> `tunacode.infrastructure.cache.caches.models_registry`
  - local imports inside functions:
    - `src/tunacode/configuration/models.py:79` -> `json`
    - `src/tunacode/configuration/models.py:80` -> `pathlib.Path`
    - `src/tunacode/configuration/models.py:239` -> `os`

- Reverse imports of `tunacode.configuration.models`:
  - `src/tunacode/configuration/pricing.py:3`
  - `src/tunacode/core/agents/agent_components/agent_config.py:31`
  - `src/tunacode/core/compaction/controller.py:20`
  - `src/tunacode/core/session/state.py:86,350`
  - `src/tunacode/core/ui_api/configuration.py:6,9,12,15,18,21,24,27,30`

- Internal call relationships inside `models.py`:
  - `load_models_registry()` -> cache `get_registry()`/`set_registry()`
  - `get_providers()` -> `load_models_registry()`
  - `get_models_for_provider()` -> `load_models_registry()`
  - `get_model_picker_entries()` -> `load_models_registry()`
  - `get_provider_env_var()` -> `get_cached_models_registry()`
  - `validate_provider_api_key()` -> `get_provider_env_var()`
  - `get_provider_base_url()` -> `get_cached_models_registry()`
  - `get_provider_alchemy_api()` -> `get_cached_models_registry()`
  - `get_model_context_window()` -> `get_cached_models_registry()`, `parse_model_string()`

- `load_models_registry()` call sites across source:
  - `src/tunacode/configuration/models.py:69,104,118,127`
  - `src/tunacode/core/agents/agent_components/agent_config.py:276,529`
  - `src/tunacode/core/compaction/controller.py:400,427`
  - `src/tunacode/core/ui_api/configuration.py:68,70`
  - `src/tunacode/ui/commands/model.py:77`

## Symbol Index

- `src/tunacode/configuration/models.py`
  - `ModelPickerEntry` dataclass at `:20`
    - fields: `full_model` (`:23`), `provider_id` (`:24`), `provider_name` (`:25`), `model_id` (`:26`), `model_name` (`:27`)
  - functions:
    - `_build_model_search_text` `:30`
    - `_matches_model_query` `:42`
    - `parse_model_string` `:51`
    - `load_models_registry` `:69`
    - `get_cached_models_registry` `:93`
    - `get_providers` `:99`
    - `get_models_for_provider` `:109`
    - `get_model_picker_entries` `:125`
    - `rank_model_picker_entries` `:156`
    - `get_provider_env_var` `:207`
    - `validate_provider_api_key` `:227`
    - `get_provider_base_url` `:250`
    - `get_provider_alchemy_api` `:267`
    - `get_model_context_window` `:285`

- `src/tunacode/core/ui_api/configuration.py` wrappers:
  - `get_models_for_provider` `:43`
  - `get_model_picker_entries` `:48`
  - `get_providers` `:53`
  - `get_provider_env_var` `:58`
  - `validate_provider_api_key` `:63`
  - `load_models_registry` `:68`
  - `get_model_context_window` `:73`
  - `rank_model_picker_entries` `:78`
  - `get_model_pricing` `:94`
  - `format_pricing_display` `:99`

- Registry cache accessor symbols (`src/tunacode/infrastructure/cache/caches/models_registry.py`):
  - constants: `MODELS_REGISTRY_CACHE_NAME` `:7`, `MODELS_REGISTRY_KEY` `:8`
  - functions: `get_registry` `:13`, `set_registry` `:23`, `clear_registry_cache` `:27`
