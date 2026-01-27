"""Core user configuration facade."""

from __future__ import annotations

from tunacode.types import UserConfig
from tunacode.types.state import StateManagerProtocol
from tunacode.utils.config import load_config_with_defaults as _load_config_with_defaults
from tunacode.utils.config.user_configuration import save_config as _save_config

__all__: list[str] = ["load_config_with_defaults", "save_config"]


def load_config_with_defaults(default_config: UserConfig) -> UserConfig:
    """Load user config from disk and merge with defaults.

    Args:
        default_config: Default configuration to merge against.

    Returns:
        The merged user configuration.
    """
    return _load_config_with_defaults(default_config)


def save_config(state_manager: StateManagerProtocol) -> None:
    """Persist the current user configuration to disk."""
    _save_config(state_manager)
