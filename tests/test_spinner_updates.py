"""
Integration test for dynamic spinner message updates.
"""

from unittest.mock import MagicMock, patch

import pytest

from tunacode.ui import console as ui
from tunacode.ui.tool_descriptions import get_batch_description, get_tool_description


@pytest.mark.asyncio
async def test_spinner_with_custom_message():
    """Test that spinner can be created with custom message."""
    mock_state_manager = MagicMock()
    mock_state_manager.session.spinner = None

    with patch("tunacode.ui.output.console") as mock_console:
        mock_status = MagicMock()
        mock_console.status.return_value = mock_status

        # Test starting spinner with custom message
        custom_msg = "Executing tool: read_file"
        await ui.spinner(show=True, state_manager=mock_state_manager, message=custom_msg)

        # Verify spinner was created with custom message
        mock_console.status.assert_called_once()
        call_args = mock_console.status.call_args
        assert custom_msg in str(call_args)


@pytest.mark.asyncio
async def test_update_spinner_message():
    """Test updating an existing spinner's message."""
    mock_state_manager = MagicMock()
    mock_spinner = MagicMock()
    mock_state_manager.session.spinner = mock_spinner

    # Test updating message
    new_message = "Reading file: /path/to/file.py"
    await ui.update_spinner_message(new_message, mock_state_manager)

    # Verify update was called
    mock_spinner.update.assert_called_once_with(new_message)


@pytest.mark.asyncio
async def test_tool_descriptions():
    """Test tool description generation."""
    # Test read_file with path
    desc = get_tool_description("read_file", {"file_path": "/test/file.py"})
    assert desc == "Reading file: /test/file.py"

    # Test grep with pattern
    desc = get_tool_description("grep", {"pattern": "test_pattern"})
    assert desc == "Searching files for: test_pattern"

    # Test long pattern truncation
    long_pattern = "a" * 50
    desc = get_tool_description("grep", {"pattern": long_pattern})
    assert desc == f"Searching files for: {'a' * 27}..."

    # Test unknown tool
    desc = get_tool_description("unknown_tool", {})
    assert desc == "Executing unknown_tool"


@pytest.mark.asyncio
async def test_batch_descriptions():
    """Test batch execution descriptions."""
    # Test single tool
    desc = get_batch_description(1)
    assert desc == "Executing 1 tool"

    # Test multiple same tools
    desc = get_batch_description(5, ["read_file"] * 5)
    assert desc == "Reading 5 files in parallel"

    # Test mixed tools
    desc = get_batch_description(3, ["read_file", "grep", "list_dir"])
    assert desc == "Executing 3 tools in parallel"


@pytest.mark.asyncio
async def test_spinner_performance():
    """Test that spinner updates don't significantly impact performance."""
    import time

    mock_state_manager = MagicMock()
    mock_spinner = MagicMock()
    mock_state_manager.session.spinner = mock_spinner

    # Measure time for 100 updates
    start_time = time.time()

    for i in range(100):
        await ui.update_spinner_message(f"Update {i}", mock_state_manager)

    elapsed = time.time() - start_time

    # Should complete in less than 100ms (1ms per update)
    assert elapsed < 0.1, f"Spinner updates took {elapsed}s, should be < 0.1s"

    # Verify all updates were called
    assert mock_spinner.update.call_count == 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
