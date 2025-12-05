"""Pricing utilities for cost calculation and model pricing lookup."""

from tunacode.configuration.models import load_models_registry
from tunacode.types import ModelPricing

TOKENS_PER_MILLION = 1_000_000


def parse_model_string(model_string: str) -> tuple[str, str]:
    """Parse 'provider:model_id' into (provider_id, model_id)."""
    if ":" not in model_string:
        raise ValueError(f"Invalid model string format: {model_string}")
    parts = model_string.split(":", 1)
    return (parts[0], parts[1])


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


def calculate_cost(
    pricing: ModelPricing,
    input_tokens: int,
    cached_tokens: int,
    output_tokens: int,
) -> float:
    """Calculate cost in USD from token counts and pricing (per million tokens)."""
    input_cost = (input_tokens * pricing.input) / TOKENS_PER_MILLION
    cached_cost = (cached_tokens * pricing.cached_input) / TOKENS_PER_MILLION
    output_cost = (output_tokens * pricing.output) / TOKENS_PER_MILLION
    return input_cost + cached_cost + output_cost


def format_pricing_display(pricing: ModelPricing) -> str:
    """Format pricing for display (e.g., '$2.00/$8.00' for input/output)."""
    return f"${pricing.input:.2f}/${pricing.output:.2f}"
