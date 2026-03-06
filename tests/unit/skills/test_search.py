from __future__ import annotations

from pathlib import Path

from tunacode.skills.models import SkillSource, SkillSummary
from tunacode.skills.search import filter_skill_summaries

EMPTY_PATH = Path(".")


def test_filter_skill_summaries_prefers_shorter_prefix_match() -> None:
    skill_summaries = [
        _build_skill_summary(name="dead-code-detector", description="Detect dead code"),
        _build_skill_summary(name="demo", description="Demo skill"),
    ]

    matching_summaries = filter_skill_summaries(skill_summaries, query="de")

    assert [skill_summary.name for skill_summary in matching_summaries] == [
        "demo",
        "dead-code-detector",
    ]


def test_filter_skill_summaries_prefers_name_matches_before_description_matches() -> None:
    skill_summaries = [
        _build_skill_summary(name="alpha", description="demo support"),
        _build_skill_summary(name="demo", description="Alpha support"),
    ]

    matching_summaries = filter_skill_summaries(skill_summaries, query="demo")

    assert [skill_summary.name for skill_summary in matching_summaries] == ["demo", "alpha"]


def _build_skill_summary(*, name: str, description: str) -> SkillSummary:
    return SkillSummary(
        name=name,
        description=description,
        source=SkillSource.LOCAL,
        skill_dir=EMPTY_PATH,
        skill_path=EMPTY_PATH,
    )
