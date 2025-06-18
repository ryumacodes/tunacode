"""
Characterization tests for TunaCode UI prompt rendering and management.
Covers: PromptConfig, PromptManager, prompt customization, and error paths.
"""

import pytest
from unittest.mock import patch, MagicMock

import tunacode.ui.prompt_manager as prompt_mod

def test_prompt_config_defaults():
    config = prompt_mod.PromptConfig()
    assert config.multiline is False
    assert config.is_password is False
    assert config.validator is None

def test_prompt_manager_creates_style():
    mgr = prompt_mod.PromptManager()
    style = mgr._create_style()
    assert hasattr(style, "get_attrs_for_style_str")

def test_prompt_manager_get_session_creates_prompt_session():
    config = prompt_mod.PromptConfig()
    mgr = prompt_mod.PromptManager()
    with patch("tunacode.ui.prompt_manager.PromptSession") as mock_session:
        session = MagicMock()
        mock_session.return_value = session
        result = mgr.get_session("test", config)
        assert result is session
        mock_session.assert_called_once()

def test_prompt_manager_handles_user_abort():
    config = prompt_mod.PromptConfig()
    mgr = prompt_mod.PromptManager()
    with patch("tunacode.ui.prompt_manager.PromptSession", side_effect=prompt_mod.UserAbortError):
        with pytest.raises(prompt_mod.UserAbortError):
            mgr.get_session("test", config)