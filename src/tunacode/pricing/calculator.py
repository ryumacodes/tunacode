"""Cost calculation for token usage."""

from tunacode.types import ModelPricing

TOKENS_PER_MILLION = 1_000_000


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
