---
title: Models Registry Loading and Guardrails
link: models-registry-loading-and-guardrails
type: metadata
ontological_relations:
  - relates_to: [[kb-claude-code-touchpoints]]
tags:
  - models
  - registry
  - lazy-load
  - ui
  - guardrails
created_at: 2026-01-03T00:33:39Z
updated_at: 2026-01-03T00:34:17Z
uuid: 4559bd26-7d53-4f64-ac9d-bb96ec791539
---

# Overview

TunaCode ships a bundled `models_registry.json`, but the registry is not loaded at startup. The registry is only loaded when the user explicitly invokes model selection (for example, via `/model` or setup screens). This avoids surprise I/O and large enumerations that can feel like a "logic bomb" on first run.

# Load and Cache Semantics

- The registry is loaded from `src/tunacode/configuration/models_registry.json` by `load_models_registry`.
- The result is cached in `_models_registry_cache` and reused on subsequent calls.
- Callers that only need metadata (context window, pricing, env var, base URL) use the cache directly and return safe defaults when the registry is not loaded.

# Defaults When Registry Is Not Loaded

- `get_model_context_window`: returns `DEFAULT_CONTEXT_WINDOW` (200000).
- `get_model_pricing`: returns `None`, so cost calculations fall back to `0.0`.
- `get_provider_env_var`: falls back to `<PROVIDER>_API_KEY`.
- `get_provider_base_url`: returns `None`.

This keeps startup deterministic and avoids hidden background work. It also means exact pricing and context window limits are only available after the registry is loaded via `/model` or setup screens.

# UI Guardrails (Model/Provider Pickers)

To avoid auto-enumerating large registries, the pickers enforce a hard cap on unfiltered lists:

- `MODEL_PICKER_UNFILTERED_LIMIT` limits visible providers/models when no filter text is provided.
- A disabled notice row indicates that the list is truncated and that the user should type to filter.
- Filtering immediately lifts the cap for matched results, keeping the UI responsive.

# Touchpoints

- `src/tunacode/configuration/models.py`: registry loading, caching, and defaults.
- `src/tunacode/configuration/pricing.py`: pricing lookup now uses cached data only.
- `src/tunacode/ui/commands/__init__.py`: `/model` explicitly loads the registry.
- `src/tunacode/ui/screens/model_picker.py`: filter/limit guardrails.
- `src/tunacode/ui/screens/setup.py`: setup screens still load registry when shown.

# Operational Notes

- Registry updates are managed by `scripts/update_models_registry.sh`.
- If a future change fetches the registry over the network, keep the same explicit user-triggered behavior and time-bound the request to prevent hangs.
