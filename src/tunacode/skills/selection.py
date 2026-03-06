from __future__ import annotations

from pathlib import Path

from tunacode.skills.discovery import DiscoveredSkillPath, discover_skills
from tunacode.skills.loader import load_skill
from tunacode.skills.models import SelectedSkill, SkillSummary
from tunacode.skills.registry import get_skill_summary


def _find_discovered_skill_by_name(
    name: str,
    *,
    local_root: Path | None = None,
    global_root: Path | None = None,
) -> DiscoveredSkillPath | None:
    """Find a discovered skill by name, preferring local over global."""
    normalized_name = name.casefold()
    for discovered_skill in discover_skills(
        local_root=local_root,
        global_root=global_root,
    ).values():
        if discovered_skill.name.casefold() == normalized_name:
            return discovered_skill
    return None


def attach_skill(
    current_skill_names: list[str],
    requested_name: str,
    *,
    local_root: Path | None = None,
    global_root: Path | None = None,
) -> tuple[list[str], SkillSummary, bool]:
    # Find the discovered skill first to ensure we use the correct path
    discovered_skill = _find_discovered_skill_by_name(
        requested_name,
        local_root=local_root,
        global_root=global_root,
    )
    if discovered_skill is None:
        raise KeyError(f"Unknown skill: {requested_name}")

    # Load the summary from the discovered skill (uses cache)
    summary = get_skill_summary(
        discovered_skill.name,
        local_root=local_root,
        global_root=global_root,
    )
    if summary is None:
        raise KeyError(f"Unknown skill: {requested_name}")

    for existing_name in current_skill_names:
        if existing_name.casefold() == summary.name.casefold():
            return list(current_skill_names), summary, True

    # Load the skill using the already-discovered path (don't rediscover)
    load_skill(discovered_skill)
    next_skill_names = [*current_skill_names, summary.name]
    return next_skill_names, summary, False


def clear_attached_skills() -> list[str]:
    return []


def resolve_selected_skills(
    selected_skill_names: list[str],
    *,
    local_root: Path | None = None,
    global_root: Path | None = None,
) -> list[SelectedSkill]:
    selected_skills: list[SelectedSkill] = []

    for attachment_index, selected_skill_name in enumerate(selected_skill_names):
        # Discover first to get the correct path (local vs global)
        discovered_skill = _find_discovered_skill_by_name(
            selected_skill_name,
            local_root=local_root,
            global_root=global_root,
        )
        if discovered_skill is None:
            raise KeyError(f"Unknown skill: {selected_skill_name}")

        # Load using the discovered path directly
        loaded_skill = load_skill(discovered_skill)
        selected_skills.append(
            SelectedSkill(
                name=loaded_skill.name,
                source=loaded_skill.source,
                skill_path=loaded_skill.skill_path,
                content=loaded_skill.content,
                attachment_index=attachment_index,
            )
        )

    return selected_skills


def resolve_selected_skill_summaries(
    selected_skill_names: list[str],
    *,
    local_root: Path | None = None,
    global_root: Path | None = None,
) -> list[SkillSummary]:
    selected_summaries: list[SkillSummary] = []

    for selected_skill_name in selected_skill_names:
        summary = get_skill_summary(
            selected_skill_name,
            local_root=local_root,
            global_root=global_root,
        )
        if summary is None:
            raise KeyError(f"Unknown skill: {selected_skill_name}")
        selected_summaries.append(summary)

    return selected_summaries
