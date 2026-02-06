from __future__ import annotations

from pathlib import Path

from tunacode.infrastructure.cache import ManualStrategy, get_cache, register_cache

RIPGREP_CACHE_NAME = "tunacode.ripgrep"

_PLATFORM_IDENTIFIER_KEY = "platform_identifier"
_BINARY_PATH_KEY = "binary_path"
_BINARY_PATH_NONE_SENTINEL = object()

register_cache(RIPGREP_CACHE_NAME, ManualStrategy())


def get_platform_identifier() -> tuple[str, str] | None:
    cache = get_cache(RIPGREP_CACHE_NAME)
    cached = cache.get(_PLATFORM_IDENTIFIER_KEY)
    if cached is None:
        return None
    if not isinstance(cached, tuple) or len(cached) != 2:
        raise TypeError(
            f"Ripgrep platform identifier cache value must be (str, str) tuple, got {cached!r}"
        )

    platform_key, system = cached
    if not isinstance(platform_key, str) or not isinstance(system, str):
        raise TypeError(
            f"Ripgrep platform identifier cache value must be (str, str) tuple, got {cached!r}"
        )

    return platform_key, system


def set_platform_identifier(platform_key: str, system: str) -> None:
    get_cache(RIPGREP_CACHE_NAME).set(_PLATFORM_IDENTIFIER_KEY, (platform_key, system))


def try_get_binary_path() -> tuple[bool, Path | None]:
    cache = get_cache(RIPGREP_CACHE_NAME)
    cached = cache.get(_BINARY_PATH_KEY)
    if cached is None:
        return False, None
    if cached is _BINARY_PATH_NONE_SENTINEL:
        return True, None
    if not isinstance(cached, Path):
        raise TypeError(
            f"Ripgrep binary path cache value must be Path or sentinel, got {type(cached).__name__}"
        )
    return True, cached


def set_binary_path(path: Path | None) -> None:
    value = _BINARY_PATH_NONE_SENTINEL if path is None else path
    get_cache(RIPGREP_CACHE_NAME).set(_BINARY_PATH_KEY, value)


def clear_ripgrep_cache() -> None:
    get_cache(RIPGREP_CACHE_NAME).clear()
