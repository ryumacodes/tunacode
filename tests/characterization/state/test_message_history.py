import pytest
from tunacode.core.state import StateManager

def test_message_history_defaults_and_append():
    """
    Characterization: messages field defaults to empty list and is mutable.
    """
    sm = StateManager()
    assert sm.session.messages == []
    sm.session.messages.append({"role": "user", "content": "hello"})
    assert sm.session.messages[0]["content"] == "hello"

def test_message_history_reset_on_session_reset():
    """
    Characterization: messages list is reset on session reset.
    """
    sm = StateManager()
    sm.session.messages.append({"role": "system", "content": "init"})
    sm.reset_session()
    assert sm.session.messages == []

def test_message_history_is_per_session():
    """
    Characterization: messages list is per-session, not shared.
    """
    sm1 = StateManager()
    sm2 = StateManager()
    sm1.session.messages.append({"role": "user", "content": "foo"})
    assert sm2.session.messages == []

def test_message_history_mutation():
    """
    Characterization: messages list supports mutation (append, pop, clear).
    """
    sm = StateManager()
    sm.session.messages.append({"role": "user", "content": "a"})
    sm.session.messages.append({"role": "assistant", "content": "b"})
    assert len(sm.session.messages) == 2
    sm.session.messages.pop()
    assert len(sm.session.messages) == 1
    sm.session.messages.clear()
    assert sm.session.messages == []

# Quirk: No message validation, no history limits, only list storage.