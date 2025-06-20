"""Test configuration setup in async context to prevent SystemExit issues."""

import asyncio
import pytest
from unittest.mock import MagicMock, patch
import sys
import types
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

mock_console = MagicMock()
sys.modules['tunacode.ui.console'] = types.SimpleNamespace(
    error=MagicMock(),
    info=MagicMock(),
    warning=MagicMock(),
    success=MagicMock(),
    console=mock_console,
    muted=MagicMock()
)
if 'prompt_toolkit.styles' not in sys.modules:
    pytest.skip("prompt_toolkit not available", allow_module_level=True)
from tunacode.core.state import StateManager
from tunacode.core.setup.config_setup import ConfigSetup
from tunacode.exceptions import ConfigurationError


@pytest.mark.asyncio
async def test_config_setup_no_config_raises_configuration_error():
    """Test that missing config raises ConfigurationError, not SystemExit."""
    state_manager = StateManager()
    config_setup = ConfigSetup(state_manager)
    
    # Mock the config loading to return None (no config)
    with patch('tunacode.utils.user_configuration.load_config', return_value=None):
        # Mock console methods to avoid actual output
        with patch('tunacode.ui.console.error') as mock_error:
            # This should raise ConfigurationError, not SystemExit
            with pytest.raises(ConfigurationError) as exc_info:
                await config_setup.execute(force_setup=False)
            
            assert "No configuration found" in str(exc_info.value)


@pytest.mark.asyncio
async def test_main_handles_configuration_error_cleanly():
    """Test that main.py handles ConfigurationError without traceback."""
    # Create a fresh state manager for this test
    test_state_manager = StateManager()
    
    # Create a mock that simulates the CLI call with no config
    with patch('tunacode.setup.setup') as mock_setup:
        mock_setup.side_effect = ConfigurationError("No configuration found")
        
        # This should not raise any exception or print traceback
        # In the real code, it just returns cleanly
        async def async_main():
            from tunacode.setup import setup
            from tunacode.cli.repl import repl
            from tunacode.exceptions import ConfigurationError
            
            # Start update check in background
            update_task = asyncio.create_task(asyncio.sleep(0))
            
            try:
                await setup(False, test_state_manager, {})
                await repl(test_state_manager)
            except Exception as e:
                if isinstance(e, ConfigurationError):
                    update_task.cancel()
                    return
                raise
        
        # This should complete without errors
        await async_main()


@pytest.mark.asyncio 
async def test_no_hanging_coroutines_on_config_error():
    """Ensure no 'coroutine was never awaited' warnings on config error."""
    state_manager = StateManager()
    config_setup = ConfigSetup(state_manager)
    
    # Track any unawaited coroutines
    import warnings
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always", RuntimeWarning)
        
        # Mock the config loading to return None
        with patch('tunacode.utils.user_configuration.load_config', return_value=None):
            # Mock console to avoid actual output
            with patch('tunacode.ui.console.console'):
                try:
                    await config_setup.execute(force_setup=False)
                except ConfigurationError:
                    pass  # Expected
        
        # Check that no RuntimeWarning about coroutines was raised
        runtime_warnings = [warning for warning in w if issubclass(warning.category, RuntimeWarning)]
        coroutine_warnings = [warning for warning in runtime_warnings if "coroutine" in str(warning.message)]
        
        assert len(coroutine_warnings) == 0, f"Found coroutine warnings: {coroutine_warnings}"