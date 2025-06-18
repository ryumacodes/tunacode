"""
Integration Test: Error Recovery Flow

Tests how the system handles a tool error and whether the agent can recover or report it gracefully.

Scenario:
- Attempt to read a non-existent file (should fail).
- Write the file.
- Read the file again (should succeed).

Uses real tool logic and tmp_path for isolation.
"""

import pytest
import asyncio
from tunacode.tools import read_file, write_file

@pytest.mark.asyncio
async def test_error_recovery_flow(tmp_path):
    file_path = tmp_path / "recoverable.txt"

    # Current behavior: read_file returns error message as string when file doesn't exist
    read_result = await read_file.read_file(str(file_path))
    assert isinstance(read_result, str)
    assert "No such file" in read_result or "not found" in read_result.lower()

    # Current behavior: write_file returns success message as string
    write_result = await write_file.write_file(str(file_path), "Recovery content")
    assert isinstance(write_result, str)
    assert "successfully wrote" in write_result.lower()

    # Current behavior: read_file returns file content as string when successful
    read_result2 = await read_file.read_file(str(file_path))
    assert isinstance(read_result2, str)
    assert read_result2 == "Recovery content"

"""
Notes:
- This test uses real tool logic and tmp_path for isolation.
- The test checks for error reporting and recovery in a user-observable workflow.
"""