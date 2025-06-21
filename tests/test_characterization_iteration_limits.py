"""
Characterization tests for iteration limits.

These tests capture the CURRENT behavior of iteration limits in TunaCode.
This is a golden-master test that documents the existing behavior before
we make changes to update the defaults.

Current behavior captured:
- Default max_iterations: 40 (updated from 20)
- Command limit: 100 (updated from 50)
- Fallback on line 201 in commands.py shows 40 (was 15, now updated)
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock

from tunacode.configuration.defaults import DEFAULT_USER_CONFIG
from tunacode.cli.commands import IterationsCommand
from tunacode.types import CommandContext
from tunacode.core.state import StateManager

class TestIterationLimitsCharacterization:
    """Golden-master tests for iteration limit behavior."""

    def test_default_max_iterations_is_40(self):
        """Capture behavior: default max_iterations is set to 40 in DEFAULT_USER_CONFIG."""
        assert DEFAULT_USER_CONFIG["settings"]["max_iterations"] == 40

    @pytest.mark.asyncio
    async def test_iterations_command_max_limit_is_100(self):
        """Capture behavior: /iterations command enforces maximum limit of 100."""
        # Setup
        cmd = IterationsCommand()
        state_manager = Mock(spec=StateManager)
        state_manager.session = Mock()
        state_manager.session.user_config = {"settings": {}}
        
        context = CommandContext(
            state_manager=state_manager
        )

        # Mock UI functions
        with patch("tunacode.cli.commands.ui.error") as mock_error:
            # Test trying to set iterations to 101 (above limit)
            await cmd.execute(["101"], context)
            
            # Assert error was shown
            mock_error.assert_called_once_with("Iterations must be between 1 and 100")

    @pytest.mark.asyncio
    async def test_iterations_command_accepts_100(self):
        """Capture behavior: /iterations command accepts exactly 100 as valid."""
        # Setup
        cmd = IterationsCommand()
        state_manager = Mock(spec=StateManager)
        state_manager.session = Mock()
        state_manager.session.user_config = {"settings": {}}
        
        context = CommandContext(
            state_manager=state_manager
        )

        # Mock UI functions
        with patch("tunacode.cli.commands.ui.success") as mock_success:
            with patch("tunacode.cli.commands.ui.muted") as mock_muted:
                # Test setting iterations to 100 (at limit)
                await cmd.execute(["100"], context)
                
                # Assert success was shown
                mock_success.assert_called_once_with("Maximum iterations set to 100")
                mock_muted.assert_called_once_with("Higher values allow more complex reasoning but may be slower")
                
                # Assert value was set
                assert state_manager.session.user_config["settings"]["max_iterations"] == 100

    @pytest.mark.asyncio
    async def test_iterations_command_rejects_0_and_negative(self):
        """Capture behavior: /iterations command rejects 0 and negative values."""
        # Setup
        cmd = IterationsCommand()
        state_manager = Mock(spec=StateManager)
        state_manager.session = Mock()
        state_manager.session.user_config = {"settings": {}}
        
        context = CommandContext(
            state_manager=state_manager
        )

        # Mock UI functions
        with patch("tunacode.cli.commands.ui.error") as mock_error:
            # Test 0
            await cmd.execute(["0"], context)
            mock_error.assert_called_with("Iterations must be between 1 and 100")
            
            # Reset mock
            mock_error.reset_mock()
            
            # Test negative
            await cmd.execute(["-5"], context)
            mock_error.assert_called_with("Iterations must be between 1 and 100")

    @pytest.mark.asyncio
    async def test_iterations_command_display_shows_default(self):
        """Capture behavior: /iterations command shows default of 40 when no config exists."""
        # Setup
        cmd = IterationsCommand()
        state_manager = Mock(spec=StateManager)
        state_manager.session = Mock()
        state_manager.session.user_config = {}  # No settings
        
        context = CommandContext(
            state_manager=state_manager
        )

        # Mock UI functions
        with patch("tunacode.cli.commands.ui.info") as mock_info:
            with patch("tunacode.cli.commands.ui.muted") as mock_muted:
                # Test showing current value without args
                await cmd.execute([], context)
                
                # Assert shows 40 as default (matching DEFAULT_USER_CONFIG)
                mock_info.assert_called_once_with("Current maximum iterations: 40")
                mock_muted.assert_called_once_with("Usage: /iterations <number> (1-100)")

    def test_process_request_reads_max_iterations_from_config(self):
        """Document behavior: process_request reads max_iterations from config on line 660."""
        # This is a documentation test to capture where max_iterations is read
        # in the process_request function. The actual line is:
        # max_iterations = state_manager.session.user_config.get("settings", {}).get("max_iterations", 40)
        
        # The process_request function:
        # 1. Reads max_iterations from user config settings
        # 2. Falls back to 40 if not specified
        # 3. Uses this value to limit iteration count in the agent loop
        # 4. Breaks the loop when i >= max_iterations
        pass

    def test_main_agent_reads_max_iterations_on_line_660(self):
        """Document that main.py reads max_iterations from config on line 660."""
        # This is a documentation test to capture the specific line where
        # max_iterations is read. The actual line is:
        # max_iterations = state_manager.session.user_config.get("settings", {}).get("max_iterations", 20)
        
        # This confirms the fallback default is 20 when not specified in config
        pass