"""Prompt version cache with mtime-based invalidation.

Caches PromptVersion objects to avoid recomputing SHA-256 hashes
on every agent creation. Invalidates when file modification time changes.
"""

from __future__ import annotations

from pathlib import Path

from tunacode.types.canonical import PromptVersion

from tunacode.infrastructure.cache import (
    MtimeMetadata,
    MtimeStrategy,
    get_cache,
    register_cache,
    stat_mtime_ns,
)

PROMPT_VERSION_CACHE_NAME = "tunacode.prompt_versions"

register_cache(PROMPT_VERSION_CACHE_NAME, MtimeStrategy())


def get_prompt_version(path: Path) -> PromptVersion | None:
    """Return cached PromptVersion for the file at path.

    The cache is mtime-aware (nanoseconds). Returns None if:
    - File doesn't exist
    - File mtime has changed (cache miss)

    Args:
        path: Path to the prompt file.

    Returns:
        Cached PromptVersion if file unchanged, None otherwise.
    """
    resolved_path = path.resolve()

    if not resolved_path.exists():
        return None

    cache = get_cache(PROMPT_VERSION_CACHE_NAME)

    cached = cache.get(resolved_path)
    if cached is not None:
        if not isinstance(cached, PromptVersion):
            raise TypeError(
                f"Prompt version cache value must be PromptVersion, got {type(cached).__name__}"
            )
        return cached

    return None


def set_prompt_version(path: Path, version: PromptVersion) -> None:
    """Store a PromptVersion in the cache with mtime metadata.

    Args:
        path: Path to the prompt file.
        version: PromptVersion to cache.
    """
    resolved_path = path.resolve()
    cache = get_cache(PROMPT_VERSION_CACHE_NAME)

    cache.set(resolved_path, version)
    cache.set_metadata(
        resolved_path,
        MtimeMetadata(path=resolved_path, mtime_ns=stat_mtime_ns(resolved_path)),
    )


def invalidate_prompt_version(path: Path) -> bool:
    """Invalidate cached PromptVersion for a specific file.

    Args:
        path: Path to the prompt file.

    Returns:
        True if an entry was invalidated, False if not cached.
    """
    resolved_path = path.resolve()
    return get_cache(PROMPT_VERSION_CACHE_NAME).delete(resolved_path)


def clear_prompt_versions() -> None:
    """Clear all cached prompt versions."""
    get_cache(PROMPT_VERSION_CACHE_NAME).clear()


__all__ = [
    "get_prompt_version",
    "set_prompt_version",
    "invalidate_prompt_version",
    "clear_prompt_versions",
    "PROMPT_VERSION_CACHE_NAME",
]
