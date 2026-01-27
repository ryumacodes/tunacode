"""Core formatting facade for shared presentation helpers."""

from __future__ import annotations

from tunacode.utils.formatting import (
    MAX_DIAGNOSTIC_MESSAGE_LENGTH,
)
from tunacode.utils.formatting import (
    truncate_diagnostic_message as _truncate_diagnostic_message,
)

__all__: list[str] = ["truncate_diagnostic_message"]


def truncate_diagnostic_message(
    message: str,
    max_length: int = MAX_DIAGNOSTIC_MESSAGE_LENGTH,
) -> str:
    """Trim verbose diagnostic text for display."""
    return _truncate_diagnostic_message(message, max_length=max_length)
