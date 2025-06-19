import types
from unittest.mock import patch
import pytest

from tunacode.core.state import StateManager
from tunacode.core.agents.main import patch_tool_messages


def make_part(kind, call_id, tool_name=None, content=None):
    return types.SimpleNamespace(part_kind=kind, tool_call_id=call_id, tool_name=tool_name, content=content)


def make_message(parts):
    return types.SimpleNamespace(parts=parts)


def test_patch_tool_messages_adds_synthetic_response():
    state = StateManager()
    call_part = make_part('tool-call', '123', 'read_file')
    state.session.messages.append(make_message([call_part]))

    class DummyReturn:
        def __init__(self, tool_name, content, tool_call_id, timestamp=None, part_kind='tool-return'):
            self.tool_name = tool_name
            self.content = content
            self.tool_call_id = tool_call_id
            self.part_kind = part_kind

    class DummyRequest:
        def __init__(self, parts=None, kind=None):
            self.parts = parts or []
            self.kind = kind

    with patch('tunacode.core.agents.main.get_model_messages', return_value=(DummyRequest, DummyReturn)):
        patch_tool_messages('error', state)

    assert len(state.session.messages) == 2
    added = state.session.messages[-1]
    assert isinstance(added, DummyRequest)
    assert added.parts[0].content == 'error'


def test_state_manager_reset_session():
    state = StateManager()
    state.session.yolo = True
    state.session.messages.append('msg')
    state.session.files_in_context.add('file.txt')

    state.reset_session()
    assert state.session.messages == []
    assert state.session.files_in_context == set()
    assert state.session.yolo is False
