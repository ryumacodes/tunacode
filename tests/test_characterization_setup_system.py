import pytest
import importlib.util
import importlib
import sys
import types
from pathlib import Path
from tunacode.core.state import StateManager

# Avoid heavy imports from setup package
sys.modules['tunacode.cli.main'] = types.SimpleNamespace(app=None)
@pytest.fixture(autouse=True)
def cleanup_modules():
    """Automatically restore sys.modules after each test."""
    original = sys.modules.get('tunacode.ui.console')
    yield
    if original is not None:
        sys.modules['tunacode.ui.console'] = original
    else:
        sys.modules.pop('tunacode.ui.console', None)

sys.modules['tunacode.ui.console'] = types.SimpleNamespace()

if 'prompt_toolkit.styles' not in sys.modules:
    pytest.skip("prompt_toolkit not available", allow_module_level=True)

spec = importlib.util.spec_from_file_location(
    "setup_coordinator",
    str(Path("src/tunacode/core/setup/coordinator.py")),
)
coordinator_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(coordinator_module)
SetupCoordinator = coordinator_module.SetupCoordinator
BaseSetup = importlib.import_module("tunacode.core.setup.base").BaseSetup

if 'prompt_toolkit.styles' not in sys.modules:
    pytest.skip("prompt_toolkit not available", allow_module_level=True)

class DummyStep(BaseSetup):
    def __init__(self, state_manager, name):
        super().__init__(state_manager)
        self._name = name
        self.executed = False
        self.validated = False

    @property
    def name(self):
        return self._name

    async def should_run(self, force_setup: bool = False) -> bool:
        return True

    async def execute(self, force_setup: bool = False) -> None:
        self.executed = True

    async def validate(self) -> bool:
        self.validated = True
        return True

@pytest.mark.asyncio
async def test_setup_coordinator_runs_steps():
    state = StateManager()
    coord = SetupCoordinator(state)
    step1 = DummyStep(state, 's1')
    step2 = DummyStep(state, 's2')
    coord.register_step(step1)
    coord.register_step(step2)
    await coord.run_setup()
    assert step1.executed and step1.validated
    assert step2.executed and step2.validated
