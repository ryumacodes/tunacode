from __future__ import annotations

from pathlib import Path

import pytest

from tunacode.skills.selection import (
    attach_skill,
    resolve_selected_skill_summaries,
    resolve_selected_skills,
)

from tunacode.infrastructure.cache import clear_all


@pytest.fixture
def clean_cache_manager() -> None:
    clear_all()
    yield
    clear_all()


def _write_skill(skill_root: Path, skill_name: str, description: str) -> Path:
    skill_dir = skill_root / skill_name
    skill_dir.mkdir(parents=True)
    skill_path = skill_dir / "SKILL.md"
    related_path = skill_dir / "README.md"
    skill_path.write_text(
        "\n".join(
            [
                "---",
                f"name: {skill_name}",
                f"description: {description}",
                "---",
                "",
                f"# {skill_name}",
                "",
                "See [README.md](README.md).",
            ]
        ),
        encoding="utf-8",
    )
    related_path.write_text("Related skill documentation", encoding="utf-8")
    return skill_path


def test_attach_skill_dedupes_case_insensitive_requests_to_one_canonical_name(
    clean_cache_manager: None,
    tmp_path: Path,
) -> None:
    local_root = tmp_path / "local-skills"
    _write_skill(local_root, "Demo", "Demo skill")

    next_skill_names, summary, already_attached = attach_skill(
        [],
        "demo",
        local_root=local_root,
        global_root=tmp_path / "global-skills",
    )
    repeated_skill_names, repeated_summary, repeated_already_attached = attach_skill(
        next_skill_names,
        "DEMO",
        local_root=local_root,
        global_root=tmp_path / "global-skills",
    )

    assert next_skill_names == ["Demo"]
    assert summary.name == "Demo"
    assert already_attached is False

    assert repeated_skill_names == ["Demo"]
    assert repeated_summary.name == "Demo"
    assert repeated_already_attached is True


def test_resolve_selected_skills_returns_loaded_content_and_related_paths(
    clean_cache_manager: None,
    tmp_path: Path,
) -> None:
    local_root = tmp_path / "local-skills"
    skill_path = _write_skill(local_root, "Demo", "Demo skill")
    related_path = local_root / "Demo" / "README.md"

    selected_skills = resolve_selected_skills(
        ["DEMO"],
        local_root=local_root,
        global_root=tmp_path / "global-skills",
    )

    assert len(selected_skills) == 1
    assert selected_skills[0].name == "Demo"
    assert selected_skills[0].content == skill_path.read_text(encoding="utf-8")
    assert selected_skills[0].related_paths == (related_path.resolve(),)


def test_resolve_selected_skill_summaries_preserves_order_and_missing_entries(
    clean_cache_manager: None,
    tmp_path: Path,
) -> None:
    local_root = tmp_path / "local-skills"
    _write_skill(local_root, "Demo", "Demo skill")

    resolved_summaries = resolve_selected_skill_summaries(
        ["Demo", "ghost"],
        local_root=local_root,
        global_root=tmp_path / "global-skills",
    )

    assert [entry.requested_name for entry in resolved_summaries] == ["Demo", "ghost"]
    assert resolved_summaries[0].summary is not None
    assert resolved_summaries[0].summary.name == "Demo"
    assert resolved_summaries[1].summary is None


def test_resolve_selected_skills_raises_for_missing_selected_skill(
    clean_cache_manager: None,
    tmp_path: Path,
) -> None:
    with pytest.raises(KeyError, match="Unknown skill: ghost"):
        resolve_selected_skills(
            ["ghost"],
            local_root=tmp_path / "local-skills",
            global_root=tmp_path / "global-skills",
        )
