from __future__ import annotations

import threading
from dataclasses import dataclass

from tunacode.infrastructure.cache.strategies import CacheStrategy


@dataclass(frozen=True, slots=True)
class _CacheEntry:
    value: object


class Cache:
    """A single named cache with a strategy and per-key metadata."""

    def __init__(self, *, name: str, strategy: CacheStrategy) -> None:
        self._name = name
        self._strategy = strategy
        self._values: dict[object, _CacheEntry] = {}
        self._metadata: dict[object, object] = {}
        self._lock = threading.RLock()

    @property
    def name(self) -> str:
        return self._name

    def get(self, key: object) -> object | None:
        with self._lock:
            entry = self._values.get(key)
            if entry is None:
                return None

            metadata = self._metadata.get(key)
            is_valid = self._strategy.is_valid(key=key, _value=entry.value, metadata=metadata)
            if is_valid:
                return entry.value

            self._values.pop(key, None)
            self._metadata.pop(key, None)
            return None

    def set(self, key: object, value: object) -> None:
        with self._lock:
            self._values[key] = _CacheEntry(value=value)

    def set_metadata(self, key: object, metadata: object) -> None:
        with self._lock:
            self._metadata[key] = metadata

    def get_metadata(self, key: object) -> object | None:
        with self._lock:
            return self._metadata.get(key)

    def delete(self, key: object) -> bool:
        with self._lock:
            had_entry = key in self._values or key in self._metadata
            self._values.pop(key, None)
            self._metadata.pop(key, None)
            return had_entry

    def clear(self) -> None:
        with self._lock:
            self._values.clear()
            self._metadata.clear()


class CacheManager:
    """Global cache registry.

    Notes:
        This is a stable singleton without a reset_instance() method.
        Tests should use clear_cache()/clear_all() for deterministic cleanup.
    """

    _instance: CacheManager | None = None
    _instance_lock = threading.RLock()

    def __init__(self) -> None:
        self._caches: dict[str, Cache] = {}
        self._lock = threading.RLock()

    @classmethod
    def get_instance(cls) -> CacheManager:
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def register_cache(self, *, name: str, strategy: CacheStrategy) -> None:
        with self._lock:
            if name in self._caches:
                raise ValueError(f"Cache already registered: {name}")
            self._caches[name] = Cache(name=name, strategy=strategy)

    def get_cache(self, *, name: str) -> Cache:
        with self._lock:
            try:
                return self._caches[name]
            except KeyError as exc:
                raise KeyError(f"Cache not registered: {name}") from exc

    def set_metadata(self, *, cache_name: str, key: object, metadata: object) -> None:
        cache = self.get_cache(name=cache_name)
        cache.set_metadata(key, metadata)

    def get_metadata(self, *, cache_name: str, key: object) -> object | None:
        cache = self.get_cache(name=cache_name)
        return cache.get_metadata(key)

    def clear_cache(self, *, name: str) -> None:
        cache = self.get_cache(name=name)
        cache.clear()

    def clear_all(self) -> None:
        with self._lock:
            # Deterministic: clear each registered cache's values+metadata.
            for cache in self._caches.values():
                cache.clear()
