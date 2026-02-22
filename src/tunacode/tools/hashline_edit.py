"""Hash-validated line editing tool for agent operations.

Provides three edit operations that validate against the line cache
populated by ``read_file``:

- **replace**: Replace a single line identified by ``<line>:<hash>``.
- **replace_range**: Replace a contiguous range of lines.
- **insert_after**: Insert new lines after a referenced line.

Each operation parses the ``line:hash`` reference, validates the hash
against the cached file state, applies the edit, and updates the cache.
If the hash does not match, the tool rejects the edit and instructs the
model to re-read the file.
"""

import asyncio
import difflib
from collections.abc import Callable
from pathlib import Path
from typing import Literal

from tunacode.exceptions import ToolRetryError

from tunacode.tools.decorators import file_tool
from tunacode.tools.hashline import parse_line_ref
from tunacode.tools.line_cache import (
    get as _cache_get,
)
from tunacode.tools.line_cache import (
    replace_range as _cache_replace_range,
)
from tunacode.tools.line_cache import (
    update_lines as _cache_update_lines,
)
from tunacode.tools.lsp.diagnostics import maybe_prepend_lsp_diagnostics

STALE_REF_MESSAGE = (
    "File has changed since last read — line {line} hash mismatch "
    "(expected '{expected}', cached '{actual}'). Re-read the file first."
)
UNCACHED_FILE_MESSAGE = "File '{filepath}' has no cached state. Read the file first with read_file."
LINE_NOT_CACHED_MESSAGE = (
    "Line {line} is not in the cached state for '{filepath}'. "
    "The file may have been read with an offset that skipped this line. "
    "Re-read the file to include this line."
)
FILE_NOT_FOUND_MESSAGE = "File '{filepath}' not found. Cannot edit."
DEFAULT_ENCODING = "utf-8"


INVALID_REF_MESSAGE = (
    "Invalid line reference '{ref}': {error}. Use '<line>:<hash>' from read_file output."
)


def _validate_ref(filepath: str, ref: str) -> int:
    """Parse and validate a line:hash reference against the cache.

    Returns the validated line number.

    Raises:
        ToolRetryError: If the file is not cached, the line is missing,
            or the hash does not match.
    """
    try:
        line_number, expected_hash = parse_line_ref(ref)
    except ValueError as exc:
        raise ToolRetryError(INVALID_REF_MESSAGE.format(ref=ref, error=str(exc))) from exc

    cached = _cache_get(filepath)
    if cached is None:
        raise ToolRetryError(UNCACHED_FILE_MESSAGE.format(filepath=filepath))

    cached_line = cached.get(line_number)
    if cached_line is None:
        raise ToolRetryError(LINE_NOT_CACHED_MESSAGE.format(line=line_number, filepath=filepath))

    if cached_line.hash != expected_hash:
        raise ToolRetryError(
            STALE_REF_MESSAGE.format(
                line=line_number,
                expected=expected_hash,
                actual=cached_line.hash,
            )
        )

    return line_number


def _read_file_lines(filepath: str) -> tuple[list[str], bool]:
    """Read all lines and whether the file ends with a trailing newline."""
    with open(filepath, encoding=DEFAULT_ENCODING) as f:
        content = f.read()
    has_trailing_newline = content.endswith("\n")
    return content.splitlines(), has_trailing_newline


def _write_file_lines(
    filepath: str,
    lines: list[str],
    preserve_trailing_newline: bool,
) -> None:
    """Write lines back to a file while preserving trailing newline state."""
    serialized = "\n".join(lines)
    if preserve_trailing_newline:
        serialized += "\n"
    with open(filepath, "w", encoding=DEFAULT_ENCODING) as f:
        f.write(serialized)


def _make_diff(
    filepath: str,
    original_lines: list[str],
    new_lines: list[str],
) -> str:
    """Generate a unified diff between original and new content."""
    diff = difflib.unified_diff(
        [ln + "\n" for ln in original_lines],
        [ln + "\n" for ln in new_lines],
        fromfile=f"a/{filepath}",
        tofile=f"b/{filepath}",
    )
    return "".join(diff)


@file_tool
async def hashline_edit(
    filepath: str,
    operation: Literal["replace", "replace_range", "insert_after"],
    line: str | None = None,
    start: str | None = None,
    end: str | None = None,
    after: str | None = None,
    new: str = "",
) -> str:
    """Edit a file using hash-validated line references.

    Three operations are supported:

    **replace** — Replace a single line.
      Required: ``line`` (e.g. "2:f1"), ``new`` (replacement text).

    **replace_range** — Replace a contiguous range of lines.
      Required: ``start`` (e.g. "1:a3"), ``end`` (e.g. "3:0e"), ``new`` (replacement text).

    **insert_after** — Insert new lines after a referenced line.
      Required: ``after`` (e.g. "3:0e"), ``new`` (text to insert).

    The ``line``, ``start``, ``end``, and ``after`` parameters use the
    format ``<line_number>:<hash>`` from the read_file output.

    Args:
        filepath: Absolute path to the file to edit.
        operation: One of "replace", "replace_range", "insert_after".
        line: Line reference for replace (e.g. "2:f1").
        start: Start line reference for replace_range.
        end: End line reference for replace_range.
        after: Line reference for insert_after.
        new: The new content to write.

    Returns:
        A message with the diff of changes applied.
    """
    path = Path(filepath)
    if not await asyncio.to_thread(path.exists):
        raise ToolRetryError(FILE_NOT_FOUND_MESSAGE.format(filepath=filepath))

    original_lines, had_trailing_newline = await asyncio.to_thread(_read_file_lines, filepath)

    if operation == "replace":
        result = _apply_replace(filepath, original_lines, line, new)
    elif operation == "replace_range":
        result = _apply_replace_range(filepath, original_lines, start, end, new)
    elif operation == "insert_after":
        result = _apply_insert_after(filepath, original_lines, after, new)
    else:
        raise ToolRetryError(
            f"Unknown operation '{operation}'. Use 'replace', 'replace_range', or 'insert_after'."
        )

    new_lines, description, cache_mutation = result
    await asyncio.to_thread(
        _write_file_lines,
        filepath,
        new_lines,
        had_trailing_newline,
    )
    cache_mutation()

    diff_text = _make_diff(filepath, original_lines, new_lines)
    output = f"{description}\n\n{diff_text}"
    output = await maybe_prepend_lsp_diagnostics(output, Path(filepath))
    return output


def _apply_replace(
    filepath: str,
    lines: list[str],
    line_ref: str | None,
    new_content: str,
) -> tuple[list[str], str, Callable[[], None]]:
    """Replace a single line."""
    if line_ref is None:
        raise ToolRetryError("The 'line' parameter is required for the 'replace' operation.")
    line_number = _validate_ref(filepath, line_ref)
    idx = line_number - 1

    if idx < 0 or idx >= len(lines):
        raise ToolRetryError(f"Line {line_number} is out of range (file has {len(lines)} lines).")

    new_lines = list(lines)
    new_lines[idx] = new_content

    def cache_mutation() -> None:
        _cache_update_lines(filepath, {line_number: new_content})

    return new_lines, f"File '{filepath}' updated: replaced line {line_number}.", cache_mutation


def _apply_replace_range(
    filepath: str,
    lines: list[str],
    start_ref: str | None,
    end_ref: str | None,
    new_content: str,
) -> tuple[list[str], str, Callable[[], None]]:
    """Replace a contiguous range of lines."""
    if start_ref is None:
        raise ToolRetryError("The 'start' parameter is required for the 'replace_range' operation.")
    if end_ref is None:
        raise ToolRetryError("The 'end' parameter is required for the 'replace_range' operation.")
    start_line = _validate_ref(filepath, start_ref)
    end_line = _validate_ref(filepath, end_ref)

    if start_line > end_line:
        raise ToolRetryError(
            f"Start line ({start_line}) must not be greater than end line ({end_line})."
        )

    start_idx = start_line - 1
    end_idx = end_line  # exclusive for slicing

    if start_idx < 0 or end_idx > len(lines):
        raise ToolRetryError(
            f"Line range {start_line}-{end_line} is out of bounds (file has {len(lines)} lines)."
        )

    replacement_lines = new_content.splitlines() if new_content else []
    new_lines = lines[:start_idx] + replacement_lines + lines[end_idx:]

    def cache_mutation() -> None:
        _cache_replace_range(filepath, start_line, end_line, replacement_lines)

    return (
        new_lines,
        f"File '{filepath}' updated: replaced lines {start_line}-{end_line}.",
        cache_mutation,
    )


def _apply_insert_after(
    filepath: str,
    lines: list[str],
    after_ref: str | None,
    new_content: str,
) -> tuple[list[str], str, Callable[[], None]]:
    """Insert new lines after a referenced line."""
    if after_ref is None:
        raise ToolRetryError("The 'after' parameter is required for the 'insert_after' operation.")
    after_line = _validate_ref(filepath, after_ref)
    insert_idx = after_line  # insert after this line

    if insert_idx > len(lines):
        raise ToolRetryError(f"Line {after_line} is out of range (file has {len(lines)} lines).")

    insertion_lines = new_content.splitlines() if new_content else []
    new_lines = lines[:insert_idx] + insertion_lines + lines[insert_idx:]

    def cache_mutation() -> None:
        _cache_replace_range(
            filepath,
            after_line + 1,
            after_line,  # end < start means zero-width range
            insertion_lines,
        )

    return (
        new_lines,
        f"File '{filepath}' updated: inserted {len(insertion_lines)} "
        f"line(s) after line {after_line}.",
        cache_mutation,
    )
