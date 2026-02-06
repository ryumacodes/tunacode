from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class MtimeMetadata:
    """Metadata required by :class:`~tunacode.infrastructure.cache.strategies.MtimeStrategy`."""

    path: Path
    mtime_ns: int
