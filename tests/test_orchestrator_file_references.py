"""Test @ file references work correctly in orchestrator mode."""

import os
import tempfile
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tunacode.cli.repl import process_request
from tunacode.core.state import StateManager


@pytest.mark.asyncio
async def test_orchestrator_expands_file_references():
    """Test that @ file references are expanded before being sent to orchestrator."""
    # Create a test file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("def example():\n    return 42")
        f.flush()
        
        try:
            # Create mock state manager
            state_manager = MagicMock(spec=StateManager)
            state_manager.session = MagicMock()
            state_manager.session.architect_mode = True  # Enable orchestrator mode
            state_manager.session.current_model = "test:model"
            state_manager.session.messages = []
            state_manager.session.spinner = None
            
            # Create mock UI functions
            with patch("tunacode.cli.repl.ui") as mock_ui:
                mock_ui.spinner = AsyncMock(return_value=None)
                mock_ui.error = AsyncMock()
                mock_ui.agent = AsyncMock()
                mock_ui.muted = AsyncMock()
                
                # Mock the orchestrator
                with patch("tunacode.cli.repl.OrchestratorAgent") as mock_orchestrator_class:
                    mock_orchestrator = AsyncMock()
                    mock_orchestrator_class.return_value = mock_orchestrator
                    
                    # Capture what text is passed to orchestrator.run()
                    captured_text = None
                    
                    async def capture_run(text, model):
                        nonlocal captured_text
                        captured_text = text
                        return []
                    
                    mock_orchestrator.run = capture_run
                    
                    # Process request with @ file reference
                    input_text = f"Please analyze @{f.name}"
                    await process_request(input_text, state_manager)
                    
                    # Verify the text was expanded before reaching orchestrator
                    assert captured_text is not None
                    assert "```python" in captured_text
                    assert "def example():" in captured_text
                    assert "return 42" in captured_text
                    
                    # Verify no error was shown
                    mock_ui.error.assert_not_called()
        finally:
            os.unlink(f.name)


@pytest.mark.asyncio
async def test_standard_mode_expands_file_references():
    """Test that @ file references are expanded in standard mode."""
    # Create a test file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False) as f:
        f.write("console.log('test');")
        f.flush()
        
        try:
            # Create mock state manager
            state_manager = MagicMock(spec=StateManager)
            state_manager.session = MagicMock()
            state_manager.session.architect_mode = False  # Disable orchestrator mode
            state_manager.session.current_model = "test:model"
            state_manager.session.messages = []
            state_manager.session.spinner = None
            state_manager.session.show_thoughts = False
            
            # Create mock UI functions
            with patch("tunacode.cli.repl.ui") as mock_ui:
                mock_ui.spinner = AsyncMock(return_value=None)
                mock_ui.error = AsyncMock()
                mock_ui.agent = AsyncMock()
                mock_ui.muted = AsyncMock()
                
                # Mock the agent
                with patch("tunacode.cli.repl.agent") as mock_agent:
                    # Capture what text is passed to process_request
                    captured_text = None
                    
                    async def capture_process_request(model, text, state, tool_callback):
                        nonlocal captured_text
                        captured_text = text
                        result = MagicMock()
                        result.result = MagicMock()
                        result.result.output = "Test output"
                        return result
                    
                    mock_agent.process_request = capture_process_request
                    
                    # Process request with @ file reference
                    input_text = f"Please analyze @{f.name}"
                    await process_request(input_text, state_manager)
                    
                    # Verify the text was expanded before reaching agent
                    assert captured_text is not None
                    assert "```javascript" in captured_text
                    assert "console.log('test');" in captured_text
                    
                    # Verify no error was shown
                    mock_ui.error.assert_not_called()
        finally:
            os.unlink(f.name)


@pytest.mark.asyncio
async def test_file_not_found_shows_error():
    """Test that non-existent file references show an error."""
    # Create mock state manager
    state_manager = MagicMock(spec=StateManager)
    state_manager.session = MagicMock()
    state_manager.session.architect_mode = True
    state_manager.session.current_model = "test:model"
    state_manager.session.messages = []
    state_manager.session.spinner = None
    
    # Create mock UI functions
    with patch("tunacode.cli.repl.ui") as mock_ui:
        mock_ui.spinner = AsyncMock(return_value=None)
        mock_ui.error = AsyncMock()
        
        # Process request with non-existent file
        input_text = "@/does/not/exist.py"
        await process_request(input_text, state_manager)
        
        # Verify error was shown
        mock_ui.error.assert_called_once()
        error_msg = mock_ui.error.call_args[0][0]
        assert "File not found" in error_msg