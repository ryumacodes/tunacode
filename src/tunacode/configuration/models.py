"""
Module: tunacode.configuration.models

Configuration for loading model data from models_registry.json.
"""

# --- Models.dev Registry Functions ---

_models_registry_cache: dict | None = None


def load_models_registry() -> dict:
    """Load bundled models.dev registry from JSON file.

    Returns cached data on subsequent calls for performance.
    """
    global _models_registry_cache
    if _models_registry_cache is not None:
        return _models_registry_cache

    import json
    from pathlib import Path

    registry_path = Path(__file__).parent / "models_registry.json"
    with open(registry_path) as f:
        _models_registry_cache = json.load(f)
    return _models_registry_cache


def get_providers() -> list[tuple[str, str]]:
    """Return (display_name, id) tuples for all providers.

    Sorted alphabetically by display name.
    """
    registry = load_models_registry()
    providers = [(p["name"], p["id"]) for p in registry.values()]
    return sorted(providers, key=lambda x: x[0].lower())


def get_models_for_provider(provider_id: str) -> list[tuple[str, str]]:
    """Return (display_name, id) tuples for a provider's models.

    Args:
        provider_id: The provider identifier (e.g., "openai", "anthropic")

    Returns:
        List of (model_name, model_id) tuples, sorted alphabetically.
    """
    registry = load_models_registry()
    provider = registry.get(provider_id, {})
    models = provider.get("models", {})
    result = [(m["name"], mid) for mid, m in models.items()]
    return sorted(result, key=lambda x: x[0].lower())


def get_provider_env_var(provider_id: str) -> str:
    """Return the environment variable name for a provider's API key.

    Args:
        provider_id: The provider identifier

    Returns:
        Environment variable name (e.g., "OPENAI_API_KEY")
    """
    registry = load_models_registry()
    provider = registry.get(provider_id, {})
    env_vars = provider.get("env", [])
    if env_vars:
        return env_vars[0]
    return f"{provider_id.upper()}_API_KEY"


def get_provider_base_url(provider_id: str) -> str | None:
    """Return the API base URL for a provider.

    Args:
        provider_id: The provider identifier

    Returns:
        Base URL string or None if not specified
    """
    registry = load_models_registry()
    provider = registry.get(provider_id, {})
    return provider.get("api")
