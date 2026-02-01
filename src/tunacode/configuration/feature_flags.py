"""Feature flag infrastructure for gradual rollouts.

Usage:
    from tunacode.configuration.feature_flags import is_enabled

    if is_enabled("new_tool_renderer"):
        # new behavior
    else:
        # old behavior

Flags can be set via:
    1. Environment: TUNACODE_FF_NEW_TOOL_RENDERER=1
    2. Config file: tunacode.json -> {"feature_flags": {"new_tool_renderer": true}}
"""

import os
from typing import Final

# Default flag states (False = off, True = on)
_DEFAULTS: Final[dict[str, bool]] = {
    # Example flags - add new flags here with default=False for gradual rollout
    # "new_tool_renderer": False,
    # "parallel_tool_execution": False,
}

_ENV_PREFIX: Final[str] = "TUNACODE_FF_"


def is_enabled(flag_name: str) -> bool:
    """Check if a feature flag is enabled.

    Resolution order:
        1. Environment variable (TUNACODE_FF_{FLAG_NAME}=1)
        2. Default value from _DEFAULTS
        3. False if not defined
    """
    env_key = f"{_ENV_PREFIX}{flag_name.upper()}"
    env_value = os.environ.get(env_key)

    if env_value is not None:
        return env_value.lower() in ("1", "true", "yes", "on")

    return _DEFAULTS.get(flag_name, False)


def get_all_flags() -> dict[str, bool]:
    """Get current state of all known flags."""
    return {name: is_enabled(name) for name in _DEFAULTS}
