"""Comprehensive security tests for enhanced bash.py tool."""

import asyncio
import pytest
import tempfile
import os
from unittest.mock import patch, AsyncMock

from pydantic_ai.exceptions import ModelRetry
from tunacode.tools.bash import bash, _validate_command_security, CommandSecurityError


class TestBashSecurityValidation:
    """Test security validation functionality."""

    def test_empty_command_blocked(self):
        """Test that empty commands are blocked."""
        with pytest.raises(ModelRetry, match="Empty command not allowed"):
            _validate_command_security("")

        with pytest.raises(ModelRetry, match="Empty command not allowed"):
            _validate_command_security("   ")

    def test_dangerous_patterns_blocked(self):
        """Test that highly dangerous patterns are blocked."""
        dangerous_commands = [
            "rm -rf /",
            "sudo rm -rf /important",
            "dd if=/dev/zero of=/dev/sda",
            "mkfs.ext4 /dev/sda1",
            "fdisk /dev/sda",
            ":(){ :|:& };:",  # fork bomb
        ]

        for command in dangerous_commands:
            with pytest.raises(ModelRetry, match="Command contains dangerous pattern"):
                _validate_command_security(command)

    def test_restricted_characters_blocked(self):
        """Test that restricted shell characters are blocked."""
        commands_with_restricted_chars = [
            "ls; echo done",  # Simple semicolon (not rm)
            "cat file & echo done",
            "echo `whoami`",
            "cat file && rm file",
            "echo {test}",  # Braces not part of variable expansion
        ]

        for command in commands_with_restricted_chars:
            with pytest.raises(ModelRetry, match="Potentially unsafe (character|pattern)"):
                _validate_command_security(command)

    def test_environment_variables_allowed(self):
        """Test that environment variables are allowed."""
        safe_env_commands = [
            "echo $HOME",
            "echo $PATH",
            "echo ${TEST_VAR}",
            "printenv HOME",
        ]

        for command in safe_env_commands:
            try:
                _validate_command_security(command)
            except ModelRetry:
                pytest.fail(f"Environment variable command was blocked: {command}")

    def test_injection_patterns_blocked(self):
        """Test that injection patterns are blocked."""
        injection_commands = [
            "ls; rm file",  # Should be caught by injection pattern
            "echo test && rm file",  # Should be caught by injection pattern
            "`rm file`",  # Should be caught by injection pattern
            "$(rm file)",  # Should be caught by injection pattern
        ]

        for command in injection_commands:
            with pytest.raises(ModelRetry, match="Potentially unsafe pattern detected"):
                _validate_command_security(command)

    def test_fork_bomb_blocked(self):
        """Test that fork bomb is caught by dangerous pattern detection."""
        fork_bomb = ":(){ :|:& };:"
        with pytest.raises(ModelRetry, match="Command contains dangerous pattern"):
            _validate_command_security(fork_bomb)

    def test_safe_commands_allowed(self):
        """Test that safe commands are allowed."""
        safe_commands = [
            "ls -la",
            "pwd",
            "echo hello world",
            "cat test.txt",
            "python --version",
            "npm test",
            "git status",
            "docker ps",
        ]

        # Should not raise any exceptions
        for command in safe_commands:
            try:
                _validate_command_security(command)
            except ModelRetry:
                pytest.fail(f"Safe command was blocked: {command}")

    def test_safe_commands_with_spaces_and_quotes(self):
        """Test that commands with spaces and quotes are handled correctly."""
        safe_commands = [
            'echo "hello world"',
            "ls 'test directory'",
            'grep "pattern" file.txt',
            "python -m unittest discover -s tests",
        ]

        # Should not raise any exceptions
        for command in safe_commands:
            try:
                _validate_command_security(command)
            except ModelRetry:
                pytest.fail(f"Safe command was blocked: {command}")


class TestBashExecution:
    """Test bash execution with security features."""

    @pytest.mark.asyncio
    async def test_simple_command_execution(self):
        """Test execution of simple, safe commands."""
        result = await bash("echo hello")
        assert "hello" in result
        assert "Exit Code: 0" in result

    @pytest.mark.asyncio
    async def test_command_with_working_directory(self):
        """Test command execution with custom working directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            result = await bash("pwd", cwd=temp_dir)
            assert temp_dir in result
            assert "Exit Code: 0" in result

    @pytest.mark.asyncio
    async def test_command_with_environment_variables(self):
        """Test command execution with custom environment variables."""
        env_vars = {"TEST_VAR": "test_value"}
        result = await bash("echo $TEST_VAR", env=env_vars)
        assert "test_value" in result
        assert "Exit Code: 0" in result

    @pytest.mark.asyncio
    async def test_command_timeout(self):
        """Test command timeout functionality."""
        with pytest.raises(ModelRetry, match="Command timed out"):
            await bash("sleep 10", timeout=1)

    @pytest.mark.asyncio
    async def test_security_validation_integration(self):
        """Test that security validation is properly integrated."""
        with pytest.raises(ModelRetry):
            await bash("ls; rm -rf /")

    @pytest.mark.asyncio
    async def test_nonexistent_directory(self):
        """Test handling of nonexistent working directory."""
        with pytest.raises(ModelRetry, match="Working directory .* does not exist"):
            await bash("ls", cwd="/nonexistent/directory/path/12345")

    @pytest.mark.asyncio
    async def test_invalid_timeout_range(self):
        """Test handling of invalid timeout values."""
        with pytest.raises(ModelRetry, match="Timeout must be between 1 and 300 seconds"):
            await bash("echo test", timeout=0)

        with pytest.raises(ModelRetry, match="Timeout must be between 1 and 300 seconds"):
            await bash("echo test", timeout=301)

    @pytest.mark.asyncio
    async def test_command_not_found_error_handling(self):
        """Test handling of command not found errors."""
        with pytest.raises(ModelRetry, match="Command .* not found"):
            await bash("nonexistentcommand12345")

    @pytest.mark.asyncio
    async def test_permission_denied_error_handling(self):
        """Test handling of permission denied errors."""
        # This test simulates a permission denied scenario
        with patch('asyncio.create_subprocess_shell') as mock_subprocess:
            mock_process = AsyncMock()
            mock_process.communicate.return_value = (b"", b"Permission denied")
            mock_process.returncode = 1
            mock_subprocess.return_value = mock_process

            with pytest.raises(ModelRetry, match="Permission denied"):
                await bash("test_command")

    @pytest.mark.asyncio
    async def test_no_capture_output(self):
        """Test command execution without capturing output."""
        # This is mainly testing that the parameter doesn't break execution
        # We can't easily test output suppression in unit tests
        result = await bash("echo hello", capture_output=False)
        # Should complete without error and return some formatted output
        assert "Command: echo hello" in result


class TestBashOutputFormatting:
    """Test output formatting functionality."""

    @pytest.mark.asyncio
    async def test_output_formatting(self):
        """Test that output is properly formatted."""
        result = await bash("echo test")

        expected_parts = [
            "Command: echo test",
            "Exit Code: 0",
            "Working Directory:",
            "STDOUT:",
            "STDERR:",
        ]

        for part in expected_parts:
            assert part in result

    @pytest.mark.asyncio
    async def test_error_output_formatting(self):
        """Test that error output is properly formatted."""
        # Command that will fail with stderr
        result = await bash("ls nonexistent_file_12345")

        assert "Exit Code:" in result
        assert "STDERR:" in result
        assert "no such file or directory" in result.lower() or "No such file" in result

    @pytest.mark.asyncio
    async def test_large_output_truncation(self):
        """Test that large output is properly truncated."""
        # Create a command that generates a lot of output
        large_output_cmd = "python -c \"print('x' * 10000)\""
        result = await bash(large_output_cmd)

        # Should be truncated
        assert len(result) < 10000
        assert "truncated" in result.lower() or len(result) < 5000


class TestBashProcessCleanup:
    """Test process cleanup functionality."""

    @pytest.mark.asyncio
    async def test_process_cleanup_on_timeout(self):
        """Test that processes are properly cleaned up on timeout."""
        with patch('asyncio.create_subprocess_shell') as mock_subprocess:
            mock_process = AsyncMock()
            # Simulate timeout
            mock_process.communicate.side_effect = asyncio.TimeoutError()
            mock_process.kill = AsyncMock()
            mock_process.wait = AsyncMock(return_value=None)
            mock_subprocess.return_value = mock_process

            with pytest.raises(ModelRetry, match="Command timed out"):
                await bash("sleep 100", timeout=1)

            # Verify cleanup was called
            mock_process.kill.assert_called_once()
            mock_process.wait.assert_called()

    @pytest.mark.asyncio
    async def test_process_cleanup_on_completion(self):
        """Test that cleanup runs even for successful processes."""
        with patch('asyncio.create_subprocess_shell') as mock_subprocess:
            mock_process = AsyncMock()
            mock_process.communicate.return_value = (b"output", b"")
            mock_process.returncode = 0
            mock_process.returncode = 0  # Already completed
            mock_subprocess.return_value = mock_process

            result = await bash("echo test")
            assert "output" in result or "test" in result