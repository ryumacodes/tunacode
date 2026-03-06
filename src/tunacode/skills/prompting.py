from __future__ import annotations

import hashlib

from tunacode.skills.models import SelectedSkill, SkillSummary

AVAILABLE_SKILLS_SECTION_TITLE = "# Available Skills"
SELECTED_SKILLS_SECTION_TITLE = "# Selected Skills"

SELECTED_SKILLS_INSTRUCTION = """\
The following skills have been loaded for this session.
You MUST read each skill's SKILL.md content fully and apply its guidance to all relevant tasks.
Do not ignore these skills - they contain critical instructions for this codebase."""


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
        lines.append(f"## {selected_skill.name} ({selected_skill.source.value})")
        lines.append(selected_skill.content)
    return "\n".join(lines)


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
        fingerprint_parts.append(
            "selected:"
            f"{selected_skill.name}:{selected_skill.source.value}:{selected_skill.skill_path}:{content_hash}"
        )

    fingerprint_input = "|".join(fingerprint_parts)
    return hashlib.sha256(fingerprint_input.encode("utf-8")).hexdigest()
