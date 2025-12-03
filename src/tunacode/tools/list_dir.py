"""Directory listing tool for agent operations."""

import asyncio
import logging
import os
from pathlib import Path
from typing import List, Tuple

from tunacode.tools.decorators import base_tool

logger = logging.getLogger(__name__)


@base_tool
async def list_dir(
    directory: str = ".", max_entries: int = 200, show_hidden: bool = False
) -> str:
    """List the contents of a directory.

    Args:
        directory: The path to the directory to list (defaults to current directory).
        max_entries: Maximum number of entries to return (default: 200).
        show_hidden: Whether to include hidden files/directories (default: False).

    Returns:
        Formatted list of directory contents.
    """
    dir_path = Path(directory).resolve()

    if not dir_path.exists():
        raise FileNotFoundError(f"Directory not found: {dir_path}")

    if not dir_path.is_dir():
        raise NotADirectoryError(f"Not a directory: {dir_path}")

    # Try CodeIndex cache first
    cached = _try_cache(dir_path, show_hidden, max_entries)
    if cached:
        return cached

    # Scan directory in background thread
    entries = await asyncio.to_thread(_scan_directory, dir_path, show_hidden)

    # Sort: directories first, then files, both alphabetically
    entries.sort(key=lambda x: (not x[1], x[0].lower()))

    # Update cache
    _update_cache(dir_path, entries)

    return _format_output(dir_path, entries, max_entries)


def _try_cache(dir_path: Path, show_hidden: bool, max_entries: int) -> str | None:
    """Try to get directory contents from CodeIndex cache."""
    try:
        from tunacode.indexing import CodeIndex

        index = CodeIndex.get_instance()
        cached = index.get_directory_contents(dir_path)

        if cached:
            if not show_hidden:
                cached = [name for name in cached if not name.startswith(".")]

            limited = cached[:max_entries]
            if limited:
                return f"Files in {dir_path}:\n" + "\n".join(f"  {name}" for name in limited)
            return f"Directory {dir_path} is empty"
    except Exception as e:
        logger.debug(f"CodeIndex cache miss for {dir_path}: {e}")
    return None


def _scan_directory(path: Path, show_hidden: bool) -> List[Tuple[str, bool, str]]:
    """Scan directory and return entry metadata (name, is_dir, type_indicator)."""
    collected: List[Tuple[str, bool, str]] = []

    with os.scandir(path) as scanner:
        for entry in scanner:
            if not show_hidden and entry.name.startswith("."):
                continue

            try:
                is_directory = entry.is_dir(follow_symlinks=False)
                is_symlink = entry.is_symlink()

                if is_symlink:
                    indicator = "@"
                elif is_directory:
                    indicator = "/"
                elif entry.is_file():
                    indicator = "*" if os.access(entry.path, os.X_OK) else ""
                else:
                    indicator = "?"

                collected.append((entry.name, is_directory, indicator))
            except (OSError, PermissionError):
                collected.append((entry.name, False, "?"))

    return collected


def _update_cache(dir_path: Path, entries: List[Tuple[str, bool, str]]) -> None:
    """Update CodeIndex cache with scanned entries."""
    try:
        from tunacode.indexing import CodeIndex

        index = CodeIndex.get_instance()
        names = [name for name, _, _ in entries]
        index.update_directory_cache(dir_path, names)
    except Exception as e:
        logger.debug(f"Failed to update CodeIndex cache for {dir_path}: {e}")


def _format_output(
    dir_path: Path, entries: List[Tuple[str, bool, str]], max_entries: int
) -> str:
    """Format directory listing output."""
    total_entries = len(entries)

    if total_entries > max_entries:
        entries = entries[:max_entries]

    if not entries:
        return f"Directory '{dir_path}' is empty"

    lines = [f"Contents of '{dir_path}':", ""]

    max_name_len = max(len(name) for name, _, _ in entries)
    col_width = min(max_name_len + 2, 50)

    for name, is_dir, indicator in entries:
        display_name = name[:44] + "..." if len(name) > 47 else name
        display_name += indicator
        entry_type = "[DIR]" if is_dir else "[FILE]"
        lines.append(f"  {display_name:<{col_width}} {entry_type}")

    displayed = len(entries)
    dir_count = sum(1 for _, is_dir, _ in entries if is_dir)
    file_count = displayed - dir_count

    lines.extend([
        "",
        f"Total: {displayed} entries ({dir_count} directories, {file_count} files)",
    ])

    if total_entries > max_entries:
        lines.append(f"Note: Output limited to {max_entries} entries")

    return "\n".join(lines)
