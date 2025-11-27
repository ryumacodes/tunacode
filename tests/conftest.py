"""Shared pytest fixtures for tunacode tests.

This module contains commonly used fixtures across multiple test files
to reduce code duplication and maintain consistent test setup.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tunacode.core.agents.main import AgentConfig
from tunacode.core.state import StateManager

if TYPE_CHECKING:
    from tunacode.types import ModelName


@pytest.fixture
def state_manager() -> StateManager:
    """Create a StateManager with initialized session."""
    manager = StateManager()
    # SessionState is already created in __init__
    # Initialize additional attributes that aren't in SessionState defaults
    session = manager.session
    session.batch_counter = 0
    session.original_query = ""
    # Initialize dynamic attributes used by handlers
    setattr(session, "consecutive_empty_responses", 0)
    setattr(session, "request_id", "test-req-id")
    return manager


@pytest.fixture
def agent_config() -> AgentConfig:
    """Create default agent configuration."""
    return AgentConfig(
        max_iterations=15,
        unproductive_limit=3,
        forced_react_interval=2,
        forced_react_limit=5,
        debug_metrics=False,
    )


@pytest.fixture
def mock_model() -> ModelName:
    """Create a mock model name."""
    return "claude-3-5-sonnet-20241022"  # type: ignore[return-value]
