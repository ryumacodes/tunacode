from __future__ import annotations

from pathlib import Path

from textual.widgets import Static

from tunacode.core.session import StateManager

from tunacode.ui.app import TextualReplApp
from tunacode.ui.commands import COMMANDS
from tunacode.ui.commands.skills import SkillsCommand
from tunacode.ui.widgets.command_autocomplete import _COMMAND_ITEMS

SKILL_TEMPLATE = """---
name: demo
description: Demo skill
---

# Demo Skill

Use this skill.
"""


async def test_skills_command_attaches_and_clears_selected_skills(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HOME", str(tmp_path / "home"))

    skill_dir = tmp_path / ".claude" / "skills" / "demo"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(SKILL_TEMPLATE, encoding="utf-8")

    app = TextualReplApp(state_manager=StateManager())

    async with app.run_test(headless=True):
        command = COMMANDS["skills"]
        assert isinstance(command, SkillsCommand)

        await command.execute(app, "demo")

        assert app.state_manager.session.selected_skill_names == ["demo"]
        field_skills = app.query_one("#field-skills", Static)
        assert field_skills.border_title == "Loaded Skills [1]"
        assert "demo" in str(field_skills.renderable).lower()

        await command.execute(app, "clear")

        assert app.state_manager.session.selected_skill_names == []
        assert field_skills.border_title == "Loaded Skills [0]"


async def test_skills_command_search_does_not_attach_partial_matches(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HOME", str(tmp_path / "home"))

    skill_dir = tmp_path / ".claude" / "skills" / "demo"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(SKILL_TEMPLATE, encoding="utf-8")

    app = TextualReplApp(state_manager=StateManager())

    async with app.run_test(headless=True):
        command = COMMANDS["skills"]
        assert isinstance(command, SkillsCommand)

        await command.execute(app, "dem")

        assert app.state_manager.session.selected_skill_names == []


def test_skills_command_is_available_in_autocomplete() -> None:
    assert "skills" in COMMANDS
    assert "skill" not in COMMANDS
    assert any(name == "skills" for name, _description in _COMMAND_ITEMS)
