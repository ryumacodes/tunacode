"""Utility for import caching and lazy importing heavy modules."""

import importlib

_import_cache = {}


def lazy_import(module_name: str):
    if module_name not in _import_cache:
        _import_cache[module_name] = importlib.import_module(module_name)
    return _import_cache[module_name]
