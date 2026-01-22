"""Tests for agent cache invalidation on abort.

Bug: When user hits ESC to abort a request, the HTTP client in the cached agent
may have a broken connection. The next request reuses this broken agent and hangs.

Fix: Invalidate agent cache (both module-level and session-level) on abort.
"""

from unittest.mock import MagicMock

import pytest

from tunacode.core.agents.agent_components.agent_config import (
    _AGENT_CACHE,
    _AGENT_CACHE_VERSION,
    clear_all_caches,
)


@pytest.fixture
def clean_caches():
    """Ensure caches are clean before and after each test."""
    clear_all_caches()
    yield
    clear_all_caches()


@pytest.fixture
def mock_session():
    """Create a mock session with agent storage."""
    session = MagicMock()
    session.agents = {}
    session.agent_versions = {}
    return session


@pytest.fixture
def mock_state_manager(mock_session):
    """Create a mock state manager."""
    state_manager = MagicMock()
    state_manager.session = mock_session
    return state_manager


def test_abort_should_invalidate_agent_cache(clean_caches, mock_state_manager):
    """After abort, agent cache should be cleared to force fresh HTTP client.

    This test captures the bug where ESC abort leaves a broken HTTP client
    in the cache, causing subsequent requests to hang.
    """
    from tunacode.core.agents.agent_components.agent_config import (
        invalidate_agent_cache,
    )

    model = "test:model"
    mock_agent = MagicMock()
    version = 12345

    # Populate both caches (simulating normal agent creation)
    _AGENT_CACHE[model] = mock_agent
    _AGENT_CACHE_VERSION[model] = version
    mock_state_manager.session.agents[model] = mock_agent
    mock_state_manager.session.agent_versions[model] = version

    # Verify caches are populated
    assert model in _AGENT_CACHE
    assert model in mock_state_manager.session.agents

    # Simulate abort - this should clear the caches
    invalidated = invalidate_agent_cache(model, mock_state_manager)

    # Verify caches are cleared
    assert invalidated is True
    assert model not in _AGENT_CACHE, "Module cache should be cleared after abort"
    assert model not in _AGENT_CACHE_VERSION, "Module version cache should be cleared"
    assert model not in mock_state_manager.session.agents, "Session cache should be cleared"
    assert model not in mock_state_manager.session.agent_versions, (
        "Session version should be cleared"
    )


def test_invalidate_returns_false_when_not_cached(clean_caches, mock_state_manager):
    """invalidate_agent_cache returns False if agent wasn't in cache."""
    from tunacode.core.agents.agent_components.agent_config import (
        invalidate_agent_cache,
    )

    model = "uncached:model"

    # Cache is empty
    assert model not in _AGENT_CACHE

    # Should return False (nothing to invalidate)
    invalidated = invalidate_agent_cache(model, mock_state_manager)
    assert invalidated is False
