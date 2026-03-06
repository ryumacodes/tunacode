from __future__ import annotations

from pathlib import Path

import pytest

from tunacode.skills.discovery import DiscoveredSkillPath
from tunacode.skills.loader import (
    MissingSkillFileError,
    SkillFrontmatterError,
    SkillReferenceError,
    load_skill,
    load_skill_summary,
)
from tunacode.skills.models import SkillSource

SKILL_TEMPLATE = """---
name: demo
description: Demo skill
---

# Demo Skill

Use `helper.py` when needed.
"""


def test_load_skill_summary_returns_metadata_without_body(tmp_path: Path) -> None:
    discovered_skill = _build_discovered_skill(tmp_path, body=SKILL_TEMPLATE)

    summary = load_skill_summary(discovered_skill)

    assert summary.name == "demo"
    assert summary.description == "Demo skill"
    assert summary.skill_path == discovered_skill.skill_path
    assert not hasattr(summary, "content")


def test_load_skill_summary_accepts_legacy_markdown_without_frontmatter(tmp_path: Path) -> None:
    legacy_body = "# Demo Skill\n\nLegacy description line.\n"
    discovered_skill = _build_discovered_skill(tmp_path, body=legacy_body)

    summary = load_skill_summary(discovered_skill)

    assert summary.name == "demo"
    assert summary.description == "Legacy description line."


def test_load_skill_raises_typed_error_for_missing_relative_reference(tmp_path: Path) -> None:
    discovered_skill = _build_discovered_skill(tmp_path, body=SKILL_TEMPLATE)

    with pytest.raises(SkillReferenceError):
        load_skill(discovered_skill)


def test_load_skill_summary_rejects_malformed_frontmatter(tmp_path: Path) -> None:
    malformed_body = "---\nname demo\ndescription: Demo skill\n"
    discovered_skill = _build_discovered_skill(tmp_path, body=malformed_body)

    with pytest.raises(SkillFrontmatterError):
        load_skill_summary(discovered_skill)


def test_load_skill_summary_accepts_yaml_list_lines_in_frontmatter(tmp_path: Path) -> None:
    body_with_list_frontmatter = """---
name: demo
description: Demo skill
tags:
  - Bash
  - tmux
---

# Demo Skill
"""
    discovered_skill = _build_discovered_skill(tmp_path, body=body_with_list_frontmatter)

    summary = load_skill_summary(discovered_skill)

    assert summary.name == "demo"
    assert summary.description == "Demo skill"


def test_load_skill_raises_typed_error_for_missing_skill_file(tmp_path: Path) -> None:
    skill_dir = tmp_path / "demo"
    skill_dir.mkdir()
    missing_skill_path = skill_dir / "SKILL.md"
    discovered_skill = DiscoveredSkillPath(
        name="demo",
        source=SkillSource.LOCAL,
        skill_dir=skill_dir,
        skill_path=missing_skill_path,
    )

    with pytest.raises(MissingSkillFileError):
        load_skill(discovered_skill)


def _build_discovered_skill(tmp_path: Path, *, body: str) -> DiscoveredSkillPath:
    skill_dir = tmp_path / "demo"
    skill_dir.mkdir()
    skill_path = skill_dir / "SKILL.md"
    skill_path.write_text(body, encoding="utf-8")
    return DiscoveredSkillPath(
        name="demo",
        source=SkillSource.LOCAL,
        skill_dir=skill_dir,
        skill_path=skill_path,
    )
