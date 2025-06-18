import pytest
from tunacode.core.state import StateManager

def test_session_persistence_and_reset():
    """
    Characterization: Session persists within StateManager instance, reset_session replaces it.
    """
    sm = StateManager()
    sm.session.user_config["foo"] = "bar"
    # Session persists changes
    assert sm.session.user_config["foo"] == "bar"
    # After reset, session is new
    sm.reset_session()
    assert sm.session.user_config == {}
    # New session_id after reset
    assert isinstance(sm.session.session_id, str)

def test_multiple_sessions_are_independent():
    """
    Characterization: Multiple StateManager instances have independent sessions.
    """
    sm1 = StateManager()
    sm2 = StateManager()
    sm1.session.user_config["a"] = 1
    sm2.session.user_config["b"] = 2
    assert sm1.session.user_config == {"a": 1}
    assert sm2.session.user_config == {"b": 2}

def test_session_id_is_unique():
    """
    Characterization: Each session gets a unique session_id.
    """
    sm1 = StateManager()
    sm2 = StateManager()
    assert sm1.session.session_id != sm2.session.session_id

# Quirk: No session persistence to disk, no session loading, only in-memory session.