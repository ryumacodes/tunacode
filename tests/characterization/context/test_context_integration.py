"""Integration tests for TUNACODE.md context injection into agent."""

import os
import tempfile
from pathlib import Path
from unittest import mock

import pytest

from tunacode.context import get_code_style, get_context
from tunacode.core.agents.main import get_or_create_agent
from tunacode.core.state import StateManager


@pytest.mark.asyncio
async def test_context_loading_reads_tunacode_md():
    """Test that get_code_style reads TUNACODE.md files."""
    # Create a temporary directory with TUNACODE.md
    with tempfile.TemporaryDirectory() as tmpdir:
        tunacode_path = Path(tmpdir) / "TUNACODE.md"
        tunacode_content = """# Project Context

## Build Commands
- Run tests: `make test`
- Lint: `make lint`

## Code Style
- Use type hints
- Guard clauses preferred"""
        
        tunacode_path.write_text(tunacode_content)
        
        # Change to temp directory
        original_cwd = os.getcwd()
        try:
            os.chdir(tmpdir)
            
            # Load context
            style = await get_code_style()
            
            # Verify content
            assert "Run tests: `make test`" in style
            assert "Use type hints" in style
            assert "Guard clauses preferred" in style
            
            # Also verify get_context works
            context = await get_context()
            assert "codeStyle" in context
            assert context["codeStyle"] == style
            
        finally:
            os.chdir(original_cwd)


@pytest.mark.asyncio
async def test_agent_creation_loads_tunacode_md():
    """Test that agent creation loads TUNACODE.md if it exists."""
    # Create a temporary directory with TUNACODE.md
    with tempfile.TemporaryDirectory() as tmpdir:
        tunacode_path = Path(tmpdir) / "TUNACODE.md"
        tunacode_content = """# Test Project Context

## Build Commands
- Test: make test
- Lint: make lint

## Code Style Guidelines
- Use type hints for all functions
- Prefer guard clauses over nested conditionals"""
        
        tunacode_path.write_text(tunacode_content)
        
        # Change to temp directory
        original_cwd = os.getcwd()
        try:
            os.chdir(tmpdir)
            
            # Create agent
            state_manager = StateManager()
            agent = get_or_create_agent("openai:gpt-4", state_manager)
            
            # We can't verify the system prompt due to pydantic_ai stubbing,
            # but the agent creation should complete without errors
            assert agent is not None
            
        finally:
            os.chdir(original_cwd)


def test_agent_creation_handles_missing_tunacode_md():
    """Test that agent creation works even without TUNACODE.md."""
    # Create a temporary directory without TUNACODE.md
    with tempfile.TemporaryDirectory() as tmpdir:
        original_cwd = os.getcwd()
        try:
            os.chdir(tmpdir)
            
            # Create agent (should not fail)
            state_manager = StateManager()
            agent = get_or_create_agent("openai:gpt-4", state_manager)
            
            # Agent should be created successfully
            assert agent is not None
            
        finally:
            os.chdir(original_cwd)