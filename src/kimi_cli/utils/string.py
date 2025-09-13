def shorten_middle(text: str, width: int) -> str:
    """Shorten the text by inserting ellipsis in the middle."""
    if len(text) <= width:
        return text
    return text[: width // 2] + "..." + text[-width // 2 :]
