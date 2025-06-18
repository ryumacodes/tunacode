"""
Integration Test: Multi-Tool Operations

Simulates a scenario where the agent uses a sequence of tools in a multi-step operation:
- Write a file
- List directory
- Read file
- Update file
- Read file again

Uses real tool logic, mocks LLM at the agent boundary, and uses tmp_path for file operations.
"""

import pytest
import asyncio
from unittest.mock import patch, AsyncMock

from tunacode.core.state import StateManager
from tunacode.tools import write_file, list_dir, read_file, update_file

@pytest.mark.asyncio
async def test_multi_tool_operations(tmp_path, monkeypatch):
    # Setup: file path and initial content
    file_path = tmp_path / "testfile.txt"
    initial_content = "Hello, TunaCode!"
    updated_content = "Updated content."

    # Write file
    write_result = await write_file.write_file(str(file_path), initial_content)
    # Current behavior: write_file returns a string message, not a dict
    assert isinstance(write_result, str)
    assert "Successfully wrote to new file:" in write_result

    # List directory
    list_result = await list_dir.list_dir(str(tmp_path))
    # Current behavior: list_dir returns a formatted string, not a dict
    assert isinstance(list_result, str)
    assert "testfile.txt" in list_result

    # Read file
    read_result = await read_file.read_file(str(file_path))
    # Current behavior: read_file returns file content as string, not a dict
    assert isinstance(read_result, str)
    assert read_result == initial_content

    # Update file
    update_result = await update_file.update_file(str(file_path), initial_content, updated_content)
    # Current behavior: update_file requires target and patch, returns string
    assert isinstance(update_result, str)
    assert "updated successfully" in update_result

    # Read file again
    read_result2 = await read_file.read_file(str(file_path))
    assert isinstance(read_result2, str)
    assert read_result2 == updated_content

"""
Notes:
- This test uses real tool logic and tmp_path for isolation.
- No LLM or agent logic is invoked here; this test focuses on tool integration.
- For agent-driven multi-tool flows, see full session or orchestrator tests.
"""