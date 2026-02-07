from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

MISSING_MTIME_NS = 0


def stat_mtime_ns(path: Path) -> int:
    """Return file mtime (ns), or 0 when the file is missing.

    Mtime-driven caches treat missing files as mtime_ns=0.
    """

    try:
        return os.stat(path).st_mtime_ns
    except FileNotFoundError:
        return MISSING_MTIME_NS


@dataclass(frozen=True, slots=True)
class MtimeMetadata:
    """Metadata required by :class:`~tunacode.infrastructure.cache.strategies.MtimeStrategy`."""

    path: Path
    mtime_ns: int
