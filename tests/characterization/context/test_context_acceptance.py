"""Acceptance tests for TUNACODE.md context injection into agent."""

import asyncio
import sys
import tempfile
import os
from pathlib import Path
from unittest import mock

import pytest

from tunacode.core.agents.main import get_or_create_agent, process_request
from tunacode.core.state import StateManager
from tunacode.context import get_code_style, get_context


@pytest.mark.asyncio
async def test_agent_includes_tunacode_md_context_in_system_prompt():
    """Acceptance test: Verify that TUNACODE.md context is loaded properly."""
    # Given: A TUNACODE.md file exists with project context
    tunacode_content = """# TUNACODE.md

## Build Commands
- Run tests: `make test`
- Run single test: `pytest tests/test_file.py::test_name`
- Lint: `make lint`

## Code Style
- Use type hints for all functions
- Follow PEP 8 conventions
- Prefer guard clauses over nested conditionals
"""
    
    # Mock the file system to have TUNACODE.md
    with mock.patch("pathlib.Path.exists") as mock_exists:
        with mock.patch("pathlib.Path.read_text") as mock_read:
            # Mock exists to return True for TUNACODE.md
            mock_exists.return_value = True
            mock_read.return_value = tunacode_content
            
            # When: We get the full context
            context = await get_context()
            
            # Then: Code style should contain TUNACODE.md content
            assert "codeStyle" in context
            style = context["codeStyle"]
            assert "Run tests: `make test`" in style
            assert "Use type hints for all functions" in style
            assert "Prefer guard clauses over nested conditionals" in style
            
            # And: Should have all context types
            assert "git" in context
            assert "directory" in context
            assert "claudeFiles" in context


@pytest.mark.asyncio
async def test_agent_loads_tunacode_md_into_system_prompt():
    """Test that the agent actually loads TUNACODE.md into its system prompt."""
    # Create a temporary directory with TUNACODE.md
    with tempfile.TemporaryDirectory() as tmpdir:
        tunacode_path = Path(tmpdir) / "TUNACODE.md"
        tunacode_content = """# Project-Specific Context

## Build Commands
- Run tests: `make test`
- Lint: `make lint`

## Code Style  
- Use type hints for all functions
- Follow guard clause pattern
"""
        tunacode_path.write_text(tunacode_content)
        
        # Change to temp directory
        original_cwd = os.getcwd()
        try:
            os.chdir(tmpdir)
            
            # Create agent
            state_manager = StateManager()
            agent = get_or_create_agent("openai:gpt-4", state_manager)
            
            # Agent should be created successfully
            assert agent is not None
            
            # If we have access to real pydantic_ai, check system prompt
            if hasattr(agent, 'system_prompt'):
                assert "Project Context from TUNACODE.md" in agent.system_prompt
                assert "Use type hints for all functions" in agent.system_prompt
                assert "Follow guard clause pattern" in agent.system_prompt
            
        finally:
            os.chdir(original_cwd)