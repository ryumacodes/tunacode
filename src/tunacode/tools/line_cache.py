"""In-memory line cache for hashline edit validation.

Stores ``{path: {line_number: HashedLine}}`` so the hashline_edit tool
can validate that a file has not changed since the model last read it.
"""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType

from tunacode.tools.hashline import HashedLine, content_hash

# Module-level singleton cache: filepath -> {line_number -> HashedLine}
_cache: dict[str, dict[int, HashedLine]] = {}


def store(filepath: str, lines: list[HashedLine]) -> None:
    """Cache hashed lines for a file, replacing any prior state."""
    _cache[filepath] = {hl.line_number: hl for hl in lines}


def get(filepath: str) -> Mapping[int, HashedLine] | None:
    """Return cached lines for a file as a read-only view, or None if uncached."""
    file_lines = _cache.get(filepath)
    if file_lines is None:
        return None
    return MappingProxyType(file_lines)


def get_line(filepath: str, line_number: int) -> HashedLine | None:
    """Return a single cached line, or None if not cached."""
    file_lines = _cache.get(filepath)
    if file_lines is None:
        return None
    return file_lines.get(line_number)


def validate_ref(filepath: str, line_number: int, expected_hash: str) -> bool:
    """Check whether a line reference matches the cached state.

    Returns True if the cached line at ``line_number`` has a hash matching
    ``expected_hash``.  Returns False if the file is not cached, the line
    is missing, or the hash differs.
    """
    cached_line = get_line(filepath, line_number)
    if cached_line is None:
        return False
    return cached_line.hash == expected_hash


def update_lines(filepath: str, updates: dict[int, str]) -> None:
    """Update cached lines in-place after an edit.

    Args:
        filepath: The file that was edited.
        updates: Mapping of ``{line_number: new_content}`` for changed lines.
    """
    file_lines = _cache.get(filepath)
    if file_lines is None:
        raise RuntimeError(
            f"update_lines called for uncached file '{filepath}'. "
            "This violates the _validate_ref precondition in hashline_edit."
        )

    for line_number, new_content in updates.items():
        h = content_hash(new_content)
        file_lines[line_number] = HashedLine(
            line_number=line_number,
            hash=h,
            content=new_content,
        )


def replace_range(
    filepath: str,
    start_line: int,
    end_line: int,
    new_lines: list[str],
) -> None:
    """Replace a range of cached lines and re-number subsequent lines.

    Used after replace_range or insert_after edits where line counts change.

    Args:
        filepath: The file that was edited.
        start_line: First line number being replaced (inclusive).
        end_line: Last line number being replaced (inclusive).
        new_lines: The replacement content lines.
    """
    file_lines = _cache.get(filepath)
    if file_lines is None:
        raise RuntimeError(
            f"replace_range called for uncached file '{filepath}'. "
            "This violates the _validate_ref precondition in hashline_edit."
        )

    old_count = end_line - start_line + 1
    new_count = len(new_lines)
    shift = new_count - old_count

    # Remove old lines in the replaced range
    for ln in range(start_line, end_line + 1):
        file_lines.pop(ln, None)

    # Shift lines after the replaced range
    if shift != 0:
        moved: list[tuple[int, HashedLine]] = []
        for ln in sorted(file_lines):
            if ln > end_line:
                moved.append((ln, file_lines[ln]))
        for ln, _hl in moved:
            del file_lines[ln]
        for ln, hl in moved:
            new_ln = ln + shift
            file_lines[new_ln] = HashedLine(
                line_number=new_ln,
                hash=hl.hash,
                content=hl.content,
            )

    # Insert new lines
    for i, line_content in enumerate(new_lines):
        ln = start_line + i
        h = content_hash(line_content)
        file_lines[ln] = HashedLine(line_number=ln, hash=h, content=line_content)


def invalidate(filepath: str) -> None:
    """Remove all cached state for a file."""
    _cache.pop(filepath, None)


def clear() -> None:
    """Clear the entire cache (useful for testing)."""
    _cache.clear()


def cached_files() -> list[str]:
    """Return list of currently cached file paths."""
    return list(_cache.keys())
