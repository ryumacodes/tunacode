"""Shared ignore logic for discovery tools."""

from __future__ import annotations

from dataclasses import dataclass
from os import DirEntry
from pathlib import Path

from tunacode.configuration.ignore_patterns import (
    DEFAULT_EXCLUDE_DIRS,
    DEFAULT_IGNORE_PATTERNS,
)

from tunacode.tools.ignore_manager import (
    IgnoreManager,
    build_gitignore_path,
    create_ignore_manager,
    get_gitignore_mtime_ns,
    read_gitignore_lines,
    resolve_root,
)


@dataclass(frozen=True)
class IgnoreCacheEntry:
    """Cached ignore manager with gitignore mtime tracking."""

    gitignore_mtime_ns: int
    manager: IgnoreManager


IGNORE_MANAGER_CACHE: dict[Path, IgnoreCacheEntry] = {}


def get_ignore_manager(root: Path) -> IgnoreManager:
    """Get a cached IgnoreManager for the provided root."""

    resolved_root = resolve_root(root)
    gitignore_path = build_gitignore_path(resolved_root)
    gitignore_mtime_ns = get_gitignore_mtime_ns(gitignore_path)

    cache_entry = IGNORE_MANAGER_CACHE.get(resolved_root)
    if cache_entry is not None and cache_entry.gitignore_mtime_ns == gitignore_mtime_ns:
        return cache_entry.manager

    gitignore_lines = read_gitignore_lines(gitignore_path)
    ignore_manager = create_ignore_manager(root=resolved_root, gitignore_lines=gitignore_lines)

    IGNORE_MANAGER_CACHE[resolved_root] = IgnoreCacheEntry(
        gitignore_mtime_ns=gitignore_mtime_ns,
        manager=ignore_manager,
    )

    return ignore_manager


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
