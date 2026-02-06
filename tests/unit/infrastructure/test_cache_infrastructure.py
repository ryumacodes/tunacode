from __future__ import annotations

import os
import uuid
from pathlib import Path

import pytest

from tunacode.infrastructure.cache import (
    ManualStrategy,
    MtimeMetadata,
    MtimeStrategy,
    clear_all,
    get_cache,
    register_cache,
    set_metadata,
)


def _unique_cache_name(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex}"


def test_get_cache_on_unregistered_raises() -> None:
    name = _unique_cache_name("unregistered")

    with pytest.raises(KeyError, match=r"Cache not registered"):
        get_cache(name)


def test_manual_strategy_never_auto_invalidates() -> None:
    name = _unique_cache_name("manual")
    register_cache(name, ManualStrategy())

    cache = get_cache(name)
    cache.set("k", "v")

    assert cache.get("k") == "v"


def test_mtime_strategy_invalidates_on_mtime_change(tmp_path: Path) -> None:
    name = _unique_cache_name("mtime")
    register_cache(name, MtimeStrategy())

    path = tmp_path / "example.txt"
    path.write_text("one")

    original_mtime_ns = os.stat(path).st_mtime_ns

    cache = get_cache(name)
    cache.set("k", "v")
    set_metadata(name, "k", MtimeMetadata(path=path, mtime_ns=original_mtime_ns))

    assert cache.get("k") == "v"

    new_mtime_ns = original_mtime_ns + 1_000_000
    os.utime(path, ns=(new_mtime_ns, new_mtime_ns))

    assert cache.get("k") is None
    assert cache.get("k") is None


def test_clear_all_clears_values_and_metadata() -> None:
    name_a = _unique_cache_name("clear-a")
    name_b = _unique_cache_name("clear-b")

    register_cache(name_a, ManualStrategy())
    register_cache(name_b, ManualStrategy())

    cache_a = get_cache(name_a)
    cache_b = get_cache(name_b)

    cache_a.set("k", "v")
    cache_a.set_metadata("k", object())

    cache_b.set("k", "v")
    cache_b.set_metadata("k", object())

    clear_all()

    assert cache_a.get("k") is None
    assert cache_a.get_metadata("k") is None

    assert cache_b.get("k") is None
    assert cache_b.get_metadata("k") is None
