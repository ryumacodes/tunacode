---
title: Core Configuration Facade
path: src/tunacode/core/configuration.py
type: file
depth: 1
description: Core-layer access to configuration defaults, models, and pricing helpers
exports: [ApplicationSettings, DEFAULT_USER_CONFIG, get_providers, get_models_for_provider, get_provider_env_var, validate_provider_api_key, load_models_registry, get_model_context_window, get_model_pricing, format_pricing_display]
seams: [M]
---

# Core Configuration Facade

## Purpose
Provide a core-layer interface to configuration defaults, model registry helpers, and pricing display so UI components do not import configuration directly.

## Key Exports

### ApplicationSettings
Settings container for config paths and application metadata.

### DEFAULT_USER_CONFIG
Default user configuration dictionary.

### Model Registry Helpers
Functions for provider lists, model lists, provider env vars, registry loading, and context window lookup.

### Pricing Helpers
Lookup and display utilities for model pricing.

## Integration Points

- **ui/main.py** - application settings
- **ui/commands/__init__.py** - model switching and API key validation
- **ui/screens/setup.py** - setup wizard provider/model lists
- **ui/screens/model_picker.py** - model listings and pricing display
