import types
import sys
import pytest
from tunacode.core.state import StateManager

# Avoid importing heavy CLI main module
sys.modules['tunacode.cli.main'] = types.SimpleNamespace(app=None)
class StubConsole(types.SimpleNamespace):
    async def success(self, *a, **k):
        pass
    async def info(self, *a, **k):
        pass
    async def muted(self, *a, **k):
        pass
    async def error(self, *a, **k):
        pass

sys.modules['tunacode.ui.console'] = StubConsole()
from tunacode.cli.commands import CommandRegistry, CommandContext

async def async_noop(*args, **kwargs):
    pass

class DummyUI(types.SimpleNamespace):
    async def success(self, *args, **kwargs):
        pass
    async def info(self, *args, **kwargs):
        pass
    async def muted(self, *args, **kwargs):
        pass
    async def error(self, *args, **kwargs):
        pass

def test_command_registry_partial_match(monkeypatch):
    monkeypatch.setattr('tunacode.cli.commands.ui', DummyUI())
    registry = CommandRegistry()
    registry.discover_commands()
    assert 'yolo' in registry.get_command_names()
    matches = registry.find_matching_commands('yo')
    assert 'yolo' in matches

@pytest.mark.asyncio
async def test_yolo_command_toggle(monkeypatch):
    monkeypatch.setattr('tunacode.cli.commands.ui', DummyUI())
    registry = CommandRegistry()
    registry.discover_commands()
    state_manager = StateManager()
    context = CommandContext(state_manager=state_manager, process_request=None)
    cmd = registry._commands['yolo']
    await cmd.execute([], context)
    assert state_manager.session.yolo is True
    await cmd.execute([], context)
    assert state_manager.session.yolo is False
