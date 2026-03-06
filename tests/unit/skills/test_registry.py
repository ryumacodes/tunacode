from __future__ import annotations

from pathlib import Path

import pytest

from tunacode.infrastructure.cache import clear_all

from tunacode.skills.models import SkillSource
from tunacode.skills.registry import get_skill_summary, load_skill_by_name, resolve_discovered_skill


@pytest.fixture
def clean_cache_manager() -> None:
    clear_all()
    yield
    clear_all()


def _write_skill(skill_root: Path, skill_name: str, description: str) -> Path:
    skill_dir = skill_root / skill_name
    skill_dir.mkdir(parents=True)
    skill_path = skill_dir / "SKILL.md"
    skill_path.write_text(
        "\n".join(
            [
                "---",
                f"name: {skill_name}",
                f"description: {description}",
                "---",
                "",
                f"# {skill_name}",
            ]
        ),
        encoding="utf-8",
    )
    return skill_path


def test_registry_lookup_prefers_local_skill_with_case_insensitive_resolution(
    clean_cache_manager: None,
    tmp_path: Path,
) -> None:
    local_root = tmp_path / "local-skills"
    global_root = tmp_path / "global-skills"
    local_skill_path = _write_skill(local_root, "Demo", "Local demo skill")
    _write_skill(global_root, "demo", "Global demo skill")

    summary = get_skill_summary("dEmO", local_root=local_root, global_root=global_root)
    loaded_skill = load_skill_by_name("DEMO", local_root=local_root, global_root=global_root)

    assert summary is not None
    assert summary.name == "Demo"
    assert summary.source is SkillSource.LOCAL
    assert summary.skill_path == local_skill_path.resolve()

    assert loaded_skill.name == "Demo"
    assert loaded_skill.source is SkillSource.LOCAL
    assert loaded_skill.skill_path == local_skill_path.resolve()


def test_resolve_discovered_skill_returns_local_match_for_mixed_case_lookup(
    clean_cache_manager: None,
    tmp_path: Path,
) -> None:
    local_root = tmp_path / "local-skills"
    global_root = tmp_path / "global-skills"
    local_skill_path = _write_skill(local_root, "Demo", "Local demo skill")
    _write_skill(global_root, "demo", "Global demo skill")

    discovered_skill = resolve_discovered_skill(
        "deMO",
        local_root=local_root,
        global_root=global_root,
    )

    assert discovered_skill is not None
    assert discovered_skill.name == "Demo"
    assert discovered_skill.source is SkillSource.LOCAL
    assert discovered_skill.skill_path == local_skill_path.resolve()
