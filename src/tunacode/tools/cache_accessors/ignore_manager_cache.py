from __future__ import annotations

from pathlib import Path

from tunacode.tools.ignore_manager import (
    IgnoreManager,
    build_gitignore_path,
    create_ignore_manager,
    get_gitignore_mtime_ns,
    read_gitignore_lines,
    resolve_root,
)

from tunacode.infrastructure.cache import MtimeMetadata, MtimeStrategy, get_cache, register_cache

IGNORE_MANAGER_CACHE_NAME = "tunacode.ignore_manager"

register_cache(IGNORE_MANAGER_CACHE_NAME, MtimeStrategy())


def get_ignore_manager(root: Path) -> IgnoreManager:
    """Return a cached IgnoreManager for the provided root.

    The cache is invalidated when the root's .gitignore mtime changes.
    """

    resolved_root = resolve_root(root)

    cache = get_cache(IGNORE_MANAGER_CACHE_NAME)

    cached = cache.get(resolved_root)
    if cached is not None:
        if not isinstance(cached, IgnoreManager):
            raise TypeError(
                f"Ignore manager cache value must be IgnoreManager, got {type(cached).__name__}"
            )
        return cached

    gitignore_path = build_gitignore_path(resolved_root)
    gitignore_mtime_ns = get_gitignore_mtime_ns(gitignore_path)
    gitignore_lines = read_gitignore_lines(gitignore_path)

    ignore_manager = create_ignore_manager(root=resolved_root, gitignore_lines=gitignore_lines)

    cache.set(resolved_root, ignore_manager)
    cache.set_metadata(
        resolved_root,
        MtimeMetadata(path=gitignore_path, mtime_ns=gitignore_mtime_ns),
    )

    return ignore_manager


def invalidate_ignore_manager(root: Path) -> bool:
    resolved_root = resolve_root(root)
    return get_cache(IGNORE_MANAGER_CACHE_NAME).delete(resolved_root)


def clear_ignore_manager_cache() -> None:
    get_cache(IGNORE_MANAGER_CACHE_NAME).clear()
