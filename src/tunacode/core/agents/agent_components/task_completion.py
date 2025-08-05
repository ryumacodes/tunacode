"""Task completion detection utilities."""

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

    lines = content.strip().split("\n")
    if lines and lines[0].strip() == "TUNACODE_TASK_COMPLETE":
        # Task is complete, return cleaned content
        cleaned_lines = lines[1:] if len(lines) > 1 else []
        cleaned_content = "\n".join(cleaned_lines).strip()
        return True, cleaned_content

    return False, content
