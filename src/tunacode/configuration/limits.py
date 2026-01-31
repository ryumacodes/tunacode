"""Centralized limit configuration with cascading defaults.

Precedence: explicit setting > standard default

This allows:
- Users to override individual limits
- Big model users to set custom limits
"""

from functools import lru_cache

from tunacode.constants import (
    LOCAL_SUMMARY_THRESHOLD,
    MAX_COMMAND_OUTPUT,
    MAX_FILES_IN_DIR,
    SUMMARY_THRESHOLD,
)


@lru_cache(maxsize=1)
def _load_settings() -> dict:
    """Load and cache settings from user config."""
    # Import here to avoid circular imports
    from tunacode.configuration.user_config import load_config

    config = load_config()
    if config and "settings" in config:
        return config["settings"]
    return {}


def clear_cache() -> None:
    """Clear the settings cache. Call when config changes."""
    _load_settings.cache_clear()


def _get_limit(key: str, default: int) -> int:
    """Get a limit value with proper precedence.

    Precedence: explicit setting > standard default
    """
    settings = _load_settings()

    # If explicitly set, use that value
    if key in settings:
        return settings[key]

    return default


def get_command_limit() -> int:
    """Get max command output length for bash tool."""
    return _get_limit("max_command_output", MAX_COMMAND_OUTPUT)


def get_max_files_in_dir() -> int:
    """Get max files to list in list_dir tool."""
    return _get_limit("max_files_in_dir", MAX_FILES_IN_DIR)


def get_max_tokens() -> int | None:
    """Get max response tokens. Returns None if not set (no limit)."""
    settings = _load_settings()

    # Explicit setting takes precedence
    if "max_tokens" in settings:
        return settings["max_tokens"]

    return None


def is_rolling_summaries_enabled() -> bool:
    """Check if rolling summaries feature is enabled."""
    return _load_settings().get("enable_rolling_summaries", False)


def get_summary_threshold() -> int:
    """Get token threshold for triggering summary generation."""
    settings = _load_settings()

    # Explicit setting takes precedence
    if "summary_threshold" in settings:
        return settings["summary_threshold"]

    # Use local threshold if local_mode is enabled
    if settings.get("local_mode", False):
        # Check user's local_summary_threshold setting first
        if "local_summary_threshold" in settings:
            return settings["local_summary_threshold"]
        return LOCAL_SUMMARY_THRESHOLD

    return SUMMARY_THRESHOLD
