"""TunaCode tools package. Implements lazy loading of submodules for faster startup."""

import importlib
from types import ModuleType


def __getattr__(name: str) -> ModuleType:
    try:
        return importlib.import_module(f".{name}", __name__)
    except ImportError as e:
        raise AttributeError(f"module {__name__} has no attribute '{name}'") from e
