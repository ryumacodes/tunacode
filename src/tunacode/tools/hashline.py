"""Content-hash line tagging and validation for file edits.

Provides a read-side annotation + write-side validation pattern:
- On read: each line is tagged with a short content hash (2 hex chars)
- On edit: the hash is validated against cached state to detect stale references

The hash is ``md5(line_content)[:2]``, giving 256 buckets — enough to
catch stale references without bloating context.
"""

import hashlib
from typing import NamedTuple

HASH_LENGTH = 2
HASH_SEPARATOR = "|"
LINE_HASH_SEPARATOR = ":"


class HashedLine(NamedTuple):
    """A single line with its content hash."""

    line_number: int
    hash: str
    content: str


def content_hash(line: str) -> str:
    """Compute a short MD5 hash of a line's content.

    Two hex characters provide 256 buckets — sufficient to detect stale
    references without inflating the context window.
    """
    return hashlib.md5(line.encode()).hexdigest()[:HASH_LENGTH]


def tag_lines(content: str, offset: int = 0) -> list[HashedLine]:
    """Split content into lines and tag each with a content hash.

    Args:
        content: Raw file content.
        offset: Number of lines skipped before this content (for pagination).

    Returns:
        List of HashedLine tuples with 1-based line numbers.
    """
    lines = content.splitlines()
    result: list[HashedLine] = []
    for i, line in enumerate(lines):
        line_number = offset + i + 1
        h = content_hash(line)
        result.append(HashedLine(line_number=line_number, hash=h, content=line))
    return result


def format_hashline(hashed_line: HashedLine) -> str:
    """Format a single hashed line for display.

    Output format: ``<line_number>:<hash>|<content>``
    Example: ``1:a3|function hello() {``
    """
    return (
        f"{hashed_line.line_number}{LINE_HASH_SEPARATOR}"
        f"{hashed_line.hash}{HASH_SEPARATOR}{hashed_line.content}"
    )


def format_hashlines(content: str, offset: int = 0) -> str:
    """Tag every line in content with a content hash and format for display.

    Args:
        content: Raw file content.
        offset: Number of lines skipped (for pagination).

    Returns:
        Formatted string with each line prefixed by ``<number>:<hash>|``.
    """
    tagged = tag_lines(content, offset=offset)
    return "\n".join(format_hashline(hl) for hl in tagged)


def parse_line_ref(ref: str) -> tuple[int, str]:
    """Parse a ``<line_number>:<hash>`` reference string.

    Args:
        ref: A string like ``"2:f1"``

    Returns:
        Tuple of (line_number, expected_hash).

    Raises:
        ValueError: If the reference format is invalid.
    """
    if LINE_HASH_SEPARATOR not in ref:
        raise ValueError(
            f"Invalid line reference '{ref}': expected format '<line>:<hash>'"
        )
    parts = ref.split(LINE_HASH_SEPARATOR, 1)
    try:
        line_number = int(parts[0])
    except ValueError as exc:
        raise ValueError(
            f"Invalid line number in reference '{ref}': {parts[0]}"
        ) from exc
    expected_hash = parts[1]
    if len(expected_hash) != HASH_LENGTH:
        raise ValueError(
            f"Invalid hash length in reference '{ref}': "
            f"expected {HASH_LENGTH} chars, got {len(expected_hash)}"
        )
    return line_number, expected_hash
