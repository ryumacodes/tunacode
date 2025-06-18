"""
Shared fixtures and utilities for agent characterization tests.
"""
import pytest
from unittest.mock import Mock


@pytest.fixture
def state_manager():
    """Create a standard mock state manager for testing."""
    sm = Mock()
    sm.session = Mock()
    sm.session.messages = []
    sm.session.agents = {}
    sm.session.user_config = {
        "settings": {
            "max_retries": 3,
            "max_iterations": 20,
            "fallback_response": True,
            "fallback_verbosity": "normal"
        }
    }
    sm.session.show_thoughts = False
    sm.session.tool_calls = []
    sm.session.files_in_context = set()
    sm.session.iteration_count = 0
    sm.session.current_iteration = 0
    return sm


@pytest.fixture
def mock_ui():
    """Mock UI console functions."""
    from unittest.mock import AsyncMock
    import tunacode.ui.console as ui
    
    ui.muted = AsyncMock()
    ui.error = AsyncMock()
    ui.warning = AsyncMock()
    
    return ui