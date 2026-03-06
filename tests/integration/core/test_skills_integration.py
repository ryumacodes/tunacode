from __future__ import annotations

from pathlib import Path

import pytest

from tunacode.infrastructure.cache import clear_all

from tunacode.core.agents.agent_components import agent_config
from tunacode.core.session import StateManager

LOCAL_SKILL_TEMPLATE = """---
name: demo
description: Local demo skill
---

# Local Demo Skill

LOCAL BODY
"""

GLOBAL_SKILL_TEMPLATE = """---
name: demo
description: Global demo skill
---

# Global Demo Skill

GLOBAL BODY
"""

LEGACY_GLOBAL_SKILL_TEMPLATE = """# Debug Tunacode API Integration

This skill provides a systematic methodology for debugging Tunacode API integrations.
"""

INVALID_GLOBAL_SKILL_TEMPLATE = """---
description: Broken skill
---
"""


@pytest.fixture
def clean_cache_manager() -> None:
    clear_all()
    yield
    clear_all()


def test_get_or_create_agent_includes_skill_metadata_and_selected_skill_body(
    clean_cache_manager: None,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))

    project_root = tmp_path / "project"
    project_root.mkdir()
    monkeypatch.chdir(project_root)

    local_skill_dir = project_root / ".claude" / "skills" / "demo"
    local_skill_dir.mkdir(parents=True)
    (local_skill_dir / "SKILL.md").write_text(LOCAL_SKILL_TEMPLATE, encoding="utf-8")

    global_skill_dir = home / ".claude" / "skills" / "demo"
    global_skill_dir.mkdir(parents=True)
    (global_skill_dir / "SKILL.md").write_text(GLOBAL_SKILL_TEMPLATE, encoding="utf-8")

    monkeypatch.setattr(
        agent_config, "load_system_prompt", lambda _base_path, model=None: ("SYSTEM", None)
    )
    monkeypatch.setattr(agent_config, "load_tunacode_context", lambda: ("CONTEXT", None))

    state_manager = StateManager()
    model_name = state_manager.session.current_model

    agent_without_selection = agent_config.get_or_create_agent(model_name, state_manager)
    prompt_without_selection = agent_without_selection._state.system_prompt

    assert "# Available Skills" in prompt_without_selection
    assert "Local demo skill" in prompt_without_selection
    assert "GLOBAL BODY" not in prompt_without_selection
    assert "LOCAL BODY" not in prompt_without_selection

    state_manager.session.selected_skill_names = ["demo"]

    agent_with_selection = agent_config.get_or_create_agent(model_name, state_manager)
    prompt_with_selection = agent_with_selection._state.system_prompt

    assert "# Selected Skills" in prompt_with_selection
    assert "LOCAL BODY" in prompt_with_selection
    assert "GLOBAL BODY" not in prompt_with_selection


def test_get_or_create_agent_accepts_legacy_global_skill_without_frontmatter(
    clean_cache_manager: None,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))

    project_root = tmp_path / "project"
    project_root.mkdir()
    monkeypatch.chdir(project_root)

    legacy_global_skill_dir = home / ".claude" / "skills" / "debug-tunacode-api"
    legacy_global_skill_dir.mkdir(parents=True)
    (legacy_global_skill_dir / "SKILL.md").write_text(
        LEGACY_GLOBAL_SKILL_TEMPLATE,
        encoding="utf-8",
    )

    monkeypatch.setattr(
        agent_config, "load_system_prompt", lambda _base_path, model=None: ("SYSTEM", None)
    )
    monkeypatch.setattr(agent_config, "load_tunacode_context", lambda: ("CONTEXT", None))

    state_manager = StateManager()
    model_name = state_manager.session.current_model

    agent = agent_config.get_or_create_agent(model_name, state_manager)
    prompt = agent._state.system_prompt

    assert "# Available Skills" in prompt
    assert "debug-tunacode-api" in prompt
    assert "systematic methodology" in prompt.casefold()


def test_get_or_create_agent_skips_invalid_global_skill_summary(
    clean_cache_manager: None,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))

    project_root = tmp_path / "project"
    project_root.mkdir()
    monkeypatch.chdir(project_root)

    local_skill_dir = project_root / ".claude" / "skills" / "demo"
    local_skill_dir.mkdir(parents=True)
    (local_skill_dir / "SKILL.md").write_text(LOCAL_SKILL_TEMPLATE, encoding="utf-8")

    invalid_global_skill_dir = home / ".claude" / "skills" / "broken"
    invalid_global_skill_dir.mkdir(parents=True)
    (invalid_global_skill_dir / "SKILL.md").write_text(
        INVALID_GLOBAL_SKILL_TEMPLATE,
        encoding="utf-8",
    )

    monkeypatch.setattr(
        agent_config, "load_system_prompt", lambda _base_path, model=None: ("SYSTEM", None)
    )
    monkeypatch.setattr(agent_config, "load_tunacode_context", lambda: ("CONTEXT", None))

    state_manager = StateManager()
    model_name = state_manager.session.current_model

    agent = agent_config.get_or_create_agent(model_name, state_manager)
    prompt = agent._state.system_prompt

    assert "# Available Skills" in prompt
    assert "Local demo skill" in prompt
    assert "broken" not in prompt


async def test_selected_skill_names_persist_across_save_and_load(
    clean_cache_manager: None,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "xdg-data"))

    state_manager = StateManager()
    state_manager.session.project_id = "project"
    state_manager.session.created_at = "2026-03-05T00:00:00+00:00"
    state_manager.session.working_directory = str(tmp_path)
    state_manager.session.selected_skill_names = ["nextstep-ui", "foo"]

    saved = await state_manager.save_session()

    assert saved is True

    reloaded_state_manager = StateManager()
    loaded = await reloaded_state_manager.load_session(state_manager.session.session_id)

    assert loaded is True
    assert reloaded_state_manager.session.selected_skill_names == ["nextstep-ui", "foo"]
