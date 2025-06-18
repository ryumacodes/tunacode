import pytest
from tunacode.core.state import StateManager, SessionState

def test_state_manager_initialization_defaults():
    """
    Characterization: StateManager initializes with default SessionState.
    """
    sm = StateManager()
    session = sm.session
    assert isinstance(session, SessionState)
    # Check default values
    assert session.user_config == {}
    assert session.agents == {}
    assert session.messages == []
    assert session.total_cost == 0.0
    assert session.current_model == "openai:gpt-4o"
    assert session.spinner is None
    assert session.tool_ignore == []
    assert session.yolo is False
    assert session.undo_initialized is False
    assert session.show_thoughts is False
    assert isinstance(session.session_id, str)
    assert session.device_id is None
    assert session.input_sessions == {}
    assert session.current_task is None
    assert session.files_in_context == set()
    assert session.tool_calls == []
    assert session.iteration_count == 0
    assert session.current_iteration == 0

def test_state_manager_reset_session():
    """
    Characterization: reset_session creates a new SessionState instance.
    """
    sm = StateManager()
    old_id = sm.session.session_id
    sm.session.user_config["foo"] = "bar"
    sm.reset_session()
    assert sm.session.user_config == {}
    assert sm.session.session_id != old_id

def test_state_manager_no_singleton_enforced():
    """
    Characterization: Multiple StateManager instances can be created (no singleton).
    """
    sm1 = StateManager()
    sm2 = StateManager()
    assert sm1 is not sm2
    assert sm1.session is not sm2.session

def test_state_manager_config_field_behavior():
    """
    Characterization: user_config is a field, not a constructor arg.
    """
    sm = StateManager()
    sm.session.user_config["theme"] = "dark"
    assert sm.session.user_config["theme"] == "dark"
    sm.reset_session()
    # After reset, config is empty
    assert sm.session.user_config == {}

# Quirk: No error handling for config, no singleton pattern, all fields defaulted.