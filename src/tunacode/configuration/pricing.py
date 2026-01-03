"""Pricing utilities for cost calculation and model pricing lookup."""

from tunacode.configuration.models import get_cached_models_registry, parse_model_string
from tunacode.types import ModelPricing

TOKENS_PER_MILLION = 1_000_000


def get_model_pricing(model_string: str) -> ModelPricing | None:
    """Get pricing for a model from cached models_registry data.

    Args:
        model_string: Full model identifier (e.g., "openrouter:openai/gpt-4.1")

    Returns:
        ModelPricing with input/output/cached costs per million tokens,
        or None if registry is not loaded, model not found, or has no pricing data.
    """
    registry = get_cached_models_registry()
    if registry is None:
        return None

    try:
        provider_id, model_id = parse_model_string(model_string)
    except ValueError:
        return None

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
    """Calculate cost in USD from token counts and pricing.

    Args:
        pricing: ModelPricing with costs per million tokens
        input_tokens: Number of input tokens (non-cached)
        cached_tokens: Number of cached input tokens
        output_tokens: Number of output tokens

    Returns:
        Total cost in USD.
    """
    input_cost = (input_tokens * pricing.input) / TOKENS_PER_MILLION
    cached_cost = (cached_tokens * pricing.cached_input) / TOKENS_PER_MILLION
    output_cost = (output_tokens * pricing.output) / TOKENS_PER_MILLION
    return input_cost + cached_cost + output_cost


def format_pricing_display(pricing: ModelPricing) -> str:
    """Format pricing for display as input/output cost string.

    Args:
        pricing: ModelPricing with costs per million tokens

    Returns:
        Formatted string (e.g., '$2.00/$8.00' for input/output).
    """
    return f"${pricing.input:.2f}/${pricing.output:.2f}"
