"""Typed cache accessors.

Each module in this package owns:
- a cache name
- cache registration (at import time)
- a typed API for interacting with that cache

Call sites should prefer these accessors over touching CacheManager directly.
"""

from __future__ import annotations
