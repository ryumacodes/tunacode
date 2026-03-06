from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from tunacode.infrastructure.cache import clear_all

from tunacode.core.session import StateManager

from tunacode.ui.app import TextualReplApp


@pytest.fixture
def clean_cache_manager() -> None:
    clear_all()
    yield
    clear_all()


def _write_skill(skill_root: Path, skill_name: str, description: str) -> None:
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


def test_build_skill_entries_uses_canonical_names_and_missing_markers(
    clean_cache_manager: None,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.chdir(tmp_path)

    local_root = tmp_path / ".claude" / "skills"
    _write_skill(local_root, "Demo", "Demo skill")

    state_manager = StateManager()
    state_manager.session.selected_skill_names = ["DEMO", "ghost"]
    app = SimpleNamespace(state_manager=state_manager)

    skill_entries = TextualReplApp._build_skill_entries(app)

    assert skill_entries == [("Demo", "local"), ("ghost", "missing")]
