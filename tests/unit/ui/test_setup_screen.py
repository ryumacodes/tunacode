from __future__ import annotations

from textual.app import App, ComposeResult
from textual.widgets import Input, Static

from tunacode.core.session import StateManager

from tunacode.ui.screens.setup import SetupScreen


class TestSetupHostApp(App[None]):
    __test__ = False

    def __init__(self, state_manager: StateManager) -> None:
        super().__init__()
        self.state_manager = state_manager

    def compose(self) -> ComposeResult:
        yield Static("host")


async def test_setup_screen_save_records_recent_model(monkeypatch) -> None:
    state_manager = StateManager()
    app = TestSetupHostApp(state_manager)
    screen = SetupScreen(state_manager)
    dismissed_results: list[bool] = []
    save_calls: list[StateManager] = []

    monkeypatch.setattr(screen, "dismiss", lambda result: dismissed_results.append(result))
    monkeypatch.setattr(
        "tunacode.ui.screens.setup.save_config",
        lambda manager: save_calls.append(manager),
    )

    async with app.run_test(headless=True) as pilot:
        app.push_screen(screen)
        await pilot.pause()

        api_key_input = screen.query_one("#api-key-input", Input)
        api_key_input.value = "test-api-key"
        screen._save_and_dismiss()

    full_model = state_manager.session.current_model
    assert state_manager.session.user_config["default_model"] == full_model
    assert state_manager.session.user_config["recent_models"][0] == full_model
    assert save_calls == [state_manager]
    assert dismissed_results == [True]
