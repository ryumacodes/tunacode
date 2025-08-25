"""
Module: tunacode.utils.api_key_validation

Utilities for validating API keys are configured for the selected model.
"""

from typing import Optional, Tuple

from tunacode.types import UserConfig


def get_required_api_key_for_model(model: str) -> Tuple[Optional[str], str]:
    """
    Determine which API key is required for a given model.

    Args:
        model: Model identifier in format "provider:model-name"

    Returns:
        Tuple of (api_key_name, provider_name) or (None, "unknown") if no specific key required
    """
    if not model or ":" not in model:
        return None, "unknown"

    provider = model.split(":")[0].lower()

    # Map providers to their required API keys
    provider_key_map = {
        "openrouter": ("OPENROUTER_API_KEY", "OpenRouter"),
        "openai": ("OPENAI_API_KEY", "OpenAI"),
        "anthropic": ("ANTHROPIC_API_KEY", "Anthropic"),
        "google": ("GEMINI_API_KEY", "Google"),
        "google-gla": ("GEMINI_API_KEY", "Google"),
        "gemini": ("GEMINI_API_KEY", "Google"),
    }

    return provider_key_map.get(provider, (None, provider))


def validate_api_key_for_model(model: str, user_config: UserConfig) -> Tuple[bool, Optional[str]]:
    """
    Check if the required API key exists for the given model.

    Args:
        model: Model identifier in format "provider:model-name"
        user_config: User configuration containing env variables

    Returns:
        Tuple of (is_valid, error_message)
    """
    api_key_name, provider_name = get_required_api_key_for_model(model)

    if not api_key_name:
        # No specific API key required (might be custom endpoint)
        return True, None

    env_config = user_config.get("env", {})
    api_key = env_config.get(api_key_name, "").strip()

    if not api_key:
        return False, (
            f"No API key found for {provider_name}.\n"
            f"Please run 'tunacode --setup' to configure your API key."
        )

    return True, None


def get_configured_providers(user_config: UserConfig) -> list[str]:
    """
    Get list of providers that have API keys configured.

    Args:
        user_config: User configuration containing env variables

    Returns:
        List of provider names that have API keys set
    """
    env_config = user_config.get("env", {})
    configured = []

    provider_map = {
        "OPENROUTER_API_KEY": "openrouter",
        "OPENAI_API_KEY": "openai",
        "ANTHROPIC_API_KEY": "anthropic",
        "GEMINI_API_KEY": "google",
    }

    for key_name, provider in provider_map.items():
        if env_config.get(key_name, "").strip():
            configured.append(provider)

    return configured
