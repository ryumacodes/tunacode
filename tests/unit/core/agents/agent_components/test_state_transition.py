"""Tests for tunacode.core.agents.agent_components.state_transition."""

import pytest

from tunacode.core.agents.agent_components.state_transition import (
    AGENT_TRANSITION_RULES,
    AgentStateMachine,
    InvalidStateTransitionError,
    StateTransitionRules,
)
from tunacode.core.types import AgentState


class TestStateTransitionRules:
    def test_valid_transition(self):
        assert AGENT_TRANSITION_RULES.is_valid_transition(
            AgentState.USER_INPUT, AgentState.ASSISTANT
        )

    def test_invalid_transition(self):
        assert not AGENT_TRANSITION_RULES.is_valid_transition(
            AgentState.USER_INPUT, AgentState.RESPONSE
        )

    def test_get_valid_next_states(self):
        states = AGENT_TRANSITION_RULES.get_valid_next_states(AgentState.ASSISTANT)
        assert AgentState.TOOL_EXECUTION in states
        assert AgentState.RESPONSE in states

    def test_empty_transitions(self):
        rules = StateTransitionRules(valid_transitions={})
        assert rules.get_valid_next_states(AgentState.USER_INPUT) == set()


class TestAgentStateMachine:
    def test_initial_state(self):
        sm = AgentStateMachine(AgentState.USER_INPUT, AGENT_TRANSITION_RULES)
        assert sm.current_state == AgentState.USER_INPUT

    def test_valid_transition(self):
        sm = AgentStateMachine(AgentState.USER_INPUT, AGENT_TRANSITION_RULES)
        sm.transition_to(AgentState.ASSISTANT)
        assert sm.current_state == AgentState.ASSISTANT

    def test_invalid_transition_raises(self):
        sm = AgentStateMachine(AgentState.USER_INPUT, AGENT_TRANSITION_RULES)
        with pytest.raises(InvalidStateTransitionError):
            sm.transition_to(AgentState.RESPONSE)

    def test_self_transition_is_noop(self):
        rules = StateTransitionRules(
            valid_transitions={AgentState.ASSISTANT: {AgentState.ASSISTANT, AgentState.RESPONSE}}
        )
        sm = AgentStateMachine(AgentState.ASSISTANT, rules)
        sm.transition_to(AgentState.ASSISTANT)
        assert sm.current_state == AgentState.ASSISTANT

    def test_can_transition_to(self):
        sm = AgentStateMachine(AgentState.USER_INPUT, AGENT_TRANSITION_RULES)
        assert sm.can_transition_to(AgentState.ASSISTANT)
        assert not sm.can_transition_to(AgentState.RESPONSE)

    def test_completion_detection(self):
        sm = AgentStateMachine(AgentState.USER_INPUT, AGENT_TRANSITION_RULES)
        assert not sm.is_completed()

        sm.transition_to(AgentState.ASSISTANT)
        sm.transition_to(AgentState.RESPONSE)
        assert not sm.is_completed()

        sm.set_completion_detected(True)
        assert sm.is_completed()

    def test_completion_only_in_response(self):
        sm = AgentStateMachine(AgentState.USER_INPUT, AGENT_TRANSITION_RULES)
        sm.set_completion_detected(True)
        assert not sm.is_completed()  # Not in RESPONSE state

    def test_reset(self):
        sm = AgentStateMachine(AgentState.USER_INPUT, AGENT_TRANSITION_RULES)
        sm.transition_to(AgentState.ASSISTANT)
        sm.transition_to(AgentState.RESPONSE)
        sm.set_completion_detected(True)

        sm.reset()
        assert sm.current_state == AgentState.USER_INPUT
        assert not sm.is_completed()

    def test_reset_to_custom_state(self):
        sm = AgentStateMachine(AgentState.USER_INPUT, AGENT_TRANSITION_RULES)
        sm.reset(AgentState.ASSISTANT)
        assert sm.current_state == AgentState.ASSISTANT


class TestInvalidStateTransitionError:
    def test_default_message(self):
        err = InvalidStateTransitionError(AgentState.USER_INPUT, AgentState.RESPONSE)
        assert "user_input" in str(err)
        assert "response" in str(err)
        assert err.from_state == AgentState.USER_INPUT
        assert err.to_state == AgentState.RESPONSE

    def test_custom_message(self):
        err = InvalidStateTransitionError(AgentState.USER_INPUT, AgentState.RESPONSE, "custom msg")
        assert str(err) == "custom msg"
