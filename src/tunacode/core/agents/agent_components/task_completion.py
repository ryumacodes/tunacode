"""Task completion detection utilities."""

import re
from typing import Tuple


def check_task_completion(content: str) -> Tuple[bool, str]:
    """
    Check if the content indicates task completion.

    Args:
        content: The text content to check

    Returns:
        Tuple of (is_complete, cleaned_content)
        - is_complete: True if task completion marker found
        - cleaned_content: Content with marker removed
    """
    if not content:
        return False, content

    lines = content.split("\n")

    # New marker: any line starting with "TUNACODE DONE:" (case-insensitive, allow leading whitespace)
    done_pattern = re.compile(r"^\s*TUNACODE\s+DONE:\s*", re.IGNORECASE)
    for idx, line in enumerate(lines):
        if done_pattern.match(line):
            # Remove the marker line and return remaining content
            cleaned = "\n".join(lines[:idx] + lines[idx + 1 :]).strip()
            return True, cleaned

    return False, content
