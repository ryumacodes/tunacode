# Research – Pricing Mechanism Consolidation

**Date:** 2025-12-04
**Owner:** Claude Agent
**Phase:** Research

## Goal

Consolidate pricing mechanism to use `models_registry.json` (from models.dev) instead of hardcoded `ModelRegistry` class. Create a modular price picker and remove the old implementation.

## Current Architecture

### Two Separate Data Sources (Problem)

| Component | File | Purpose | Pricing Data |
|-----------|------|---------|--------------|
| `ModelRegistry` class | `src/tunacode/configuration/models.py:12-94` | Hardcoded pricing | `ModelPricing(input, cached_input, output)` for 24 models |
| `models_registry.json` | `src/tunacode/configuration/models_registry.json` | Model picker data | `cost: {input, output, cache_read}` from models.dev |

### JSON Registry Structure (models_registry.json)

The JSON file already contains pricing data from models.dev:

```python
{
  "provider_id": {
    "id": "provider_id",
    "name": "Display Name",
    "env": ["PROVIDER_API_KEY"],
    "api": "https://api.provider.com/v1",
    "models": {
      "model-id": {
        "id": "model-id",
        "name": "Model Display Name",
        "cost": {
          "input": 1.15,      # Per million tokens
          "output": 8.0,      # Per million tokens
          "cache_read": 0.15  # Per million tokens
        },
        "limit": {
          "context": 262144,
          "output": 262144
        },
        ...
      }
    }
  }
}
```

### Hardcoded ModelRegistry (To Remove)

Location: `src/tunacode/configuration/models.py:12-94`

```python
class ModelRegistry:
    def _load_default_models(self) -> ModelRegistryType:
        return {
            "anthropic:claude-opus-4-20250514": ModelConfig(
                pricing=ModelPricing(input=3.00, cached_input=1.50, output=15.00)
            ),
            # ... 23 more hardcoded models
        }
```

**Problems with current approach:**
1. Pricing is duplicated between JSON and Python
2. JSON has more models (581KB vs 24 models)
3. JSON is sourced from models.dev (more maintainable)
4. Hardcoded pricing requires code changes to update

## Findings

### Files That Need Modification

| File | Lines | Change Required |
|------|-------|-----------------|
| `src/tunacode/configuration/models.py` | 12-94 | Remove `ModelRegistry` class, add `get_model_pricing()` function |
| `src/tunacode/types.py` | 44-60 | Keep `ModelPricing`, `ModelConfig` types |
| `src/tunacode/core/agents/agent_components/node_processor.py` | 33 | Replace `cost = 0.0` with actual calculation |
| `src/tunacode/ui/screens/model_picker.py` | 15-242 | Add pricing display to model selection |
| `README.md` | TBD | Add pricing accuracy disclaimer |

### Files That Use ModelRegistry (Impact Analysis)

```bash
# Direct imports of ModelRegistry
grep -r "ModelRegistry" src/tunacode/
```

| File | Usage | Impact |
|------|-------|--------|
| `src/tunacode/types.py:60` | Type alias only | No change needed |
| `src/tunacode/configuration/models.py:12` | Class definition | **Remove entirely** |

### Cost Calculation Location

The cost calculation happens (or rather, doesn't) at:

`src/tunacode/core/agents/agent_components/node_processor.py:22-37`

```python
def _update_token_usage(state_manager: StateManager, model_response) -> None:
    session = state_manager.session
    usage = model_response.usage
    request_tokens = getattr(usage, "request_tokens", 0) or 0
    response_tokens = getattr(usage, "response_tokens", 0) or 0

    session.last_call_usage["prompt_tokens"] = request_tokens
    session.last_call_usage["completion_tokens"] = response_tokens
    session.last_call_usage["cost"] = 0.0  # <-- HARDCODED, needs real calculation
```

### Model Picker UI Location

`src/tunacode/ui/screens/model_picker.py`

- `ProviderPickerScreen` (lines 15-126): Selects provider
- `ModelPickerScreen` (lines 128-242): Selects model from provider
- Neither displays pricing information currently

## Key Patterns / Solutions Found

### Pattern 1: JSON Pricing Access

Add function to `models.py` to get pricing from JSON:

```python
def get_model_pricing(provider_id: str, model_id: str) -> ModelPricing | None:
    """Get pricing for a model from models_registry.json.

    Args:
        provider_id: Provider identifier (e.g., "openai")
        model_id: Model identifier (e.g., "gpt-4.1")

    Returns:
        ModelPricing with input/cached_input/output costs, or None
    """
    registry = load_models_registry()
    provider = registry.get(provider_id, {})
    model = provider.get("models", {}).get(model_id, {})
    cost = model.get("cost", {})

    if not cost:
        return None

    return ModelPricing(
        input=cost.get("input", 0.0),
        cached_input=cost.get("cache_read", 0.0),  # JSON uses "cache_read"
        output=cost.get("output", 0.0)
    )
```

### Pattern 2: Cost Calculation

```python
def calculate_cost(
    pricing: ModelPricing,
    input_tokens: int,
    cached_tokens: int,
    output_tokens: int
) -> float:
    """Calculate cost in USD from token counts and pricing.

    Pricing is per million tokens.
    """
    return (
        (input_tokens * pricing.input / 1_000_000) +
        (cached_tokens * pricing.cached_input / 1_000_000) +
        (output_tokens * pricing.output / 1_000_000)
    )
```

### Pattern 3: Model Picker with Pricing

Display format in ModelPickerScreen:

```
gpt-4.1          $2.00/$8.00  (in/out per 1M tokens)
gpt-4.1-mini     $0.40/$1.60
claude-opus-4    $3.00/$15.00
```

## Knowledge Gaps

1. **Pricing accuracy**: models.dev pricing may not be 100% current
   - Need README disclaimer
   - Consider adding last_updated field tracking

2. **Cache pricing field name mismatch**:
   - JSON uses `cache_read`
   - Python uses `cached_input`
   - Need mapping in `get_model_pricing()`

3. **Missing models**: Some hardcoded models may not exist in JSON
   - Need fallback behavior (return None or default pricing)

4. **OpenRouter pricing**: OpenRouter models have markup over base pricing
   - JSON may have OpenRouter-specific pricing already

## Implementation Plan

### Phase 1: New Price Picker Module

1. Create `src/tunacode/pricing/` module:
   - `__init__.py` - exports
   - `calculator.py` - cost calculation functions
   - `registry.py` - pricing lookup from JSON

2. Functions to implement:
   - `get_model_pricing(model_string: str) -> ModelPricing | None`
   - `calculate_cost(pricing, input_tokens, cached_tokens, output_tokens) -> float`
   - `format_pricing_display(pricing: ModelPricing) -> str`

### Phase 2: Integrate with Node Processor

Update `node_processor.py:_update_token_usage()`:
1. Parse model name from `state_manager.session.current_model`
2. Get pricing via `get_model_pricing()`
3. Calculate actual cost
4. Update `session.last_call_usage["cost"]`

### Phase 3: Update Model Picker UI

Update `model_picker.py:ModelPickerScreen`:
1. Load pricing data alongside model names
2. Display pricing in selection list
3. Sort/filter by price option

### Phase 4: Remove Old ModelRegistry

1. Delete `ModelRegistry` class from `models.py` (lines 12-94)
2. Update any imports (none found)
3. Keep `load_models_registry()` and helper functions

### Phase 5: Documentation

Add to README.md:
```markdown
## Pricing Disclaimer

Token pricing is sourced from [models.dev](https://models.dev) registry
and may not reflect current provider pricing. For accurate billing,
check your provider's dashboard directly.
```

## References

### Core Files
- `src/tunacode/configuration/models.py` - Current pricing implementation
- `src/tunacode/configuration/models_registry.json` - JSON registry (581KB)
- `src/tunacode/ui/screens/model_picker.py` - Model selection UI
- `src/tunacode/core/agents/agent_components/node_processor.py` - Token tracking

### Type Definitions
- `src/tunacode/types.py:44-60` - `ModelPricing`, `ModelConfig`
- `src/tunacode/types.py:201-216` - `TokenUsage`, `CostBreakdown`

### UI Components
- `src/tunacode/ui/widgets/resource_bar.py` - Cost display widget
- `src/tunacode/ui/app.py:293-306` - Resource bar updates

### Related Research
- `memory-bank/research/2025-12-04_token-management-context-compaction.md`
- `memory-bank/research/2025-09-21_models-registry-pydantic-conversion.md`
