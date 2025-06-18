import pytest
from tunacode.core.state import StateManager

def test_agents_field_defaults_and_mutation():
    """
    Characterization: agents field defaults to empty dict and is mutable.
    """
    sm = StateManager()
    assert sm.session.agents == {}
    sm.session.agents["agent1"] = object()
    assert "agent1" in sm.session.agents

def test_agents_reset_on_session_reset():
    """
    Characterization: agents dict is reset on session reset.
    """
    sm = StateManager()
    sm.session.agents["agent2"] = object()
    sm.reset_session()
    assert sm.session.agents == {}

def test_agents_are_per_session():
    """
    Characterization: agents dict is per-session, not shared.
    """
    sm1 = StateManager()
    sm2 = StateManager()
    sm1.session.agents["a"] = 1
    assert sm2.session.agents == {}

# Quirk: No agent lifecycle management, only dict storage.