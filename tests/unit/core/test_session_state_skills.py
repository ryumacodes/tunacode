from __future__ import annotations

from pathlib import Path

from tunacode.core.session import StateManager


async def test_selected_skill_names_round_trip_through_session_persistence(
    tmp_path: Path,
    monkeypatch,
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
