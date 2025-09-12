"""
Unit tests for new model selection persistence behavior (post-fix).

Validates that selecting a model without the 'default' keyword
now persists to the configuration file by default.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from tunacode.cli.commands.implementations.model import ModelCommand
from tunacode.types import CommandContext


@pytest.fixture
def temp_config(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp:
        cfg_dir = Path(tmp)
        cfg_file = cfg_dir / "tunacode.json"
        # Patch settings to point to temp file
        monkeypatch.setattr(
            "tunacode.utils.user_configuration.ApplicationSettings",
            lambda: MagicMock(paths=MagicMock(config_dir=cfg_dir, config_file=cfg_file)),
        )
        yield cfg_dir, cfg_file


@pytest.fixture
def mock_context():
    ctx = MagicMock(spec=CommandContext)
    ctx.state_manager = MagicMock()
    ctx.state_manager.session = MagicMock()
    ctx.state_manager.session.user_config = {}
    ctx.state_manager.session.current_model = "openai:gpt-4"
    return ctx


@pytest.fixture
def command():
    cmd = ModelCommand()
    cmd._registry_loaded = True
    cmd.registry = MagicMock()
    return cmd


@pytest.mark.asyncio
async def test_direct_model_selection_persists_by_default(command, mock_context, temp_config):
    cfg_dir, cfg_file = temp_config

    # Registry returns valid model
    model_info = MagicMock()
    model_info.full_id = "openai:gpt-4o"
    model_info.name = "GPT-4o"
    command.registry.get_model.return_value = model_info

    # Execute without 'default'
    await command._set_model("openai:gpt-4o", [], mock_context)

    # Session updated
    assert mock_context.state_manager.session.current_model == "openai:gpt-4o"
    # Config persisted
    assert cfg_file.exists()
    data = json.loads(cfg_file.read_text())
    assert data.get("default_model") == "openai:gpt-4o"


@pytest.mark.asyncio
async def test_default_keyword_still_returns_restart(command, mock_context, temp_config):
    cfg_dir, cfg_file = temp_config

    model_info = MagicMock()
    model_info.full_id = "anthropic:claude-3-sonnet"
    model_info.name = "Claude 3 Sonnet"
    command.registry.get_model.return_value = model_info

    result = await command._set_model("anthropic:claude-3-sonnet", ["default"], mock_context)
    assert result == "restart"
    assert cfg_file.exists()
    data = json.loads(cfg_file.read_text())
    assert data.get("default_model") == "anthropic:claude-3-sonnet"


@pytest.mark.asyncio
async def test_search_single_match_persists(command, mock_context, temp_config):
    cfg_dir, cfg_file = temp_config

    model_info = MagicMock()
    model_info.full_id = "google:gemini-pro"
    model_info.name = "Gemini Pro"
    command.registry.search_models.return_value = [model_info]

    await command._set_model("gemini-pro", [], mock_context)
    assert mock_context.state_manager.session.current_model == "google:gemini-pro"
    assert cfg_file.exists()
    data = json.loads(cfg_file.read_text())
    assert data.get("default_model") == "google:gemini-pro"


@pytest.mark.asyncio
async def test_interactive_single_result_persists(command, mock_context, temp_config):
    cfg_dir, cfg_file = temp_config

    model_info = MagicMock()
    model_info.full_id = "openrouter:meta-llama-3.1-8b-instruct"
    model_info.name = "Llama 3.1 8B Instruct"
    command.registry.search_models.return_value = [model_info]

    await command._interactive_select(mock_context, initial_query="llama 3.1")
    assert (
        mock_context.state_manager.session.current_model == "openrouter:meta-llama-3.1-8b-instruct"
    )
    assert cfg_file.exists()
    data = json.loads(cfg_file.read_text())
    assert data.get("default_model") == "openrouter:meta-llama-3.1-8b-instruct"
