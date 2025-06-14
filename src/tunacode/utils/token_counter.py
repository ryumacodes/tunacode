"""Simple token counting utility for estimating message sizes."""


def estimate_tokens(text: str) -> int:
    """
    Estimate token count using a simple character-based approximation.

    This is a rough estimate: ~4 characters per token on average.
    For more accurate counting, we would need tiktoken or similar.
    """
    if not text:
        return 0

    # Simple approximation: ~4 characters per token
    # This is roughly accurate for English text
    return len(text) // 4


def format_token_count(count: int) -> str:
    """Format token count for display."""
    if count >= 1000:
        return f"{count:,}"
    return str(count)
