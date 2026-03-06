from __future__ import annotations

import hashlib
from collections.abc import Iterable
from pathlib import Path

from tunacode.skills.models import SelectedSkill, SkillSummary

AVAILABLE_SKILLS_SECTION_TITLE = "# Available Skills"
SELECTED_SKILLS_SECTION_TITLE = "# Selected Skills"

SELECTED_SKILLS_INSTRUCTION = """\
The user explicitly loaded the following skills via /skills, and they are ACTIVE for this session.
These loaded skills are not optional reference material; they are active operating instructions.
Before doing work, determine whether one or more loaded skills apply to the user's request.
If a loaded skill applies, you MUST follow it,
even if the user does not repeat its name in the latest message.
When a loaded skill is relevant,
prefer its workflow and guidance over generic default behavior.
Before searching the repository for help,
check the loaded skill paths below and use them directly when they are relevant.
You MUST read each loaded skill's full SKILL.md content
and use the exact absolute skill paths below as authoritative.
These skill files may live outside the current project working directory.
Do not assume searching only the repo root will find them.
When a loaded skill materially affects your answer or plan,
explicitly say that the skill is loaded and being used.
Do not ignore a loaded skill that matches the task."""

SKILL_STATUS_LABEL = "Skill status"
SKILL_DIRECTORY_LABEL = "Skill directory (absolute)"
SKILL_FILE_LABEL = "Skill definition file (absolute)"
SKILL_REFERENCED_FILES_LABEL = "Files explicitly referenced by SKILL.md"
SKILL_RELATED_FILES_LABEL = "Other files available in the skill directory"
SKILL_CONTENT_LABEL = "Full SKILL.md content"
EMPTY_PATH_LIST_LABEL = "(none)"


def render_available_skills_block(skill_summaries: list[SkillSummary]) -> str:
    lines = ["", "", AVAILABLE_SKILLS_SECTION_TITLE]
    if not skill_summaries:
        lines.append("(none)")
        return "\n".join(lines)

    for skill_summary in skill_summaries:
        lines.append(f"- {skill_summary.name}: {skill_summary.description}")
    return "\n".join(lines)


def render_selected_skills_block(selected_skills: list[SelectedSkill]) -> str:
    if not selected_skills:
        return ""

    lines = ["", "", SELECTED_SKILLS_SECTION_TITLE]
    lines.append(SELECTED_SKILLS_INSTRUCTION)
    lines.append("")
    for selected_skill in selected_skills:
        _append_selected_skill_block(lines, selected_skill)
    return "\n".join(lines)


def _append_selected_skill_block(lines: list[str], selected_skill: SelectedSkill) -> None:
    lines.append(f"## {selected_skill.name} ({selected_skill.source.value})")
    lines.append(f"{SKILL_STATUS_LABEL}: ACTIVE - explicitly loaded by the user via /skills")
    lines.append(f"{SKILL_DIRECTORY_LABEL}: {selected_skill.skill_dir}")
    lines.append(f"{SKILL_FILE_LABEL}: {selected_skill.skill_path}")
    lines.append(
        "This skill is active right now. "
        "Use these absolute paths directly when you need skill files."
    )
    lines.append(f"{SKILL_REFERENCED_FILES_LABEL}:")
    _append_path_list(lines, selected_skill.referenced_paths)

    additional_related_paths = [
        path for path in selected_skill.related_paths if path not in selected_skill.referenced_paths
    ]
    lines.append(f"{SKILL_RELATED_FILES_LABEL}:")
    _append_path_list(lines, additional_related_paths)

    lines.append("")
    lines.append(f"{SKILL_CONTENT_LABEL}:")
    lines.append(selected_skill.content)
    lines.append("")


def _append_path_list(lines: list[str], paths: Iterable[Path]) -> None:
    materialized_paths = list(paths)
    if not materialized_paths:
        lines.append(f"- {EMPTY_PATH_LIST_LABEL}")
        return

    for path in materialized_paths:
        lines.append(f"- {path}")


def compute_skills_prompt_fingerprint(
    skill_summaries: list[SkillSummary],
    selected_skills: list[SelectedSkill],
) -> str:
    fingerprint_parts: list[str] = []

    for skill_summary in skill_summaries:
        fingerprint_parts.append(
            f"summary:{skill_summary.name}:{skill_summary.description}:{skill_summary.source.value}"
        )

    for selected_skill in selected_skills:
        content_hash = hashlib.sha256(selected_skill.content.encode("utf-8")).hexdigest()
        referenced_paths_hash = _hash_paths(selected_skill.referenced_paths)
        related_paths_hash = _hash_paths(selected_skill.related_paths)
        fingerprint_parts.append(
            "selected:"
            f"{selected_skill.name}:{selected_skill.source.value}:{selected_skill.skill_dir}:"
            f"{selected_skill.skill_path}:{content_hash}:{referenced_paths_hash}:{related_paths_hash}"
        )

    fingerprint_input = "|".join(fingerprint_parts)
    return hashlib.sha256(fingerprint_input.encode("utf-8")).hexdigest()


def _hash_paths(paths: Iterable[Path]) -> str:
    joined_paths = "|".join(str(path) for path in paths)
    return hashlib.sha256(joined_paths.encode("utf-8")).hexdigest()
