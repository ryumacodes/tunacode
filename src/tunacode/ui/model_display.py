"""Utilities for displaying provider/model in constrained UI areas.

This module intentionally lives in ``tunacode.ui`` (not renderers/widgets)
so both Rich renderers and Textual widgets can share the same formatting.
"""

from __future__ import annotations

# Maximum length for model display in single-line UI bars.
MODEL_DISPLAY_MAX_LENGTH = 40

# Provider id -> compact prefix.
# Note: Prefixes include the trailing slash to normalize both "provider/model"
# and "provider:model" into a single display form.
MODEL_PROVIDER_ABBREVIATIONS: dict[str, str] = {
    "anthropic": "ANTH/",
    "openai": "OA/",
    "google": "GOOG/",
    "mistral": "MIST/",
    "openrouter": "OR/",
    "together": "TOG/",
    "groq": "GROQ/",
}


def format_model_for_display(
    model: str,
    *,
    max_length: int = MODEL_DISPLAY_MAX_LENGTH,
) -> str:
    """Format a model string for display.

    Examples:
        - "openai/gpt-4o" -> "OA/gpt-4o"
        - "openai:gpt-4o" -> "OA/gpt-4o"

    Preconditions:
        - max_length >= 4 (room for "...")

    Postconditions:
        - Returned string length <= max_length

    Args:
        model: Raw model string from the session.
        max_length: Maximum length of the returned string.

    Returns:
        Formatted model string suitable for compact, single-line UI.
    """
    if max_length < 4:
        raise ValueError(f"max_length must be >= 4, got {max_length}")

    normalized = model

    for provider_id, abbrev in MODEL_PROVIDER_ABBREVIATIONS.items():
        provider_prefix_slash = f"{provider_id}/"
        provider_prefix_colon = f"{provider_id}:"

        if normalized.startswith(provider_prefix_slash):
            normalized = abbrev + normalized[len(provider_prefix_slash) :]
            break

        if normalized.startswith(provider_prefix_colon):
            normalized = abbrev + normalized[len(provider_prefix_colon) :]
            break

    if len(normalized) > max_length:
        keep = max_length - 3
        return normalized[:keep] + "..."

    return normalized
