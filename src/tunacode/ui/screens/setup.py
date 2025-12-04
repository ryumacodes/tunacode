"""Setup wizard screen for first-time configuration."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Button, Input, Label, Select, Static

if TYPE_CHECKING:
    from tunacode.core.state import StateManager

PROVIDERS = [
    ("OpenRouter (recommended)", "openrouter"),
    ("OpenAI", "openai"),
    ("Anthropic", "anthropic"),
    ("Google", "google"),
]

DEFAULT_MODELS = {
    "openrouter": "openrouter:openai/gpt-4.1",
    "openai": "openai:gpt-4o",
    "anthropic": "anthropic:claude-3-5-sonnet-20241022",
    "google": "google:gemini-2.0-flash",
}

API_KEY_NAMES = {
    "openrouter": "OPENROUTER_API_KEY",
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "google": "GEMINI_API_KEY",
}


class SetupWizardScreen(Screen[None]):
    """Wizard screen for initial setup."""

    DEFAULT_CSS = """
    SetupWizardScreen {
        align: center middle;
    }

    #wizard-container {
        width: 60;
        height: auto;
        border: solid $primary;
        padding: 1 2;
        background: $surface;
    }

    #wizard-title {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
    }

    #wizard-subtitle {
        text-align: center;
        color: $text-muted;
        margin-bottom: 2;
    }

    .wizard-label {
        margin-top: 1;
        margin-bottom: 0;
    }

    #api-key-input {
        margin-bottom: 1;
    }

    #save-button {
        margin-top: 2;
        width: 100%;
    }

    #skip-button {
        width: 100%;
        margin-top: 1;
    }
    """

    def __init__(self, state_manager: "StateManager") -> None:
        super().__init__()
        self.state_manager = state_manager
        self._selected_provider = "openrouter"

    def compose(self) -> ComposeResult:
        yield Vertical(
            Static("TunaCode Setup", id="wizard-title"),
            Static("Configure your AI provider", id="wizard-subtitle"),
            Label("Provider:", classes="wizard-label"),
            Select(
                [(label, value) for label, value in PROVIDERS],
                value="openrouter",
                id="provider-select",
            ),
            Label("API Key:", classes="wizard-label"),
            Input(placeholder="Enter your API key...", password=True, id="api-key-input"),
            Button("Save & Start", id="save-button", variant="success"),
            Button("Skip (configure later)", id="skip-button", variant="default"),
            id="wizard-container",
        )

    def on_select_changed(self, event: Select.Changed) -> None:
        self._selected_provider = str(event.value)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "skip-button":
            self.app.pop_screen()
            return

        if event.button.id == "save-button":
            api_key_input = self.query_one("#api-key-input", Input)
            api_key = api_key_input.value.strip()

            if not api_key:
                self.notify("Please enter an API key", severity="warning")
                return

            self._save_config(api_key)
            self.app.pop_screen()

    def _save_config(self, api_key: str) -> None:
        provider = self._selected_provider
        model = DEFAULT_MODELS.get(provider, "openrouter:openai/gpt-4.1")
        key_name = API_KEY_NAMES.get(provider, "OPENROUTER_API_KEY")

        config = {
            "default_model": model,
            "env": {
                "ANTHROPIC_API_KEY": "",
                "GEMINI_API_KEY": "",
                "OPENAI_API_KEY": "",
                "OPENROUTER_API_KEY": "",
            },
            "settings": {
                "max_retries": 10,
                "max_iterations": 40,
                "enable_streaming": True,
            },
        }
        config["env"][key_name] = api_key

        config_dir = Path.home() / ".tunacode"
        config_dir.mkdir(mode=0o700, exist_ok=True)
        config_file = config_dir / "config.json"

        with open(config_file, "w") as f:
            json.dump(config, f, indent=2)

        self.state_manager.session.current_model = model
        self.state_manager.session.user_config = config

        self.notify(f"Saved! Using {model}")
