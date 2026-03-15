"""TunaCode UI layer - Textual-based TUI.

Keep package import thin so submodules like ``tunacode.ui.main`` do not pay for
full Textual app imports unless they actually need them.
"""

from __future__ import annotations

import importlib
from typing import Any


def __getattr__(name: str) -> Any:
    if name == "TextualReplApp":
        return importlib.import_module(".app", __name__).TextualReplApp
    if name == "run_textual_repl":
        return importlib.import_module(".repl_support", __name__).run_textual_repl
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
