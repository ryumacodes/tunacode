"""Glob tool for fast file pattern matching."""

import asyncio
import fnmatch
import os
import re
from enum import Enum
from pathlib import Path

from tunacode.exceptions import ToolRetryError

from tunacode.tools.decorators import base_tool
from tunacode.tools.ignore import IgnoreManager, get_ignore_manager, traverse_gitignore

MAX_RESULTS = 5000
EXCLUDE_DIR_SUFFIX = "/"
EMPTY_EXCLUDE_DIR_PATTERNS: tuple[str, ...] = ()


class SortOrder(Enum):
    """Sorting options for glob results."""

    MODIFIED = "modified"
    SIZE = "size"
    ALPHABETICAL = "alphabetical"
    DEPTH = "depth"


@base_tool
async def glob(
    pattern: str,
    directory: str = ".",
    recursive: bool = True,
    include_hidden: bool = False,
    exclude_dirs: list[str] | None = None,
    max_results: int = MAX_RESULTS,
    sort_by: str = "modified",
    case_sensitive: bool = False,
) -> str:
    """Find files matching glob patterns.

    Args:
        pattern: Glob pattern to match (e.g., "*.py", "**/*.{js,ts}").
        directory: Directory to search in (default: current directory).
        recursive: Whether to search recursively (default: True).
        include_hidden: Whether to include hidden files/directories.
        exclude_dirs: Additional directories to exclude from search.
        max_results: Maximum number of results to return.
        sort_by: How to sort results (modified/size/alphabetical/depth).
        case_sensitive: Whether pattern matching is case-sensitive.

    Returns:
        Formatted list of matching file paths.
    """
    root_path = Path(directory).resolve()
    if not root_path.exists():
        raise ToolRetryError(f"Directory not found: {directory}. Check the path.")
    if not root_path.is_dir():
        raise ToolRetryError(f"Not a directory: {directory}. Provide a directory path.")

    ignore_manager = _build_ignore_manager(root_path, exclude_dirs)
    sort_order = _parse_sort_order(sort_by)
    patterns = _expand_brace_pattern(pattern)

    matches = await _glob_filesystem(
        root_path,
        patterns,
        recursive,
        include_hidden,
        ignore_manager,
        max_results,
        case_sensitive,
    )

    if not matches:
        return f"No files found matching pattern: {pattern}"

    matches = await _sort_matches(matches, sort_order)
    return _format_output(pattern, matches, max_results)


def _parse_sort_order(sort_by: str) -> SortOrder:
    """Parse sort order string to enum."""
    try:
        return SortOrder(sort_by)
    except ValueError:
        return SortOrder.MODIFIED


def _build_ignore_manager(root: Path, exclude_dirs: list[str] | None) -> IgnoreManager:
    ignore_manager = get_ignore_manager(root)
    exclude_patterns = _normalize_exclude_dir_patterns(exclude_dirs)
    if not exclude_patterns:
        return ignore_manager
    return ignore_manager.with_additional_patterns(exclude_patterns)


def _normalize_exclude_dir_patterns(exclude_dirs: list[str] | None) -> tuple[str, ...]:
    if not exclude_dirs:
        return EMPTY_EXCLUDE_DIR_PATTERNS
    patterns: list[str] = []
    for name in exclude_dirs:
        stripped_name = name.strip()
        if not stripped_name:
            continue
        has_suffix = stripped_name.endswith(EXCLUDE_DIR_SUFFIX)
        pattern = stripped_name if has_suffix else f"{stripped_name}{EXCLUDE_DIR_SUFFIX}"
        patterns.append(pattern)
    return tuple(patterns)


def _expand_brace_pattern(pattern: str) -> list[str]:
    """Expand brace patterns like "*.{py,js,ts}" into multiple patterns."""
    if "{" not in pattern or "}" not in pattern:
        return [pattern]

    expanded = []
    stack = [pattern]

    while stack:
        current = stack.pop()
        start = -1
        depth = 0

        for i, char in enumerate(current):
            if char == "{":
                if depth == 0:
                    start = i
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0 and start != -1:
                    prefix = current[:start]
                    suffix = current[i + 1 :]
                    options = current[start + 1 : i].split(",")

                    for option in options:
                        new_pattern = prefix + option.strip() + suffix
                        if "{" in new_pattern:
                            stack.append(new_pattern)
                        else:
                            expanded.append(new_pattern)
                    break
        else:
            expanded.append(current)

    return expanded


def _compile_patterns(patterns: list[str], flags: int) -> list[tuple[str, re.Pattern[str]]]:
    """Compile glob patterns into regex patterns for matching."""
    compiled: list[tuple[str, re.Pattern[str]]] = []
    for pat in patterns:
        if "**" in pat:
            regex_pat = pat.replace("**", "__STARSTAR__")
            regex_pat = fnmatch.translate(regex_pat)
            regex_pat = regex_pat.replace("__STARSTAR__", ".*")
            compiled.append((pat, re.compile(regex_pat, flags)))
        else:
            compiled.append((pat, re.compile(fnmatch.translate(pat), flags)))
    return compiled


def _single_pattern_matches(
    entry_name: str,
    rel_path: str,
    orig: str,
    comp: re.Pattern[str],
    recursive: bool,
) -> bool:
    """Check if a single compiled pattern matches the entry."""
    if "**" not in orig:
        return bool(comp.match(entry_name))
    if orig.startswith("**/") and not recursive:
        return fnmatch.fnmatch(entry_name, orig[3:])
    if comp.match(rel_path):
        return True
    if orig.startswith("**/"):
        return fnmatch.fnmatch(entry_name, orig[3:])
    return False


def _entry_matches_any_pattern(
    entry_name: str,
    rel_path: str,
    compiled: list[tuple[str, re.Pattern[str]]],
    recursive: bool,
) -> bool:
    """Check if an entry matches any of the compiled patterns."""
    for orig, comp in compiled:
        if _single_pattern_matches(entry_name, rel_path, orig, comp, recursive):
            return True
    return False


def _should_skip_entry(
    entry: os.DirEntry[str],
    include_hidden: bool,
    ignore_manager: IgnoreManager,
    recursive: bool,
    stack: list[Path],
) -> bool:
    """Check if a directory entry should be skipped."""
    if entry.name.startswith(".") and not include_hidden:
        return True
    return traverse_gitignore(entry, ignore_manager, recursive, stack)


def _scan_directory(
    current: Path,
    root: Path,
    compiled: list[tuple[str, re.Pattern[str]]],
    recursive: bool,
    include_hidden: bool,
    ignore_manager: IgnoreManager,
    stack: list[Path],
    matches: list[str],
    max_results: int,
) -> None:
    """Scan a single directory for matching entries."""
    try:
        with os.scandir(current) as entries:
            for entry in entries:
                if _should_skip_entry(entry, include_hidden, ignore_manager, recursive, stack):
                    continue
                rel_path = os.path.relpath(entry.path, root)
                if _entry_matches_any_pattern(entry.name, rel_path, compiled, recursive):
                    matches.append(entry.path)
                if len(matches) >= max_results:
                    break
    except (PermissionError, OSError):
        pass


def _search_sync(
    root: Path,
    patterns: list[str],
    recursive: bool,
    include_hidden: bool,
    ignore_manager: IgnoreManager,
    max_results: int,
    case_sensitive: bool,
) -> list[str]:
    """Synchronous glob search using os.scandir."""
    matches: list[str] = []
    stack = [root]
    flags = 0 if case_sensitive else re.IGNORECASE
    compiled = _compile_patterns(patterns, flags)

    while stack:
        if len(matches) >= max_results:
            break
        current = stack.pop()
        _scan_directory(
            current,
            root,
            compiled,
            recursive,
            include_hidden,
            ignore_manager,
            stack,
            matches,
            max_results,
        )

    return matches[:max_results]


async def _glob_filesystem(
    root: Path,
    patterns: list[str],
    recursive: bool,
    include_hidden: bool,
    ignore_manager: IgnoreManager,
    max_results: int,
    case_sensitive: bool,
) -> list[str]:
    """Perform glob search using os.scandir."""
    return await asyncio.to_thread(
        _search_sync,
        root,
        patterns,
        recursive,
        include_hidden,
        ignore_manager,
        max_results,
        case_sensitive,
    )


async def _sort_matches(matches: list[str], sort_by: SortOrder) -> list[str]:
    """Sort matches based on the specified order."""
    if not matches:
        return matches

    def sort_sync() -> list[str]:
        if sort_by == SortOrder.MODIFIED:
            return sorted(matches, key=lambda p: os.path.getmtime(p), reverse=True)
        if sort_by == SortOrder.SIZE:
            return sorted(matches, key=lambda p: os.path.getsize(p), reverse=True)
        if sort_by == SortOrder.DEPTH:
            return sorted(matches, key=lambda p: (p.count(os.sep), p))
        return sorted(matches)

    return await asyncio.to_thread(sort_sync)


def _format_output(pattern: str, matches: list[str], max_results: int) -> str:
    """Format glob results with header for rich panel parsing.

    Args:
        pattern: The glob pattern used.
        matches: List of matching file paths.
        max_results: Maximum results limit.

    Returns:
        Formatted output with file count header.
    """
    file_count = len(matches)
    file_word = "file" if file_count == 1 else "files"
    parts = [f"Found {file_count} {file_word} matching pattern: {pattern}"]

    if matches:
        parts.append("")  # Blank line
        parts.extend(matches)

    if file_count == max_results:
        parts.append(f"(truncated at {max_results})")

    return "\n".join(parts)
