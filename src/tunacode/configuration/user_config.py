"""User configuration file management.

Handles loading, saving, and updating user preferences including model selection.
"""

import copy
import json
from json import JSONDecodeError
from typing import Protocol

from tunacode.configuration.settings import ApplicationSettings
from tunacode.constants import MODEL_PICKER_RECENT_LIMIT
from tunacode.exceptions import ConfigurationError
from tunacode.types import ModelName, UserConfig


class UserConfigSession(Protocol):
    """Minimal session interface for user config persistence."""

    user_config: UserConfig


class UserConfigStateManager(Protocol):
    """State manager interface needed for config persistence."""

    @property
    def session(self) -> UserConfigSession:
        """Return the session containing user config."""


def load_config() -> UserConfig | None:
    """Load user config from file.

    Returns None when the config file does not exist.
    Raises ConfigurationError for invalid JSON or other failures.
    """
    app_settings = ApplicationSettings()
    try:
        with open(app_settings.paths.config_file) as f:
            return json.load(f)
    except FileNotFoundError:
        return None
    except JSONDecodeError as err:
        msg = f"Invalid JSON in config file at {app_settings.paths.config_file}"
        raise ConfigurationError(msg) from err
    except Exception as err:
        raise ConfigurationError(f"Failed to load configuration: {err}") from err


def merge_user_config(default_config: UserConfig, user_config: UserConfig | None) -> UserConfig:
    """Merge user config on top of defaults."""
    if not user_config:
        return copy.deepcopy(default_config)

    merged_config = copy.deepcopy(default_config)
    merged_config.update(user_config)

    user_settings = user_config.get("settings")
    if not user_settings:
        return merged_config

    merged_settings = copy.deepcopy(default_config["settings"])
    merged_settings.update(user_settings)
    merged_config["settings"] = merged_settings
    return merged_config


def load_config_with_defaults(default_config: UserConfig) -> UserConfig:
    """Load user config from file and merge with defaults."""
    user_config = load_config()
    return merge_user_config(default_config, user_config)


def get_recent_models(
    user_config: UserConfig,
    *,
    available_models: set[str] | None = None,
    limit: int = MODEL_PICKER_RECENT_LIMIT,
) -> list[str]:
    """Return normalized recent models, optionally filtered to known entries."""
    raw_recent_models = user_config.get("recent_models", [])
    if not isinstance(raw_recent_models, list):
        return []

    normalized_recent_models: list[str] = []
    seen_models: set[str] = set()

    for raw_model in raw_recent_models:
        if not isinstance(raw_model, str):
            continue

        model_name = raw_model.strip()
        if not model_name or model_name in seen_models:
            continue

        if available_models is not None and model_name not in available_models:
            continue

        seen_models.add(model_name)
        normalized_recent_models.append(model_name)

        if len(normalized_recent_models) >= limit:
            break

    return normalized_recent_models


def record_recent_model(user_config: UserConfig, model_name: ModelName) -> list[str]:
    """Promote a model to the front of the recent-model MRU list."""
    normalized_model_name = model_name.strip()
    if not normalized_model_name:
        return get_recent_models(user_config)

    recent_models = get_recent_models(user_config)
    recent_models = [
        recent_model for recent_model in recent_models if recent_model != normalized_model_name
    ]
    recent_models.insert(0, normalized_model_name)
    user_config["recent_models"] = recent_models[:MODEL_PICKER_RECENT_LIMIT]
    return user_config["recent_models"]


def save_config(state_manager: UserConfigStateManager) -> None:
    """Save user config to file."""
    app_settings = ApplicationSettings()
    try:
        app_settings.paths.config_dir.mkdir(mode=0o700, parents=True, exist_ok=True)

        with open(app_settings.paths.config_file, "w") as f:
            json.dump(state_manager.session.user_config, f, indent=4)
    except PermissionError as e:
        raise ConfigurationError(
            f"Permission denied writing to {app_settings.paths.config_file}: {e}"
        ) from e
    except OSError as e:
        raise ConfigurationError(
            f"Failed to save configuration to {app_settings.paths.config_file}: {e}"
        ) from e
    except Exception as e:
        raise ConfigurationError(f"Unexpected error saving configuration: {e}") from e


def set_default_model(model_name: ModelName, state_manager: UserConfigStateManager) -> None:
    """Set the default model in the user config and save."""
    state_manager.session.user_config["default_model"] = model_name
    save_config(state_manager)
