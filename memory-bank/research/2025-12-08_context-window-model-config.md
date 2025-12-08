# Research - Context Window Model Configuration

**Date:** 2025-12-08
**Owner:** agent
**Phase:** Research

## Goal

Understand how context window is currently configured (200k default) and how to update it to use model-specific values from `models_registry.json`.

## Findings

### Current Implementation

| File | Purpose |
|------|---------|
| `src/tunacode/constants.py` | `DEFAULT_CONTEXT_WINDOW = 200000` |
| `src/tunacode/configuration/defaults.py:28` | `"context_window_size": 200000` in settings |
| `src/tunacode/core/state.py:140-142` | `max_tokens` initialized from config, defaults to 200000 |
| `src/tunacode/ui/widgets/resource_bar.py` | Hardcoded `_max_tokens: int = 200000` fallback |

### Model Registry JSON Structure

Location: `src/tunacode/configuration/models_registry.json`

Each model has a `limit.context` field:
```json
// Claude Sonnet 3.5
"limit": { "context": 200000, "output": 8192 }

// GPT-4o
"limit": { "context": 128000, "output": 16384 }
```

### Gap Analysis

1. **No lookup function** - `models.py` has no `get_model_context_window()` function
2. **Static max_tokens** - When model changes, `max_tokens` is NOT updated
3. **Hardcoded compaction thresholds** - `compaction.py` uses absolute 40k/20k values

## Key Patterns / Solutions Found

- `get_model_pricing()` in `pricing.py:17-36` demonstrates the pattern for looking up model-specific data from registry
- Model string format is `"provider:model_id"` parsed by `parse_model_string()`

## Implementation Plan

### Step 1: Add lookup function to `models.py`

```python
def get_model_context_window(model_string: str) -> int | None:
    """Get context window size for a model from models_registry.json."""
    provider_id, model_id = parse_model_string(model_string)
    registry = load_models_registry()
    model = registry.get(provider_id, {}).get("models", {}).get(model_id, {})
    limit = model.get("limit", {})
    return limit.get("context")
```

### Step 2: Update `state.py` to use model-specific context

When model changes or loads, lookup context window from registry with 200k fallback.

### Step 3: Update model change handlers

In `ui/commands/__init__.py`, update `max_tokens` when model switches.

## Knowledge Gaps

- Need to verify all providers in registry have `limit.context` field
- Consider if user override should take precedence over model default

## References

- `src/tunacode/configuration/models_registry.json` - Model metadata with `limit.context`
- `src/tunacode/configuration/models.py` - Registry loader functions
- `src/tunacode/configuration/pricing.py` - Pattern for model lookups
- `src/tunacode/core/state.py` - Session state with `max_tokens`
