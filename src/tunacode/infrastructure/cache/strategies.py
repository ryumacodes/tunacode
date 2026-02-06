from __future__ import annotations

import os
from pathlib import Path
from typing import Protocol

from tunacode.infrastructure.cache.metadata import MtimeMetadata


class CacheStrategy(Protocol):
    """Strategy interface for cache invalidation."""

    def is_valid(self, *, key: object, _value: object, metadata: object | None) -> bool:
        """Return True if cached (key, value) is still valid."""


class ManualStrategy:
    """A strategy that never auto-invalidates."""

    def is_valid(self, *, key: object, _value: object, metadata: object | None) -> bool:  # noqa: ARG002
        return True


class MtimeStrategy:
    """Invalidate entries when the underlying file mtime changes."""

    def is_valid(self, *, key: object, _value: object, metadata: object | None) -> bool:  # noqa: ARG002
        if metadata is None:
            return False
        if not isinstance(metadata, MtimeMetadata):
            raise TypeError(
                "MtimeStrategy requires MtimeMetadata, "
                f"got {type(metadata).__name__} for key={key!r}"
            )

        path = metadata.path
        current_mtime_ns = _stat_mtime_ns(path)
        return current_mtime_ns == metadata.mtime_ns


MISSING_MTIME_NS = 0


def _stat_mtime_ns(path: Path) -> int:
    try:
        return os.stat(path).st_mtime_ns
    except FileNotFoundError:
        return MISSING_MTIME_NS
