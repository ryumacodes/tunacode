"""Shared ignore logic for discovery tools."""

from __future__ import annotations

from os import DirEntry
from pathlib import Path

from tunacode.configuration.ignore_patterns import (
    DEFAULT_EXCLUDE_DIRS,
    DEFAULT_IGNORE_PATTERNS,
)

from tunacode.tools.ignore_manager import IgnoreManager

from tunacode.infrastructure.cache.caches.ignore_manager import (
    get_ignore_manager as _get_cached_ignore_manager,
)


def get_ignore_manager(root: Path) -> IgnoreManager:
    """Return a cached IgnoreManager for the provided root."""

    return _get_cached_ignore_manager(root)


def traverse_gitignore(
    entry: DirEntry,
    ignore_manager: IgnoreManager,
    recursive: bool,
    stack: list[Path],
) -> bool:
    """Bypass the gitignore filtering directory."""

    entry_path = Path(entry.path)

    if entry.is_dir(follow_symlinks=False):
        if not recursive:
            return True
        if ignore_manager.should_ignore_dir(entry_path):
            return True
        stack.append(entry_path)
        return True

    if not entry.is_file(follow_symlinks=False):
        return True

    return ignore_manager.should_ignore(entry_path)


__all__ = [
    "DEFAULT_EXCLUDE_DIRS",
    "DEFAULT_IGNORE_PATTERNS",
    "IgnoreManager",
    "get_ignore_manager",
    "traverse_gitignore",
]
