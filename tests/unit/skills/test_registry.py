from __future__ import annotations

import os
from pathlib import Path

import pytest

from tunacode.infrastructure.cache import clear_all

from tunacode.skills.registry import get_skill_summary, list_skill_summaries, load_skill_by_name

MTIME_INCREMENT_NS = 1_000_000_000
SKILL_TEMPLATE = """---
name: {name}
description: {description}
---

# {name}

{body}
"""


@pytest.fixture
def clean_cache_manager() -> None:
    clear_all()
    yield
    clear_all()


def test_list_skill_summaries_returns_sorted_metadata(
    clean_cache_manager: None,
    tmp_path: Path,
) -> None:
    local_root = tmp_path / "local"
    _write_skill(local_root, "zeta", description="Last", body="body")
    _write_skill(local_root, "alpha", description="First", body="body")

    summaries = list_skill_summaries(local_root=local_root, global_root=tmp_path / "global")

    assert [summary.name for summary in summaries] == ["alpha", "zeta"]
    assert [summary.description for summary in summaries] == ["First", "Last"]


def test_get_skill_summary_resolves_case_insensitive_name(
    clean_cache_manager: None,
    tmp_path: Path,
) -> None:
    local_root = tmp_path / "local"
    _write_skill(local_root, "Demo", description="Demo skill", body="body")

    summary = get_skill_summary("demo", local_root=local_root, global_root=tmp_path / "global")

    assert summary is not None
    assert summary.name == "Demo"


def test_load_skill_by_name_refreshes_after_mtime_change(
    clean_cache_manager: None,
    tmp_path: Path,
) -> None:
    local_root = tmp_path / "local"
    skill_path = _write_skill(local_root, "demo", description="Initial", body="version one")
    helper_path = skill_path.parent / "helper.py"
    helper_path.write_text("print('ok')\n", encoding="utf-8")

    first = load_skill_by_name("demo", local_root=local_root, global_root=tmp_path / "global")
    second = load_skill_by_name("demo", local_root=local_root, global_root=tmp_path / "global")

    assert first is second
    assert "version one" in first.content

    original_mtime_ns = os.stat(skill_path).st_mtime_ns
    skill_path.write_text(
        SKILL_TEMPLATE.format(
            name="demo", description="Updated", body="version two with `helper.py`"
        ),
        encoding="utf-8",
    )
    updated_mtime_ns = original_mtime_ns + MTIME_INCREMENT_NS
    os.utime(skill_path, ns=(updated_mtime_ns, updated_mtime_ns))

    third = load_skill_by_name("demo", local_root=local_root, global_root=tmp_path / "global")

    assert third is not second
    assert third.description == "Updated"
    assert "version two" in third.content


def _write_skill(root: Path, name: str, *, description: str, body: str) -> Path:
    skill_dir = root / name
    skill_dir.mkdir(parents=True, exist_ok=True)
    skill_path = skill_dir / "SKILL.md"
    skill_path.write_text(
        SKILL_TEMPLATE.format(name=name, description=description, body=body),
        encoding="utf-8",
    )
    return skill_path
