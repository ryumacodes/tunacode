from __future__ import annotations

from pathlib import Path

from tunacode.infrastructure.cache import (
    MtimeMetadata,
    MtimeStrategy,
    get_cache,
    register_cache,
    stat_mtime_ns,
)

TUNACODE_CONTEXT_CACHE_NAME = "tunacode.context"

CONTEXT_HEADER_PREFIX = "\n\n# Project Context from {file_name}\n"
TEXT_ENCODING = "utf-8"

register_cache(TUNACODE_CONTEXT_CACHE_NAME, MtimeStrategy())


def get_context(path: Path) -> str:
    """Return cached Project Context content for the file at path.

    The cache is mtime-aware (nanoseconds). Missing files are treated as mtime_ns=0.
    """

    resolved_path = path.resolve()

    cache = get_cache(TUNACODE_CONTEXT_CACHE_NAME)

    cached = cache.get(resolved_path)
    if cached is not None:
        if not isinstance(cached, str):
            raise TypeError(f"Context cache value must be str, got {type(cached).__name__}")
        return cached

    context = _load_context(resolved_path)
    cache.set(resolved_path, context)

    cache.set_metadata(
        resolved_path,
        MtimeMetadata(path=resolved_path, mtime_ns=stat_mtime_ns(resolved_path)),
    )

    return context


def invalidate_context(path: Path) -> bool:
    resolved_path = path.resolve()
    return get_cache(TUNACODE_CONTEXT_CACHE_NAME).delete(resolved_path)


def clear_context_cache() -> None:
    get_cache(TUNACODE_CONTEXT_CACHE_NAME).clear()


def _load_context(path: Path) -> str:
    try:
        content = path.read_text(encoding=TEXT_ENCODING)
    except FileNotFoundError:
        return ""

    if not content.strip():
        return ""

    header = CONTEXT_HEADER_PREFIX.format(file_name=path.name)
    return f"{header}{content}"
