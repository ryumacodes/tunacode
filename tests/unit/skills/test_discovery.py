from __future__ import annotations

from pathlib import Path

import pytest

from tunacode.skills.discovery import (
    SKILL_FILE_NAME,
    DuplicateSkillNameError,
    discover_skills,
)
from tunacode.skills.models import SkillSource


def _write_skill(root: Path, skill_name: str, body: str = "demo") -> Path:
    skill_dir = root / skill_name
    skill_dir.mkdir(parents=True, exist_ok=True)
    skill_path = skill_dir / SKILL_FILE_NAME
    skill_path.write_text(body, encoding="utf-8")
    return skill_path


def test_discover_skills_returns_local_only_entries(tmp_path: Path) -> None:
    local_root = tmp_path / "local"
    global_root = tmp_path / "global"
    local_path = _write_skill(local_root, "demo")

    discovered = discover_skills(local_root=local_root, global_root=global_root)

    assert list(discovered) == ["demo"]
    assert discovered["demo"].source is SkillSource.LOCAL
    assert discovered["demo"].skill_path == local_path.resolve()


def test_discover_skills_returns_global_only_entries(tmp_path: Path) -> None:
    local_root = tmp_path / "local"
    global_root = tmp_path / "global"
    global_path = _write_skill(global_root, "demo")

    discovered = discover_skills(local_root=local_root, global_root=global_root)

    assert list(discovered) == ["demo"]
    assert discovered["demo"].source is SkillSource.GLOBAL
    assert discovered["demo"].skill_path == global_path.resolve()


def test_discover_skills_prefers_local_over_global_on_name_collision(tmp_path: Path) -> None:
    local_root = tmp_path / "local"
    global_root = tmp_path / "global"
    local_path = _write_skill(local_root, "demo", body="local")
    _write_skill(global_root, "demo", body="global")

    discovered = discover_skills(local_root=local_root, global_root=global_root)

    assert list(discovered) == ["demo"]
    assert discovered["demo"].source is SkillSource.LOCAL
    assert discovered["demo"].skill_path == local_path.resolve()


def test_discover_skills_ignores_directories_without_skill_file(tmp_path: Path) -> None:
    local_root = tmp_path / "local"
    ignored_dir = local_root / "ignored"
    ignored_dir.mkdir(parents=True)

    discovered = discover_skills(local_root=local_root, global_root=tmp_path / "global")

    assert discovered == {}


def test_discover_skills_rejects_same_root_casefold_duplicates(tmp_path: Path) -> None:
    local_root = tmp_path / "local"
    _write_skill(local_root, "demo")
    _write_skill(local_root, "Demo")

    with pytest.raises(DuplicateSkillNameError):
        discover_skills(local_root=local_root, global_root=tmp_path / "global")
