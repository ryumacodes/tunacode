---
title: Configuration Layer
summary: User settings, model registry, path resolution, pricing tables, and ignore patterns.
read_when: Adding a new user-facing setting, supporting a new provider, or changing default behavior.
depends_on: [types, infrastructure]
feeds_into: [core, tools, ui]
---

# Configuration Layer

**Package:** `src/tunacode/configuration/`

## What

Everything that can be configured by the user or the project. This layer reads `tunacode.json`, resolves paths, loads the bundled model registry, and exposes typed accessors for limits, pricing, and ignore patterns.

Registry-backed metadata reads are lazy on a cold cache. Call sites that need provider env vars, provider base URLs, context windows, or pricing can read through the configuration accessors without preloading `models_registry.json` first.

## Key Files

| File | Purpose |
|------|---------|
| `defaults.py` | `DEFAULT_USER_CONFIG` dict -- the fallback for every setting. |
| `user_config.py` | `load_config()` reads `tunacode.json` from `~/.config/`. `load_config_with_defaults()` deep-merges user overrides onto defaults. |
| `settings.py` | `ApplicationSettings` dataclass -- app name, version, paths, internal tool list. `PathConfig` resolves `~/.config/tunacode.json`. |
| `models.py` | `load_models_registry()` parses `models_registry.json` (bundled) and populates the manual models-registry cache. `parse_model_string()` splits `"provider:model_id"`. Read helpers back lazy accessors such as `get_provider_env_var()`, `get_provider_base_url()`, `get_provider_alchemy_api()`, and `get_model_context_window()`. |
| `paths.py` | Session storage directory, project ID derivation, home-dir resolution. |
| `limits.py` | `get_max_tokens()` -- resolves the effective max output tokens from user config. |
| `pricing.py` | Registry-backed pricing lookup and cost formatting/calculation helpers. `get_model_pricing()` now reads through the same lazy registry path as the metadata accessors. |
| `ignore_patterns.py` | Built-in ignore defaults plus shared helpers for loading `.gitignore` rules, tolerating unreadable ignore files by falling back to defaults, and compiling reusable `pathspec` matchers. |

## Related Docs

- [`models-registry.md`](models-registry.md) -- contributor workflow for refreshing `models_registry.json` from models.dev and applying TunaCode-specific normalization rules.

## How

At startup, `StateManager.__init__()` calls `load_config_with_defaults()` to build the merged user config. This config dict is stored on `SessionState.user_config` and read by every other layer.

Model resolution flow:
1. `parse_model_string("openrouter:openai/gpt-4.1")` returns `("openrouter", "openai/gpt-4.1")`.
2. `get_provider_env_var("openrouter")` lazy-loads the registry on first access and returns `"OPENROUTER_API_KEY"`.
3. `get_provider_base_url("openrouter")` returns the API endpoint from the bundled registry without requiring a manual preload.
4. `get_model_context_window("openrouter:openai/gpt-4.1")` resolves the token limit through the same lazy read path.
5. `get_model_pricing("openrouter:openai/gpt-4.1")` resolves the pricing record from the same cached registry document.

## Why

Centralizing configuration avoids scattered `os.getenv()` calls. The bundled `models_registry.json` means users never need to know provider URLs or env-var names -- just pick a provider and model from the registry.
