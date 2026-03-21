from __future__ import annotations

from pathlib import Path

import pytest

from tunacode.infrastructure.cache import clear_all

from tunacode.core.agents.agent_components import agent_config
from tunacode.core.session import StateManager

SYSTEM_PROMPT_STUB = "SYSTEM"
CONTEXT_PROMPT_STUB = "CONTEXT"
SKILL_NAME = "md-organizer"
SKILL_DESCRIPTION = "Organize markdown files"
SCRIPT_FILE_NAME = "organize-md.py"
README_FILE_NAME = "README.md"
SCRIPT_REFERENCE_LINE = f"See [{SCRIPT_FILE_NAME}]({SCRIPT_FILE_NAME})."
SKILL_TEMPLATE = f"""---
name: {SKILL_NAME}
description: {SKILL_DESCRIPTION}
---

# MD Organizer

This skill organizes markdown files.
{SCRIPT_REFERENCE_LINE}
"""
README_CONTENT = "Skill README"
SCRIPT_CONTENT = "print('organize')\n"


@pytest.fixture
def clean_cache_manager() -> None:
    clear_all()
    yield
    clear_all()


def test_get_or_create_agent_injects_loaded_skill_prompt_with_canonical_paths(
    clean_cache_manager: None,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.chdir(tmp_path)

    skill_dir = tmp_path / ".claude" / "skills" / SKILL_NAME
    skill_dir.mkdir(parents=True)
    skill_path = skill_dir / "SKILL.md"
    readme_path = skill_dir / README_FILE_NAME
    script_path = skill_dir / SCRIPT_FILE_NAME

    skill_path.write_text(SKILL_TEMPLATE, encoding="utf-8")
    readme_path.write_text(README_CONTENT, encoding="utf-8")
    script_path.write_text(SCRIPT_CONTENT, encoding="utf-8")

    monkeypatch.setattr(
        agent_config,
        "load_system_prompt",
        lambda _base_path, model=None: SYSTEM_PROMPT_STUB,
    )
    monkeypatch.setattr(
        agent_config,
        "load_tunacode_context",
        lambda: CONTEXT_PROMPT_STUB,
    )

    state_manager = StateManager()
    state_manager.session.selected_skill_names = [SKILL_NAME.upper()]

    agent = agent_config.get_or_create_agent(state_manager.session.current_model, state_manager)
    system_prompt = agent._state.system_prompt

    selected_index = system_prompt.index("# Selected Skills")
    available_index = system_prompt.index("# Available Skills")

    assert selected_index < available_index
    assert "ACTIVE for this session" in system_prompt
    assert "explicitly say that the skill is loaded and being used" in system_prompt
    assert f"## {SKILL_NAME} (local)" in system_prompt
    assert f"Skill definition file (absolute): {skill_path.resolve()}" in system_prompt
    assert f"Skill directory (absolute): {skill_dir.resolve()}" in system_prompt
    assert f"- {script_path.resolve()}" in system_prompt
    assert f"- {readme_path.resolve()}" in system_prompt
    assert "Full SKILL.md content:" in system_prompt
    assert SKILL_TEMPLATE.strip() in system_prompt
    assert SCRIPT_REFERENCE_LINE in system_prompt
