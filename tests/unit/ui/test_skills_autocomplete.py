from __future__ import annotations

from pathlib import Path

from textual_autocomplete import TargetState

from tunacode.core.session import StateManager

from tunacode.ui.app import TextualReplApp
from tunacode.ui.widgets.command_autocomplete import CommandAutoComplete
from tunacode.ui.widgets.skills_autocomplete import SkillsAutoComplete

SKILL_TEMPLATE = """---
name: {name}
description: {description}
---

# {name}

{description}
"""


class _FakeInput:
    def __init__(self, value: str = "") -> None:
        self.value = value
        self.cursor_position = len(value)


def test_skills_autocomplete_suggests_subcommands_and_skill_names(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    _write_skill(tmp_path, "prompting-skills", description="Prompt engineering help")

    autocomplete = SkillsAutoComplete(_FakeInput())

    candidates = autocomplete.get_candidates(TargetState(text="/skills pr", cursor_position=10))

    candidate_names = [str(candidate.main) for candidate in candidates]
    assert "prompting-skills" in candidate_names


async def test_skills_autocomplete_applies_root_completion(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    _write_skill(tmp_path, "prompting-skills", description="Prompt engineering help")

    app = TextualReplApp(state_manager=StateManager())

    async with app.run_test(headless=True):
        app.editor.value = "/skills pr"
        autocomplete = app.query_one(SkillsAutoComplete)
        autocomplete.apply_completion(
            "prompting-skills",
            TargetState(text=app.editor.value, cursor_position=len(app.editor.value)),
        )

        assert app.editor.value == "/skills prompting-skills"


async def test_skills_autocomplete_applies_search_completion(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    _write_skill(tmp_path, "prompting-skills", description="Prompt engineering help")

    app = TextualReplApp(state_manager=StateManager())

    async with app.run_test(headless=True):
        app.editor.value = "/skills search pr"
        autocomplete = app.query_one(SkillsAutoComplete)
        autocomplete.apply_completion(
            "prompting-skills",
            TargetState(text=app.editor.value, cursor_position=len(app.editor.value)),
        )

        assert app.editor.value == "/skills search prompting-skills"


async def test_skills_autocomplete_applies_search_subcommand_with_trailing_space(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HOME", str(tmp_path / "home"))

    app = TextualReplApp(state_manager=StateManager())

    async with app.run_test(headless=True):
        app.editor.value = "/skills se"
        autocomplete = app.query_one(SkillsAutoComplete)
        autocomplete.apply_completion(
            "search",
            TargetState(text=app.editor.value, cursor_position=len(app.editor.value)),
        )

        assert app.editor.value == "/skills search "


async def test_skills_autocomplete_enter_prefers_best_prefix_match(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    _write_skill(tmp_path, "dead-code-detector", description="Find dead code")
    _write_skill(tmp_path, "demo", description="Demo skill")

    app = TextualReplApp(state_manager=StateManager())

    async with app.run_test(headless=True) as pilot:
        autocomplete = app.query_one(SkillsAutoComplete)

        await _type_text(pilot, "/skills de")
        await pilot.pause()

        assert autocomplete.display is True
        assert app.editor.value == "/skills de"

        await pilot.press("enter")
        await pilot.pause()

        assert app.editor.value == "/skills demo"

        await pilot.press("enter")
        await pilot.pause()

        assert app.editor.value == ""
        assert app.state_manager.session.selected_skill_names == ["demo"]


async def test_skills_autocomplete_down_selects_highlighted_skill(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    _write_skill(tmp_path, "alpha", description="Alpha skill")
    _write_skill(tmp_path, "beta", description="Beta skill")

    app = TextualReplApp(state_manager=StateManager())

    async with app.run_test(headless=True) as pilot:
        command_autocomplete = app.query_one(CommandAutoComplete)
        skills_autocomplete = app.query_one(SkillsAutoComplete)

        await _type_text(pilot, "/skills ")
        await pilot.pause()

        assert app.editor.value == "/skills "
        assert command_autocomplete.option_list.option_count == 0
        assert command_autocomplete.display is False
        assert skills_autocomplete.display is True

        await pilot.press("down")
        await pilot.press("down")
        await pilot.press("down")
        await pilot.pause()

        highlighted_index = skills_autocomplete.option_list.highlighted
        assert highlighted_index == 3
        highlighted_option = skills_autocomplete.option_list.get_option_at_index(highlighted_index)
        assert highlighted_option.value == "alpha"

        await pilot.press("enter")
        await pilot.pause()

        assert app.editor.value == "/skills alpha"
        assert command_autocomplete.display is False

        await pilot.press("enter")
        await pilot.pause()

        assert app.editor.value == ""
        assert app.state_manager.session.selected_skill_names == ["alpha"]


async def _type_text(pilot, text: str) -> None:
    for character in text:
        key = "space" if character == " " else character
        await pilot.press(key)


def _write_skill(root: Path, name: str, *, description: str) -> None:
    skill_dir = root / ".claude" / "skills" / name
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text(
        SKILL_TEMPLATE.format(name=name, description=description),
        encoding="utf-8",
    )
