from __future__ import annotations

from pathlib import Path

from tunacode.infrastructure.cache.caches import skills as skills_cache

from tunacode.skills.discovery import DiscoveredSkillPath, discover_skills
from tunacode.skills.loader import load_skill, load_skill_summary
from tunacode.skills.models import LoadedSkill, SkillSummary


def list_skill_summaries(
    *,
    local_root: Path | None = None,
    global_root: Path | None = None,
) -> list[SkillSummary]:
    discovered_skills = discover_skills(local_root=local_root, global_root=global_root)
    sorted_skills = sorted(discovered_skills.values(), key=lambda skill: skill.name.casefold())
    return [_get_or_load_summary(skill) for skill in sorted_skills]


def get_skill_summary(
    name: str,
    *,
    local_root: Path | None = None,
    global_root: Path | None = None,
) -> SkillSummary | None:
    discovered_skill = _find_discovered_skill(
        name=name,
        local_root=local_root,
        global_root=global_root,
    )
    if discovered_skill is None:
        return None
    return _get_or_load_summary(discovered_skill)


def load_skill_by_name(
    name: str,
    *,
    local_root: Path | None = None,
    global_root: Path | None = None,
) -> LoadedSkill:
    discovered_skill = _find_discovered_skill(
        name=name,
        local_root=local_root,
        global_root=global_root,
    )
    if discovered_skill is None:
        raise KeyError(f"Unknown skill: {name}")
    return _get_or_load_loaded_skill(discovered_skill)


def _find_discovered_skill(
    *,
    name: str,
    local_root: Path | None,
    global_root: Path | None,
) -> DiscoveredSkillPath | None:
    normalized_name = name.casefold()
    for discovered_skill in discover_skills(
        local_root=local_root, global_root=global_root
    ).values():
        if discovered_skill.name.casefold() == normalized_name:
            return discovered_skill
    return None


def _get_or_load_summary(discovered_skill: DiscoveredSkillPath) -> SkillSummary:
    cached_summary = skills_cache.get_skill_summary(discovered_skill.skill_path)
    if cached_summary is not None:
        return cached_summary

    summary = load_skill_summary(discovered_skill)
    skills_cache.set_skill_summary(discovered_skill.skill_path, summary)
    return summary


def _get_or_load_loaded_skill(discovered_skill: DiscoveredSkillPath) -> LoadedSkill:
    cached_loaded_skill = skills_cache.get_loaded_skill(discovered_skill.skill_path)
    if cached_loaded_skill is not None:
        return cached_loaded_skill

    loaded_skill = load_skill(discovered_skill)
    skills_cache.set_loaded_skill(discovered_skill.skill_path, loaded_skill)
    return loaded_skill
