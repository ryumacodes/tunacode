from __future__ import annotations

import os
from pathlib import Path

from tunacode.infrastructure.cache import MtimeMetadata, MtimeStrategy, get_cache, register_cache

XML_PROMPTS_CACHE_NAME = "tunacode.xml.prompts"
XML_PROMPT_NONE_SENTINEL = object()

register_cache(XML_PROMPTS_CACHE_NAME, MtimeStrategy())


def try_get_prompt(tool_name: str) -> tuple[bool, str | None]:
    cache = get_cache(XML_PROMPTS_CACHE_NAME)
    cached = cache.get(tool_name)
    if cached is None:
        return False, None
    if cached is XML_PROMPT_NONE_SENTINEL:
        return True, None
    if not isinstance(cached, str):
        raise TypeError(
            f"XML prompt cache value must be str or sentinel, got {type(cached).__name__}"
        )
    return True, cached


def set_prompt(tool_name: str, *, prompt: str | None, file_path: Path) -> None:
    cache = get_cache(XML_PROMPTS_CACHE_NAME)

    value = XML_PROMPT_NONE_SENTINEL if prompt is None else prompt
    cache.set(tool_name, value)

    mtime_ns = _stat_mtime_ns(file_path)
    cache.set_metadata(tool_name, MtimeMetadata(path=file_path, mtime_ns=mtime_ns))


def clear_xml_prompts_cache() -> None:
    get_cache(XML_PROMPTS_CACHE_NAME).clear()


def _stat_mtime_ns(path: Path) -> int:
    try:
        return os.stat(path).st_mtime_ns
    except FileNotFoundError:
        return 0
