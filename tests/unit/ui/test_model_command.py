from __future__ import annotations

import copy
from dataclasses import dataclass, field
from typing import Any, cast

import pytest

from tunacode.configuration.defaults import DEFAULT_USER_CONFIG

from tunacode.core.session import StateManager

from tunacode.ui.commands.model import ModelCommand
from tunacode.ui.screens.model_picker import ModelPickerScreen


@dataclass
class _FakeChatContainer:
    messages: list[str] = field(default_factory=list)

    def write(self, message: str) -> None:
        self.messages.append(message)


class _FakeApp:
    def __init__(self, *, auto_select_model: bool = False) -> None:
        self.state_manager = StateManager()
        self.chat_container = _FakeChatContainer()
        self.notifications: list[tuple[str, str]] = []
        self.pushed_screens: list[tuple[object, Any]] = []
        self.resource_bar_updates = 0
        self.auto_select_model = auto_select_model

    def notify(self, message: str, severity: str = "information") -> None:
        self.notifications.append((message, severity))

    def push_screen(self, screen: object, callback: Any | None = None) -> None:
        self.pushed_screens.append((screen, callback))

        if (
            self.auto_select_model
            and callback is not None
            and isinstance(screen, ModelPickerScreen)
        ):
            callback("openai:gpt-5")

    def _update_resource_bar(self) -> None:
        self.resource_bar_updates += 1


@pytest.mark.asyncio
async def test_model_command_execute_without_args_opens_single_model_picker(monkeypatch) -> None:
    app = _FakeApp()

    monkeypatch.setattr(
        "tunacode.core.ui_api.user_configuration.load_config_with_defaults",
        lambda default_config: dict(default_config),
    )

    await ModelCommand().execute(cast(Any, app), "")

    assert len(app.pushed_screens) == 1
    assert isinstance(app.pushed_screens[0][0], ModelPickerScreen)


def test_apply_model_selection_updates_default_model_and_recent_history(monkeypatch) -> None:
    app = _FakeApp()
    app.state_manager.session.user_config = {
        "default_model": "anthropic:claude-sonnet-4",
        "recent_models": ["anthropic:claude-sonnet-4"],
        "env": {},
        "settings": {},
    }
    save_calls: list[StateManager] = []
    invalidations: list[tuple[str, StateManager]] = []

    monkeypatch.setattr(
        "tunacode.core.ui_api.configuration.get_model_context_window",
        lambda full_model: 123456,
    )
    monkeypatch.setattr(
        "tunacode.core.ui_api.user_configuration.save_config",
        lambda state_manager: save_calls.append(state_manager),
    )
    monkeypatch.setattr(
        "tunacode.core.agents.agent_components.agent_config.invalidate_agent_cache",
        lambda full_model, state_manager: invalidations.append((full_model, state_manager)),
    )

    ModelCommand()._apply_model_selection(cast(Any, app), "openai:gpt-5")

    session = app.state_manager.session
    assert session.current_model == "openai:gpt-5"
    assert session.user_config["default_model"] == "openai:gpt-5"
    assert session.user_config["recent_models"][0] == "openai:gpt-5"
    assert session.conversation.max_tokens == 123456
    assert save_calls == [app.state_manager]
    assert invalidations == [("openai:gpt-5", app.state_manager)]
    assert app.resource_bar_updates == 1
    assert app.notifications[-1] == ("Model: openai:gpt-5", "information")


def test_handle_direct_model_selection_applies_model_when_provider_is_ready(monkeypatch) -> None:
    app = _FakeApp()
    applied_models: list[str] = []

    monkeypatch.setattr("tunacode.core.ui_api.configuration.load_models_registry", lambda: {})
    monkeypatch.setattr(
        "tunacode.ui.commands.model._validate_provider_api_key_with_notification",
        lambda *args, **kwargs: True,
    )
    monkeypatch.setattr(
        ModelCommand,
        "_apply_model_selection",
        lambda self, _app, full_model: applied_models.append(full_model),
    )

    ModelCommand()._handle_direct_model_selection(cast(Any, app), "openai:gpt-5")

    assert applied_models == ["openai:gpt-5"]


def test_open_model_picker_pushes_api_key_entry_when_selection_needs_credentials(
    monkeypatch,
) -> None:
    app = _FakeApp(auto_select_model=True)
    app.state_manager.session.user_config = copy.deepcopy(DEFAULT_USER_CONFIG)
    app.state_manager.session.current_model = "openrouter:openai/gpt-4.1"

    monkeypatch.setattr(
        "tunacode.ui.commands.model._validate_provider_api_key_with_notification",
        lambda *args, **kwargs: False,
    )

    ModelCommand()._open_model_picker(cast(Any, app))

    assert [screen.__class__.__name__ for screen, _ in app.pushed_screens] == [
        "ModelPickerScreen",
        "ApiKeyEntryScreen",
    ]
