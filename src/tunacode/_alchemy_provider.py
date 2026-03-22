"""TunaCode wrapper around tinyagent's alchemy provider."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

from tunacode._tinyagent_alchemy import prefer_external_tinyagent_alchemy

prefer_external_tinyagent_alchemy()

_alchemy_provider = importlib.import_module("tinyagent.alchemy_provider")

_openai_compat_model = _alchemy_provider.OpenAICompatModel
stream_alchemy_openai_completions = _alchemy_provider.stream_alchemy_openai_completions

if TYPE_CHECKING:
    from tinyagent.alchemy_provider import OpenAICompatModel


def __getattr__(name: str) -> object:
    if name == "OpenAICompatModel":
        return _openai_compat_model
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = ["OpenAICompatModel", "stream_alchemy_openai_completions"]
