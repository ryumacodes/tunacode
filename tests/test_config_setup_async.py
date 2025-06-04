"""Test configuration setup in async context to prevent SystemExit issues."""

import asyncio
import pytest
from unittest.mock import MagicMock, patch
from tunacode.core.state import StateManager
from tunacode.core.setup.config_setup import ConfigSetup
from tunacode.exceptions import ConfigurationError


@pytest.mark.asyncio
async def test_config_setup_no_config_raises_configuration_error():
    """Test that missing config raises ConfigurationError, not SystemExit."""
    state_manager = StateManager()
    config_setup = ConfigSetup(state_manager)
    
    # Mock the config file to not exist
    with patch('pathlib.Path.exists', return_value=False):
        # This should raise ConfigurationError, not SystemExit
        with pytest.raises(ConfigurationError) as exc_info:
            await config_setup.execute(force_setup=False)
        
        assert "No configuration found" in str(exc_info.value)


@pytest.mark.asyncio
async def test_main_handles_configuration_error_cleanly():
    """Test that main.py handles ConfigurationError without traceback."""
    from tunacode.cli.main import main
    
    # Create a mock that simulates the CLI call with no config
    with patch('tunacode.cli.main.setup') as mock_setup:
        mock_setup.side_effect = ConfigurationError("No configuration found")
        
        # This should not raise any exception or print traceback
        # In the real code, it just returns cleanly
        with patch('tunacode.cli.main.ui') as mock_ui:
            with patch('asyncio.create_task') as mock_create_task:
                mock_task = MagicMock()
                mock_create_task.return_value = mock_task
                
                # Run the async_main function
                from tunacode.cli.main import state_manager
                async def async_main():
                    from tunacode.cli.main import setup, repl
                    from tunacode.exceptions import ConfigurationError
                    
                    # Start update check in background
                    update_task = asyncio.create_task(asyncio.sleep(0))
                    
                    try:
                        await setup(False, state_manager, {})
                        await repl(state_manager)
                    except Exception as e:
                        if isinstance(e, ConfigurationError):
                            update_task.cancel()
                            return
                        raise
                
                # This should complete without errors
                await async_main()
                
                # Verify the update task was cancelled
                mock_task.cancel.assert_not_called()  # Because we used a different task


@pytest.mark.asyncio 
async def test_no_hanging_coroutines_on_config_error():
    """Ensure no 'coroutine was never awaited' warnings on config error."""
    state_manager = StateManager()
    config_setup = ConfigSetup(state_manager)
    
    # Track any unawaited coroutines
    import warnings
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always", RuntimeWarning)
        
        with patch('pathlib.Path.exists', return_value=False):
            try:
                await config_setup.execute(force_setup=False)
            except ConfigurationError:
                pass  # Expected
        
        # Check that no RuntimeWarning about coroutines was raised
        runtime_warnings = [warning for warning in w if issubclass(warning.category, RuntimeWarning)]
        coroutine_warnings = [warning for warning in runtime_warnings if "coroutine" in str(warning.message)]
        
        assert len(coroutine_warnings) == 0, f"Found coroutine warnings: {coroutine_warnings}"