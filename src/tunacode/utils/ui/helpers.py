"""
Module: tunacode.utils.ui.helpers

Provides DotDict for dot notation access to dictionary attributes
and shared UI utility functions.
"""

from typing import Any


class DotDict(dict):
    """dot.notation access to dictionary attributes"""

    __getattr__ = dict.get
    __setattr__ = dict.__setitem__  # type: ignore[assignment]
    __delattr__ = dict.__delitem__  # type: ignore[assignment]


def truncate(value: Any, max_length: int = 50) -> str:
    """Truncate a value to max_length with ellipsis."""
    s = str(value)
    if len(s) <= max_length:
        return s
    return s[: max_length - 3] + "..."
