import pytest
from tunacode.core.state import StateManager

def test_user_config_defaults_and_mutation():
    """
    Characterization: user_config defaults to empty dict and is mutable.
    """
    sm = StateManager()
    assert sm.session.user_config == {}
    sm.session.user_config["theme"] = "dark"
    assert sm.session.user_config["theme"] == "dark"

def test_user_config_reset_on_session_reset():
    """
    Characterization: user_config is reset to empty dict on session reset.
    """
    sm = StateManager()
    sm.session.user_config["foo"] = "bar"
    sm.reset_session()
    assert sm.session.user_config == {}

def test_user_config_is_per_session():
    """
    Characterization: user_config is per-session, not shared.
    """
    sm1 = StateManager()
    sm2 = StateManager()
    sm1.session.user_config["x"] = 1
    assert sm2.session.user_config == {}

# Quirk: No config file loading, no error handling for config, only in-memory dict.