"""Tests for tunacode.core.session.state."""

from unittest.mock import patch

import pytest

from tunacode.core.session.state import SessionState, StateManager


class TestSessionState:
    def test_default_values(self):
        state = SessionState()
        assert state.user_config == {}
        assert state.agents == {}
        assert state.agent_versions == {}
        assert state.debug_mode is False
        assert state.undo_initialized is False
        assert state.show_thoughts is False
        assert state.session_id
        assert state.current_recursion_depth == 0
        assert state.max_recursion_depth == 5
        assert state.parent_task_id is None
        assert state.task_hierarchy == {}
        assert state.iteration_budgets == {}
        assert state.recursive_context_stack == []

    def test_session_id_unique(self):
        s1 = SessionState()
        s2 = SessionState()
        assert s1.session_id != s2.session_id


class TestStateManager:
    @pytest.fixture
    def sm(self):
        with patch("tunacode.configuration.user_config.load_config_with_defaults") as mock_load:
            mock_load.return_value = {
                "default_model": "openai:gpt-4",
                "env": {},
                "settings": {},
            }
            with patch("tunacode.configuration.models.get_model_context_window", return_value=8192):
                return StateManager()

    def test_session_property(self, sm):
        assert isinstance(sm.session, SessionState)

    def test_conversation_property(self, sm):
        assert sm.conversation is sm.session.conversation

    def test_task_property(self, sm):
        assert sm.task is sm.session.task

    def test_runtime_property(self, sm):
        assert sm.runtime is sm.session.runtime

    def test_usage_property(self, sm):
        assert sm.usage is sm.session.usage

    def test_push_recursive_context(self, sm):
        ctx = {"task_id": "t1", "depth": 1}
        sm.push_recursive_context(ctx)
        assert sm.session.current_recursion_depth == 1
        assert len(sm.session.recursive_context_stack) == 1

    def test_pop_recursive_context(self, sm):
        sm.push_recursive_context({"task_id": "t1"})
        result = sm.pop_recursive_context()
        assert result == {"task_id": "t1"}
        assert sm.session.current_recursion_depth == 0

    def test_pop_empty_stack_returns_none(self, sm):
        assert sm.pop_recursive_context() is None

    def test_set_and_get_task_iteration_budget(self, sm):
        sm.set_task_iteration_budget("t1", 20)
        assert sm.get_task_iteration_budget("t1") == 20

    def test_get_default_budget(self, sm):
        assert sm.get_task_iteration_budget("unknown") == 10

    def test_can_recurse_deeper(self, sm):
        assert sm.can_recurse_deeper() is True
        sm.session.current_recursion_depth = 5
        assert sm.can_recurse_deeper() is False

    def test_reset_recursive_state(self, sm):
        sm.push_recursive_context({"task_id": "t1"})
        sm.set_task_iteration_budget("t1", 20)
        sm.session.parent_task_id = "parent"
        sm.session.task_hierarchy["t1"] = "parent"

        sm.reset_recursive_state()
        assert sm.session.current_recursion_depth == 0
        assert sm.session.parent_task_id is None
        assert sm.session.task_hierarchy == {}
        assert sm.session.iteration_budgets == {}
        assert sm.session.recursive_context_stack == []

    def test_reset_session(self, sm):
        sm.session.debug_mode = True
        sm.reset_session()
        assert sm.session.debug_mode is False

    def test_split_thought_messages(self, sm):
        messages = [
            {"thought": "I think..."},
            {"kind": "request", "parts": []},
            {"thought": "Another thought"},
            {"content": "user message"},
        ]
        thoughts, cleaned = sm._split_thought_messages(messages)
        assert len(thoughts) == 2
        assert "I think..." in thoughts
        assert "Another thought" in thoughts
        assert len(cleaned) == 2

    def test_split_thought_none_value(self, sm):
        messages = [{"thought": None}]
        thoughts, cleaned = sm._split_thought_messages(messages)
        assert thoughts == []
        assert cleaned == []

    def test_coerce_str_value(self, sm):
        assert sm._coerce_str_value("hello", "default") == "hello"
        assert sm._coerce_str_value(None, "default") == "default"
        assert sm._coerce_str_value(123, "default") == "123"

    def test_loads_user_config(self):
        with patch(
            "tunacode.configuration.user_config.load_config_with_defaults",
        ) as mock_load, patch(
            "tunacode.configuration.models.get_model_context_window",
            return_value=200000,
        ):
            mock_load.return_value = {
                "default_model": "anthropic:claude-3",
                "env": {},
                "settings": {},
            }
            sm = StateManager()
            assert sm.session.current_model == "anthropic:claude-3"
            assert sm.session.conversation.max_tokens == 200000
