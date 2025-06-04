"""TunaCode tools package. Implements lazy loading of submodules for faster startup."""

import importlib


def __getattr__(name):
    try:
        return importlib.import_module(f".{name}", __name__)
    except ImportError as e:
        raise AttributeError(f"module {__name__} has no attribute '{name}'") from e
