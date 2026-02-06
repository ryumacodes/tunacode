from __future__ import annotations

import os
from pathlib import Path

from tunacode.infrastructure.cache import MtimeMetadata, MtimeStrategy, get_cache, register_cache

TUNACODE_CONTEXT_CACHE_NAME = "tunacode.context"

CONTEXT_HEADER_PREFIX = "\n\n# Project Context from {file_name}\n"
TEXT_ENCODING = "utf-8"
MISSING_MTIME_NS = 0

register_cache(TUNACODE_CONTEXT_CACHE_NAME, MtimeStrategy())


def get_context(path: Path) -> str:
    """Return cached Project Context content for the file at path.

    The cache is mtime-aware (nanoseconds). Missing files are treated as mtime_ns=0.
    """

    resolved_path = path.resolve()
    cache_key = resolved_path

    cache = get_cache(TUNACODE_CONTEXT_CACHE_NAME)

    cached = cache.get(cache_key)
    if cached is not None:
        if not isinstance(cached, str):
            raise TypeError(f"Context cache value must be str, got {type(cached).__name__}")
        return cached

    context = _load_context(resolved_path)
    cache.set(cache_key, context)

    mtime_ns = _get_mtime_ns(resolved_path)
    cache.set_metadata(cache_key, MtimeMetadata(path=resolved_path, mtime_ns=mtime_ns))

    return context


def invalidate_context(path: Path) -> bool:
    resolved_path = path.resolve()
    return get_cache(TUNACODE_CONTEXT_CACHE_NAME).delete(resolved_path)


def clear_context_cache() -> None:
    get_cache(TUNACODE_CONTEXT_CACHE_NAME).clear()


def _get_mtime_ns(path: Path) -> int:
    try:
        return os.stat(path).st_mtime_ns
    except FileNotFoundError:
        return MISSING_MTIME_NS


def _load_context(path: Path) -> str:
    try:
        content = path.read_text(encoding=TEXT_ENCODING)
    except FileNotFoundError:
        return ""

    if not content.strip():
        return ""

    header = CONTEXT_HEADER_PREFIX.format(file_name=path.name)
    return f"{header}{content}"
