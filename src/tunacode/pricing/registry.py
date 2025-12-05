"""Pricing registry lookup from models_registry.json."""

from tunacode.configuration.models import load_models_registry
from tunacode.types import ModelPricing


def parse_model_string(model_string: str) -> tuple[str, str]:
    """Parse 'provider:model_id' into (provider_id, model_id)."""
    if ":" not in model_string:
        raise ValueError(f"Invalid model string format: {model_string}")
    return model_string.split(":", 1)


def get_model_pricing(model_string: str) -> ModelPricing | None:
    """Get pricing for a model from models_registry.json."""
    try:
        provider_id, model_id = parse_model_string(model_string)
    except ValueError:
        return None

    registry = load_models_registry()
    provider = registry.get(provider_id, {})
    model = provider.get("models", {}).get(model_id, {})
    cost = model.get("cost", {})

    if not cost:
        return None

    return ModelPricing(
        input=cost.get("input", 0.0),
        output=cost.get("output", 0.0),
        cached_input=cost.get("cache_read", 0.0),
    )
