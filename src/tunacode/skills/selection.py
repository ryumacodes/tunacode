from __future__ import annotations

from pathlib import Path

from tunacode.skills.loader import list_skill_related_paths
from tunacode.skills.models import SelectedSkill, SkillSummary
from tunacode.skills.registry import get_skill_summary, load_skill_by_name


def attach_skill(
    current_skill_names: list[str],
    requested_name: str,
    *,
    local_root: Path | None = None,
    global_root: Path | None = None,
) -> tuple[list[str], SkillSummary, bool]:
    summary = get_skill_summary(
        requested_name,
        local_root=local_root,
        global_root=global_root,
    )
    if summary is None:
        raise KeyError(f"Unknown skill: {requested_name}")

    for existing_name in current_skill_names:
        if existing_name.casefold() == summary.name.casefold():
            return list(current_skill_names), summary, True

    load_skill_by_name(
        summary.name,
        local_root=local_root,
        global_root=global_root,
    )
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
        loaded_skill = load_skill_by_name(
            selected_skill_name,
            local_root=local_root,
            global_root=global_root,
        )
        related_paths = list_skill_related_paths(
            loaded_skill.skill_dir,
            skill_path=loaded_skill.skill_path,
        )
        selected_skills.append(
            SelectedSkill(
                name=loaded_skill.name,
                source=loaded_skill.source,
                skill_dir=loaded_skill.skill_dir,
                skill_path=loaded_skill.skill_path,
                referenced_paths=loaded_skill.referenced_paths,
                related_paths=related_paths,
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
