"""Cache infrastructure.

This package provides a small, strict cache subsystem used by higher-level typed
accessors (see follow-up tickets in epic tun-gqgx).

Design goals:
- central registration (fail loud on unknown caches)
- pluggable invalidation strategies (manual, mtime-based)
- deterministic clearing for tests
"""

from __future__ import annotations

from tunacode.infrastructure.cache.manager import Cache, CacheManager
from tunacode.infrastructure.cache.metadata import MtimeMetadata
from tunacode.infrastructure.cache.strategies import CacheStrategy, ManualStrategy, MtimeStrategy


def get_cache_manager() -> CacheManager:
    return CacheManager.get_instance()


def register_cache(name: str, strategy: CacheStrategy) -> None:
    get_cache_manager().register_cache(name=name, strategy=strategy)


def get_cache(name: str) -> Cache:
    return get_cache_manager().get_cache(name=name)


def set_metadata(cache_name: str, key: object, metadata: object) -> None:
    get_cache_manager().set_metadata(cache_name=cache_name, key=key, metadata=metadata)


def get_metadata(cache_name: str, key: object) -> object | None:
    return get_cache_manager().get_metadata(cache_name=cache_name, key=key)


def clear_cache(name: str) -> None:
    get_cache_manager().clear_cache(name=name)


def clear_all() -> None:
    get_cache_manager().clear_all()


__all__ = [
    "Cache",
    "CacheManager",
    "CacheStrategy",
    "ManualStrategy",
    "MtimeStrategy",
    "MtimeMetadata",
    "clear_all",
    "clear_cache",
    "get_cache",
    "get_cache_manager",
    "get_metadata",
    "register_cache",
    "set_metadata",
]
