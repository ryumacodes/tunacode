import os
import time

import pytest

from tunacode.types import EscapeState
from tunacode.exceptions import EscapeInterrupt
from tunacode.core.state import StateManager
from tunacode.core.tool_handler import ToolHandler
from tunacode.tools.write_file import WriteFileTool, write_file
from tunacode.tools.update_file import UpdateFileTool, update_file
try:
    from tunacode.ui.keybindings import create_key_bindings
except ImportError:
    create_key_bindings = None


@pytest.fixture(autouse=True)
def freeze_time(monkeypatch):
    """Freeze time.time() to a mutable value for predictable testing."""
    t = [1000.0]
    monkeypatch.setattr(time, 'time', lambda: t[0])
    return t


def test_escape_state_initial_window_inactive():
    state = EscapeState()
    assert not state.is_window_active()
    assert state.last_escape_time is None


def test_escape_state_window_active_and_reset(freeze_time):
    state = EscapeState()
    # First press sets last_escape_time
    freeze_time[0] = 1000.0
    state.last_escape_time = freeze_time[0]
    # Within 1 second window it should be active
    freeze_time[0] = 1000.5
    assert state.is_window_active()
    # After window expires it should reset state
    freeze_time[0] = 2000.0
    assert not state.is_window_active()
    assert state.last_escape_time is None
    assert not state.escape_pending
    assert not state.message_shown


def test_escape_state_reset():
    state = EscapeState(last_escape_time=1.0, escape_pending=True, message_shown=True)
    state.reset_escape_state()
    assert state.last_escape_time is None
    assert not state.escape_pending
    assert not state.message_shown


def test_tool_handler_check_escape_noop():
    manager = StateManager()
    handler = ToolHandler(manager)
    handler.check_escape()


def test_tool_handler_check_escape_triggers(freeze_time):
    manager = StateManager()
    manager.escape_state.last_escape_time = freeze_time[0]
    manager.escape_state.escape_pending = True
    handler = ToolHandler(manager)
    with pytest.raises(EscapeInterrupt):
        handler.check_escape()
    assert manager.escape_state.last_escape_time is None
    assert not manager.escape_state.escape_pending


class _DummyBuffer:
    def __init__(self):
        self.text_inserted = ''

    def validate_and_handle(self):
        pass

    def insert_text(self, text):
        self.text_inserted += text


class _DummyOutput:
    def __init__(self):
        self.messages = []
    def write(self, txt):
        self.messages.append(txt)


class _DummyApp:
    pass


def _make_event(manager):
    app = _DummyApp()
    app.state_manager = manager
    app.output = _DummyOutput()
    return type('Evt', (), {'app': app, 'current_buffer': _DummyBuffer()})()


def test_double_escape_binding(freeze_time):
    if create_key_bindings is None:
        pytest.skip("prompt_toolkit not installed, skipping keybinding test")
    manager = StateManager()
    # Simulate a running task so ESC ESC hint is enabled
    manager.session.current_task = type('DummyTask', (), {'done': lambda self: False})()
    kb = create_key_bindings()
    esc_binding = next(b for b in kb.bindings if b.keys == ('escape',))
    event = _make_event(manager)
    # first ESC press
    freeze_time[0] = 1000.0
    esc_binding.handler(event)
    assert manager.escape_state.escape_pending
    assert event.app.output.messages == ['Press ESC again to stop\n']
    # second ESC press within window
    freeze_time[0] = 1000.5
    with pytest.raises(EscapeInterrupt):
        esc_binding.handler(event)

def test_escape_enter_binding(freeze_time):
    if create_key_bindings is None:
        pytest.skip("prompt_toolkit not installed, skipping keybinding test")
    manager = StateManager()
    kb = create_key_bindings()
    # Keys.ControlM is used for Enter key
    from prompt_toolkit.keys import Keys
    ee_binding = next(b for b in kb.bindings if b.keys == (Keys.Escape, Keys.ControlM))
    event = _make_event(manager)
    ee_binding.handler(event)
    buf = event.current_buffer
    assert buf.text_inserted == "\n"
    assert not manager.escape_state.escape_pending

def test_ctrl_c_not_overridden():
    if create_key_bindings is None:
        pytest.skip("prompt_toolkit not installed, skipping Ctrl+C compatibility test")
    kb = create_key_bindings()
    # Ensure no custom binding overrides Ctrl+C
    assert not any(binding.keys == ('c-c',) for binding in kb.bindings)


@pytest.mark.asyncio
async def test_write_file_tool_atomic(tmp_path):
    filepath = tmp_path / 'out.txt'
    content = 'Hello, Tuna!'
    tool = WriteFileTool(None)
    result = await tool._execute(str(filepath), content)
    assert filepath.read_text(encoding='utf-8') == content
    assert 'Successfully wrote to new file' in result
    assert not os.path.exists(str(filepath) + '.tuna_tmp')


@pytest.mark.asyncio
async def test_write_file_convenience(tmp_path):
    filepath = tmp_path / 'out2.txt'
    content = 'TunaCode!'
    result = await write_file(str(filepath), content)
    assert filepath.read_text(encoding='utf-8') == content
    assert 'Successfully wrote to new file' in result


@pytest.mark.asyncio
async def test_update_file_tool_atomic(tmp_path):
    filepath = tmp_path / 'in.txt'
    original = 'foo\nbar\nbaz\n'
    filepath.write_text(original, encoding='utf-8')
    tool = UpdateFileTool(None)
    result = await tool._execute(str(filepath), 'bar', 'qux')
    updated = filepath.read_text(encoding='utf-8')
    assert 'bar' not in updated and 'qux' in updated
    assert 'updated successfully' in result
    assert not os.path.exists(str(filepath) + '.tuna_tmp')


@pytest.mark.asyncio
async def test_update_file_convenience(tmp_path):
    filepath = tmp_path / 'in2.txt'
    original = 'alpha\nbeta\n'
    filepath.write_text(original, encoding='utf-8')
    result = await update_file(str(filepath), 'alpha', 'gamma')
    updated = filepath.read_text(encoding='utf-8')
    assert 'alpha' not in updated and 'gamma' in updated
    assert 'updated successfully' in result