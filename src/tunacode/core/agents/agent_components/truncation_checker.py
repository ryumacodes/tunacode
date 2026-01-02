"""Truncation detection utilities for agent responses."""


def check_for_truncation(combined_content: str) -> bool:
    """Check if content appears to be truncated.

    Args:
        combined_content: The text content to check for truncation

    Returns:
        bool: True if the content appears truncated, False otherwise
    """
    if not combined_content:
        return False

    # Truncation indicators:
    # 1. Ends with "..." or "…" (but not part of a complete sentence)
    # 2. Contains incomplete markdown/code blocks
    # 3. Ends with incomplete parentheses/brackets

    # Check for ellipsis at end suggesting truncation
    if combined_content.endswith(("...", "…")) and not combined_content.endswith(("....", "….")):
        return True

    # Check for unclosed markdown code blocks
    code_block_count = combined_content.count("```")
    if code_block_count % 2 != 0:
        return True

    # Check for unclosed brackets/parentheses (more opens than closes)
    open_brackets = (
        combined_content.count("[") + combined_content.count("(") + combined_content.count("{")
    )
    close_brackets = (
        combined_content.count("]") + combined_content.count(")") + combined_content.count("}")
    )
    return open_brackets > close_brackets
