"""Tests for the shell tool."""

from pathlib import Path

import pytest
from kosong.tooling import ToolError, ToolOk

from kimi_cli.tools.bash import Bash, Params


@pytest.fixture
def bash_tool() -> Bash:
    """Create a Shell tool instance."""
    return Bash()


@pytest.mark.asyncio
async def test_simple_command(bash_tool: Bash):
    """Test executing a simple command."""
    result = await bash_tool(Params(command="echo 'Hello World'"))

    assert isinstance(result, ToolOk)
    assert isinstance(result.output, str)
    assert "Hello World" in result.output
    assert "executed successfully" in result.message


@pytest.mark.asyncio
async def test_command_with_error(bash_tool: Bash):
    """Test executing a command that returns an error."""
    result = await bash_tool(Params(command="ls /nonexistent/directory"))

    assert isinstance(result, ToolError)
    assert "failed with exit code" in result.message


@pytest.mark.asyncio
async def test_command_chaining(bash_tool: Bash):
    """Test command chaining with &&."""
    result = await bash_tool(Params(command="echo 'First' && echo 'Second'"))

    assert isinstance(result, ToolOk)
    assert isinstance(result.output, str)
    assert "First" in result.output
    assert "Second" in result.output


@pytest.mark.asyncio
async def test_command_sequential(bash_tool: Bash):
    """Test sequential command execution with ;."""
    result = await bash_tool(Params(command="echo 'One'; echo 'Two'"))

    assert isinstance(result, ToolOk)
    assert isinstance(result.output, str)
    assert "One" in result.output
    assert "Two" in result.output


@pytest.mark.asyncio
async def test_command_conditional(bash_tool: Bash):
    """Test conditional command execution with ||."""
    result = await bash_tool(Params(command="false || echo 'Success'"))

    assert isinstance(result, ToolOk)
    assert isinstance(result.output, str)
    assert "Success" in result.output


@pytest.mark.asyncio
async def test_command_pipe(bash_tool: Bash):
    """Test command piping."""
    result = await bash_tool(Params(command="echo 'Hello World' | wc -w"))

    assert isinstance(result, ToolOk)
    assert isinstance(result.output, str)
    # Should count 2 words: "Hello" and "World"
    assert "2" in result.output


@pytest.mark.asyncio
async def test_command_with_timeout(bash_tool: Bash):
    """Test command execution with timeout."""
    result = await bash_tool(Params(command="sleep 0.1", timeout=1))

    assert isinstance(result, ToolOk)
    assert result.output == ""
    assert "executed successfully" in result.message


@pytest.mark.asyncio
async def test_command_timeout_expires(bash_tool: Bash):
    """Test command that times out."""
    result = await bash_tool(Params(command="sleep 2", timeout=1))

    assert isinstance(result, ToolError)
    assert "Killed by timeout" in result.brief
    assert "killed by timeout (1s)" in result.message


@pytest.mark.asyncio
async def test_environment_variables(bash_tool: Bash):
    """Test setting and using environment variables."""
    result = await bash_tool(Params(command="export TEST_VAR='test_value' && echo $TEST_VAR"))

    assert isinstance(result, ToolOk)
    assert isinstance(result.output, str)
    assert "test_value" in result.output


@pytest.mark.asyncio
async def test_file_operations(bash_tool: Bash, temp_work_dir: Path):
    """Test basic file operations."""
    # Create a test file
    result = await bash_tool(Params(command=f"echo 'Test content' > {temp_work_dir}/test_file.txt"))
    assert isinstance(result, ToolOk)

    # Read the file
    result = await bash_tool(Params(command=f"cat {temp_work_dir}/test_file.txt"))
    assert isinstance(result, ToolOk)
    assert isinstance(result.output, str)
    assert "Test content" in result.output


@pytest.mark.asyncio
async def test_text_processing(bash_tool: Bash):
    """Test text processing commands."""
    result = await bash_tool(Params(command="echo 'apple banana cherry' | sed 's/banana/orange/'"))

    assert isinstance(result, ToolOk)
    assert isinstance(result.output, str)
    assert "apple orange cherry" in result.output


@pytest.mark.asyncio
async def test_multiple_pipes(bash_tool: Bash):
    """Test multiple pipes in one command."""
    result = await bash_tool(Params(command="echo '1\n2\n3' | grep '2' | wc -l"))

    assert isinstance(result, ToolOk)
    assert isinstance(result.output, str)
    assert "1" in result.output  # Should find exactly one line with '2'


@pytest.mark.asyncio
async def test_command_substitution(bash_tool: Bash):
    """Test command substitution with a portable command."""
    result = await bash_tool(Params(command='echo "Result: $(echo hello)"'))

    assert isinstance(result, ToolOk)
    assert isinstance(result.output, str)
    assert "Result: hello" in result.output


@pytest.mark.asyncio
async def test_arithmetic_substitution(bash_tool: Bash):
    """Test arithmetic substitution - more portable than date command."""
    result = await bash_tool(Params(command='echo "Answer: $((2 + 2))"'))

    assert isinstance(result, ToolOk)
    assert isinstance(result.output, str)
    assert "Answer: 4" in result.output


@pytest.mark.asyncio
async def test_very_long_output(bash_tool: Bash):
    """Test command that produces very long output."""
    result = await bash_tool(Params(command="seq 1 100 | head -50"))

    assert isinstance(result, ToolOk)
    assert isinstance(result.output, str)
    assert "1" in result.output
    assert "50" in result.output
    assert "100" not in result.output  # Should not contain 100
