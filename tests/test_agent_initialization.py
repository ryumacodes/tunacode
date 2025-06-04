"""Test agent initialization to prevent NoneType errors."""

import pytest
from unittest.mock import MagicMock, patch, mock_open
from pathlib import Path

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
    
    # Mock the file system to simulate missing prompt files
    with patch('pathlib.Path.open', side_effect=FileNotFoundError):
        with patch('builtins.open', side_effect=FileNotFoundError):
            # This should not raise TypeError about NoneType
            agent = get_or_create_agent(state_manager.session.current_model, state_manager)
            
            # Verify agent was created with default prompt
            assert agent is not None
            assert hasattr(agent, '_system_prompts')
            # Check that a default prompt was used
            assert agent._system_prompts is not None
            assert len(agent._system_prompts) > 0
            assert agent._system_prompts[0] == "You are a helpful AI assistant for software development tasks."


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
    
    def mock_open_file(path, *args, **kwargs):
        if str(path).endswith('system.md'):
            raise FileNotFoundError
        elif str(path).endswith('system.txt'):
            return mock_open(read_data=txt_content)()
        raise FileNotFoundError
    
    with patch('builtins.open', side_effect=mock_open_file):
        agent = get_or_create_agent(state_manager.session.current_model, state_manager)
        
        assert agent is not None
        assert hasattr(agent, '_system_prompts')
        assert agent._system_prompts[0] == txt_content


@pytest.mark.asyncio
async def test_agent_creation_with_system_md():
    """Test that agent uses system.md when available."""
    state_manager = StateManager()
    state_manager.session.current_model = "openai:gpt-4"
    state_manager.session.user_config = {
        "default_model": "openai:gpt-4", 
        "env": {"OPENAI_API_KEY": "test-key"}
    }
    
    md_content = "Test prompt from system.md"
    
    with patch('builtins.open', mock_open(read_data=md_content)):
        agent = get_or_create_agent(state_manager.session.current_model, state_manager)
        
        assert agent is not None
        assert hasattr(agent, '_system_prompts')
        assert agent._system_prompts[0] == md_content


def test_agent_never_receives_none_system_prompt():
    """Ensure Agent class never receives None as system_prompt."""
    from pydantic_ai import Agent
    
    # This should raise TypeError if we pass None
    with pytest.raises(TypeError, match="'NoneType' object is not iterable"):
        Agent(
            model="openai:gpt-4",
            system_prompt=None,  # This is what was happening
            tools=[]
        )