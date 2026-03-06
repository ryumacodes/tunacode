from __future__ import annotations

# ruff: noqa: I001

from pathlib import Path

from tunacode.skills.models import LoadedSkill, SkillSummary

from tunacode.infrastructure.cache import (
    MtimeMetadata,
    MtimeStrategy,
    get_cache,
    register_cache,
    stat_mtime_ns,
)

SKILLS_CACHE_NAME = "tunacode.skills"
SUMMARY_KEY_PREFIX = "summary"
LOADED_KEY_PREFIX = "loaded"

register_cache(SKILLS_CACHE_NAME, MtimeStrategy())


def get_skill_summary(path: Path) -> SkillSummary | None:
    cache_key = _build_cache_key(SUMMARY_KEY_PREFIX, path)
    cached = get_cache(SKILLS_CACHE_NAME).get(cache_key)
    if cached is None:
        return None
    if not isinstance(cached, SkillSummary):
        raise TypeError(
            f"Skill summary cache value must be SkillSummary, got {type(cached).__name__}"
        )
    return cached


def set_skill_summary(path: Path, summary: SkillSummary) -> None:
    resolved_path = path.resolve()
    cache = get_cache(SKILLS_CACHE_NAME)
    cache_key = _build_cache_key(SUMMARY_KEY_PREFIX, resolved_path)
    cache.set(cache_key, summary)
    cache.set_metadata(
        cache_key,
        MtimeMetadata(path=resolved_path, mtime_ns=stat_mtime_ns(resolved_path)),
    )


def get_loaded_skill(path: Path) -> LoadedSkill | None:
    cache_key = _build_cache_key(LOADED_KEY_PREFIX, path)
    cached = get_cache(SKILLS_CACHE_NAME).get(cache_key)
    if cached is None:
        return None
    if not isinstance(cached, LoadedSkill):
        raise TypeError(
            f"Loaded skill cache value must be LoadedSkill, got {type(cached).__name__}"
        )
    return cached


def set_loaded_skill(path: Path, loaded_skill: LoadedSkill) -> None:
    resolved_path = path.resolve()
    cache = get_cache(SKILLS_CACHE_NAME)
    cache_key = _build_cache_key(LOADED_KEY_PREFIX, resolved_path)
    cache.set(cache_key, loaded_skill)
    cache.set_metadata(
        cache_key,
        MtimeMetadata(path=resolved_path, mtime_ns=stat_mtime_ns(resolved_path)),
    )


def clear_skills_cache() -> None:
    get_cache(SKILLS_CACHE_NAME).clear()


def _build_cache_key(prefix: str, path: Path) -> tuple[str, Path]:
    return prefix, path.resolve()
