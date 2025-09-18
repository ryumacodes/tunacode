"""Tests for the shell tool."""

from pathlib import Path

import pytest
from kosong.tooling import ToolError, ToolOk

from kimi_cli.tools.shell import Shell


@pytest.fixture
def shell_tool() -> Shell:
    """Create a Shell tool instance."""
    return Shell()


@pytest.mark.asyncio
async def test_simple_command(shell_tool: Shell):
    """Test executing a simple command."""
    result = await shell_tool("echo 'Hello World'")

    assert isinstance(result, ToolOk)
    assert isinstance(result.value, str)
    assert "Hello World" in result.value
    assert "(Exit code: 0)" in result.value


@pytest.mark.asyncio
async def test_command_with_error(shell_tool: Shell):
    """Test executing a command that returns an error."""
    result = await shell_tool("ls /nonexistent/directory")

    assert isinstance(result, ToolError)
    assert "Failed with exit code" in result.brief
    assert "(Exit code:" in result.message


@pytest.mark.asyncio
async def test_command_chaining(shell_tool: Shell):
    """Test command chaining with &&."""
    result = await shell_tool("echo 'First' && echo 'Second'")

    assert isinstance(result, ToolOk)
    assert isinstance(result.value, str)
    assert "First" in result.value
    assert "Second" in result.value


@pytest.mark.asyncio
async def test_command_sequential(shell_tool: Shell):
    """Test sequential command execution with ;."""
    result = await shell_tool("echo 'One'; echo 'Two'")

    assert isinstance(result, ToolOk)
    assert isinstance(result.value, str)
    assert "One" in result.value
    assert "Two" in result.value


@pytest.mark.asyncio
async def test_command_conditional(shell_tool: Shell):
    """Test conditional command execution with ||."""
    result = await shell_tool("false || echo 'Success'")

    assert isinstance(result, ToolOk)
    assert isinstance(result.value, str)
    assert "Success" in result.value


@pytest.mark.asyncio
async def test_command_pipe(shell_tool: Shell):
    """Test command piping."""
    result = await shell_tool("echo 'Hello World' | wc -w")

    assert isinstance(result, ToolOk)
    assert isinstance(result.value, str)
    # Should count 2 words: "Hello" and "World"
    assert "2" in result.value


@pytest.mark.asyncio
async def test_command_with_timeout(shell_tool: Shell):
    """Test command execution with timeout."""
    result = await shell_tool("sleep 0.1", timeout=1)

    assert isinstance(result, ToolOk)
    assert isinstance(result.value, str)
    assert "(Exit code: 0)" in result.value


@pytest.mark.asyncio
async def test_command_timeout_expires(shell_tool: Shell):
    """Test command that times out."""
    result = await shell_tool("sleep 2", timeout=1)

    assert isinstance(result, ToolError)
    assert "Killed by timeout" in result.brief
    assert "Killed by timeout (1s)" in result.message


@pytest.mark.asyncio
async def test_environment_variables(shell_tool: Shell):
    """Test setting and using environment variables."""
    result = await shell_tool("export TEST_VAR='test_value' && echo $TEST_VAR")

    assert isinstance(result, ToolOk)
    assert isinstance(result.value, str)
    assert "test_value" in result.value


@pytest.mark.asyncio
async def test_file_operations(shell_tool: Shell, temp_work_dir: Path):
    """Test basic file operations."""
    # Create a test file
    result = await shell_tool(f"echo 'Test content' > {temp_work_dir}/test_file.txt")
    assert isinstance(result, ToolOk)

    # Read the file
    result = await shell_tool(f"cat {temp_work_dir}/test_file.txt")
    assert isinstance(result, ToolOk)
    assert isinstance(result.value, str)
    assert "Test content" in result.value


@pytest.mark.asyncio
async def test_text_processing(shell_tool: Shell):
    """Test text processing commands."""
    result = await shell_tool("echo 'apple banana cherry' | sed 's/banana/orange/'")

    assert isinstance(result, ToolOk)
    assert isinstance(result.value, str)
    assert "apple orange cherry" in result.value


@pytest.mark.asyncio
async def test_multiple_pipes(shell_tool: Shell):
    """Test multiple pipes in one command."""
    result = await shell_tool("echo '1\n2\n3' | grep '2' | wc -l")

    assert isinstance(result, ToolOk)
    assert isinstance(result.value, str)
    assert "1" in result.value  # Should find exactly one line with '2'


@pytest.mark.asyncio
async def test_command_substitution(shell_tool: Shell):
    """Test command substitution with a portable command."""
    result = await shell_tool('echo "Result: $(echo hello)"')

    assert isinstance(result, ToolOk)
    assert isinstance(result.value, str)
    assert "Result: hello" in result.value


@pytest.mark.asyncio
async def test_arithmetic_substitution(shell_tool: Shell):
    """Test arithmetic substitution - more portable than date command."""
    result = await shell_tool('echo "Answer: $((2 + 2))"')

    assert isinstance(result, ToolOk)
    assert isinstance(result.value, str)
    assert "Answer: 4" in result.value


@pytest.mark.asyncio
async def test_very_long_output(shell_tool: Shell):
    """Test command that produces very long output."""
    result = await shell_tool("seq 1 100 | head -50")

    assert isinstance(result, ToolOk)
    assert isinstance(result.value, str)
    assert "1" in result.value
    assert "50" in result.value
    assert "100" not in result.value  # Should not contain 100
