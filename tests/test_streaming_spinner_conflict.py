"""Test for streaming and spinner conflict resolution."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tunacode.core.state import StateManager
from tunacode.ui.panels import StreamingAgentPanel


@pytest.mark.asyncio
async def test_streaming_prevents_spinner_operations():
    """Test that spinner operations are skipped when streaming is active."""
    state_manager = StateManager()

    # Mock spinner
    mock_spinner = MagicMock()
    mock_spinner.start = MagicMock()
    mock_spinner.stop = MagicMock()
    state_manager.session.spinner = mock_spinner

    # Enable streaming
    state_manager.session.user_config = {"settings": {"enable_streaming": True}}

    # Test when streaming is active
    state_manager.session.is_streaming_active = True

    # Import after setting up mocks
    from tunacode.cli.repl import _tool_confirm
    from tunacode.core.tool_handler import ToolHandler
    from tunacode.types import ToolConfirmationResponse

    # Mock tool call
    mock_tool_call = MagicMock()
    mock_tool_call.tool_name = "write_file"
    mock_tool_call.args = '{"file_path": "test.txt", "content": "test"}'

    # Mock tool handler to say confirmation is needed
    with patch.object(ToolHandler, "should_confirm", return_value=True):
        with patch.object(ToolHandler, "create_confirmation_request"):
            with patch("tunacode.cli.repl._tool_ui") as mock_tool_ui:
                # Return proper ToolConfirmationResponse object
                mock_response = ToolConfirmationResponse(
                    approved=True, skip_future=False, abort=False
                )
                mock_tool_ui.show_confirmation = AsyncMock(return_value=mock_response)

                # Call tool confirm
                await _tool_confirm(mock_tool_call, None, state_manager)

                # Verify spinner was NOT manipulated when streaming is active
                mock_spinner.stop.assert_not_called()
                mock_spinner.start.assert_not_called()


@pytest.mark.asyncio
async def test_spinner_works_when_not_streaming():
    """Test that spinner operations work normally when streaming is inactive."""
    state_manager = StateManager()

    # Mock spinner
    mock_spinner = MagicMock()
    mock_spinner.start = MagicMock()
    mock_spinner.stop = MagicMock()
    state_manager.session.spinner = mock_spinner

    # Disable streaming
    state_manager.session.is_streaming_active = False

    # Import after setting up mocks
    from tunacode.cli.repl import _tool_confirm
    from tunacode.core.tool_handler import ToolHandler
    from tunacode.types import ToolConfirmationResponse

    # Mock tool call
    mock_tool_call = MagicMock()
    mock_tool_call.tool_name = "write_file"
    mock_tool_call.args = '{"file_path": "test.txt", "content": "test"}'

    # Mock tool handler
    with patch.object(ToolHandler, "should_confirm", return_value=True):
        with patch.object(ToolHandler, "create_confirmation_request"):
            with patch("tunacode.cli.repl._tool_ui") as mock_tool_ui:
                # Return proper ToolConfirmationResponse object
                mock_response = ToolConfirmationResponse(
                    approved=True, skip_future=False, abort=False
                )
                mock_tool_ui.show_confirmation = AsyncMock(return_value=mock_response)

                # Call tool confirm
                await _tool_confirm(mock_tool_call, None, state_manager)

                # Verify spinner WAS manipulated when streaming is inactive
                mock_spinner.stop.assert_called_once()
                mock_spinner.start.assert_called_once()


@pytest.mark.asyncio
async def test_streaming_panel_lifecycle():
    """Test that streaming panel properly manages its lifecycle."""
    panel = StreamingAgentPanel()

    # Mock console to avoid actual display
    with patch("tunacode.ui.panels.Live") as mock_live_class:
        mock_live = MagicMock()
        mock_live_class.return_value = mock_live

        # Start panel
        await panel.start()
        assert panel.live is not None
        mock_live.start.assert_called_once()

        # Update content
        await panel.update("Test content")
        assert panel.content == "Test content"
        mock_live.update.assert_called()

        # Stop panel
        await panel.stop()
        assert panel.live is None
        mock_live.stop.assert_called_once()


if __name__ == "__main__":
    asyncio.run(test_streaming_prevents_spinner_operations())
    asyncio.run(test_spinner_works_when_not_streaming())
    asyncio.run(test_streaming_panel_lifecycle())
    print("All tests passed!")
