"""Core formatting helpers for shared presentation helpers."""

from __future__ import annotations

MAX_DIAGNOSTIC_MESSAGE_LENGTH = 80


def truncate_diagnostic_message(
    message: str,
    max_length: int = MAX_DIAGNOSTIC_MESSAGE_LENGTH,
) -> str:
    """Trim verbose diagnostic text for display."""
    first_line = message.split("\n")[0].strip()
    if len(first_line) > max_length:
        return first_line[: max_length - 3] + "..."
    return first_line
