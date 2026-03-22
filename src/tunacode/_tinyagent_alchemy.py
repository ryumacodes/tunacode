"""Compatibility helpers for tinyagent alchemy binding discovery."""

from __future__ import annotations

import importlib
import sys
from types import ModuleType

TINYAGENT_ALCHEMY_MODULE = "tinyagent._alchemy"
EXTERNAL_ALCHEMY_MODULE = "_alchemy"


def prefer_external_tinyagent_alchemy() -> ModuleType | None:
    """Alias a working external `_alchemy` module as `tinyagent._alchemy`.

    tinyagent's loader currently tries `tinyagent._alchemy` before the top-level
    `_alchemy` module. On some macOS arm64 installs the bundled wheel is broken
    while an externally installed `_alchemy` binding works. Registering the
    external module under the package-qualified name lets TunaCode use the
    working binding without mutating site-packages.
    """

    existing_module = sys.modules.get(TINYAGENT_ALCHEMY_MODULE)
    if existing_module is not None:
        return existing_module

    try:
        external_module = importlib.import_module(EXTERNAL_ALCHEMY_MODULE)
    except Exception:
        return None

    sys.modules.setdefault(TINYAGENT_ALCHEMY_MODULE, external_module)
    alchemy_provider_module = sys.modules.get("tinyagent.alchemy_provider")
    if alchemy_provider_module is not None:
        alchemy_provider_module._ALCHEMY_MODULE = external_module  # type: ignore[attr-defined]
    return external_module
