"""Test agent initialization to prevent NoneType errors."""

import pytest
from unittest.mock import MagicMock, patch, mock_open
from pathlib import Path
import os

from tunacode.core.state import StateManager
from tunacode.core.agents.main import get_or_create_agent


@pytest.mark.asyncio
async def test_agent_creation_with_missing_system_prompt_files():
    """Test that agent creation handles missing prompt files gracefully."""
    state_manager = StateManager()
    state_manager.session.current_model = "openai:gpt-4"
    state_manager.session.user_config = {
        "default_model": "openai:gpt-4",
        "env": {"OPENAI_API_KEY": "test-key"},
        "settings": {"max_retries": 3}
    }
    
    # Mock environment variable
    with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
        # Mock the Agent class to avoid actual OpenAI client creation
        mock_agent = MagicMock()
        mock_agent._system_prompts = ["You are a helpful AI assistant for software development tasks."]
        
        with patch('tunacode.core.agents.main.get_agent_tool') as mock_get_agent_tool:
            mock_Agent = MagicMock(return_value=mock_agent)
            mock_Tool = MagicMock()
            mock_get_agent_tool.return_value = (mock_Agent, mock_Tool)
            
            # Mock the file system to simulate missing prompt files
            with patch('pathlib.Path.open', side_effect=FileNotFoundError):
                with patch('builtins.open', side_effect=FileNotFoundError):
                    # This should not raise TypeError about NoneType
                    agent = get_or_create_agent(state_manager.session.current_model, state_manager)
                    
                    # Verify agent was created with default prompt
                    assert agent is not None
                    # Check that Agent was called with the default prompt
                    mock_Agent.assert_called_once()
                    args, kwargs = mock_Agent.call_args
                    assert kwargs['system_prompt'] == "You are a helpful AI assistant for software development tasks."


@pytest.mark.asyncio
async def test_agent_creation_with_system_txt():
    """Test that agent falls back to system.txt when system.md is missing."""
    state_manager = StateManager()
    state_manager.session.current_model = "openai:gpt-4"
    state_manager.session.user_config = {
        "default_model": "openai:gpt-4",
        "env": {"OPENAI_API_KEY": "test-key"},
        "settings": {"max_retries": 3}
    }
    
    txt_content = "Test prompt from system.txt"
    
    with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
        mock_agent = MagicMock()
        mock_agent._system_prompts = [txt_content]
        
        with patch('tunacode.core.agents.main.get_agent_tool') as mock_get_agent_tool:
            mock_Agent = MagicMock(return_value=mock_agent)
            mock_Tool = MagicMock()
            mock_get_agent_tool.return_value = (mock_Agent, mock_Tool)
            
            def mock_open_file(path, *args, **kwargs):
                if str(path).endswith('system.md'):
                    raise FileNotFoundError
                elif str(path).endswith('system.txt'):
                    return mock_open(read_data=txt_content)()
                raise FileNotFoundError
            
            with patch('builtins.open', side_effect=mock_open_file):
                agent = get_or_create_agent(state_manager.session.current_model, state_manager)
                
                assert agent is not None
                # Check that Agent was called with the txt content
                mock_Agent.assert_called_once()
                args, kwargs = mock_Agent.call_args
                assert kwargs['system_prompt'] == txt_content


@pytest.mark.asyncio
async def test_agent_creation_with_system_md():
    """Test that agent uses system.md when available."""
    state_manager = StateManager()
    state_manager.session.current_model = "openai:gpt-4"
    state_manager.session.user_config = {
        "default_model": "openai:gpt-4", 
        "env": {"OPENAI_API_KEY": "test-key"},
        "settings": {"max_retries": 3}
    }
    
    md_content = "Test prompt from system.md"
    
    with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
        mock_agent = MagicMock()
        mock_agent._system_prompts = [md_content]
        
        with patch('tunacode.core.agents.main.get_agent_tool') as mock_get_agent_tool:
            mock_Agent = MagicMock(return_value=mock_agent)
            mock_Tool = MagicMock()
            mock_get_agent_tool.return_value = (mock_Agent, mock_Tool)
            
            with patch('builtins.open', mock_open(read_data=md_content)):
                agent = get_or_create_agent(state_manager.session.current_model, state_manager)
                
                assert agent is not None
                # Check that Agent was called with the md content
                mock_Agent.assert_called_once()
                args, kwargs = mock_Agent.call_args
                assert kwargs['system_prompt'] == md_content


def test_agent_never_receives_none_system_prompt():
    """Ensure our code never passes None as system_prompt."""
    state_manager = StateManager()
    state_manager.session.current_model = "openai:gpt-4"
    state_manager.session.user_config = {
        "default_model": "openai:gpt-4",
        "env": {"OPENAI_API_KEY": "test-key"},
        "settings": {"max_retries": 3}
    }
    
    with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
        mock_agent = MagicMock()
        
        with patch('tunacode.core.agents.main.get_agent_tool') as mock_get_agent_tool:
            mock_Agent = MagicMock(return_value=mock_agent)
            mock_Tool = MagicMock()
            mock_get_agent_tool.return_value = (mock_Agent, mock_Tool)
            
            # Even with all files missing, we should never pass None
            with patch('pathlib.Path.open', side_effect=FileNotFoundError):
                with patch('builtins.open', side_effect=FileNotFoundError):
                    agent = get_or_create_agent(state_manager.session.current_model, state_manager)
                    
                    # Verify that system_prompt was never None
                    mock_Agent.assert_called_once()
                    args, kwargs = mock_Agent.call_args
                    assert kwargs['system_prompt'] is not None
                    assert isinstance(kwargs['system_prompt'], str)
                    assert len(kwargs['system_prompt']) > 0