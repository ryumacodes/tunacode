from __future__ import annotations

from pathlib import Path

from tunacode.skills.discovery import DiscoveredSkillPath
from tunacode.skills.loader import load_skill_summary
from tunacode.skills.models import SkillSource

SKILL_TEMPLATE = """---
name: demo
description: Demo skill
---

# Demo Skill

Use `helper.py` when needed.
"""


def test_load_skill_summary_returns_metadata_without_body(tmp_path: Path) -> None:
    skill_dir = tmp_path / "demo"
    skill_dir.mkdir()
    skill_path = skill_dir / "SKILL.md"
    skill_path.write_text(SKILL_TEMPLATE, encoding="utf-8")
    discovered_skill = DiscoveredSkillPath(
        name="demo",
        source=SkillSource.LOCAL,
        skill_dir=skill_dir,
        skill_path=skill_path,
    )

    summary = load_skill_summary(discovered_skill)

    assert summary.name == "demo"
    assert summary.description == "Demo skill"
    assert summary.skill_path == skill_path
    assert not hasattr(summary, "content")
