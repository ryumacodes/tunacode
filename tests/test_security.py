"""
Security tests for command execution validation.
Tests various command injection scenarios and validates security controls.
"""

from unittest.mock import MagicMock, patch

import pytest

from tunacode.utils.security import (
    CommandSecurityError,
    safe_subprocess_popen,
    safe_subprocess_run,
    sanitize_command_args,
    validate_command_safety,
)


class TestCommandValidation:
    """Test command safety validation."""

    def test_empty_command_rejected(self):
        """Empty commands should be rejected."""
        with pytest.raises(CommandSecurityError, match="Empty command not allowed"):
            validate_command_safety("")

        with pytest.raises(CommandSecurityError, match="Empty command not allowed"):
            validate_command_safety("   ")

    def test_safe_commands_allowed(self):
        """Safe commands should pass validation."""
        safe_commands = [
            "ls -la",
            "cat file.txt",
            "python script.py",
            "git status",
            "npm install",
            "make test",
        ]

        for cmd in safe_commands:
            # Should not raise exception
            validate_command_safety(cmd, allow_shell_features=True)

    def test_dangerous_patterns_blocked(self):
        """Highly dangerous commands should always be blocked."""
        dangerous_commands = [
            "rm -rf /",
            "sudo rm -rf /home",
            "dd if=/dev/zero of=/dev/sda",
            "mkfs.ext4 /dev/sda1",
            "fdisk /dev/sda",
            ":(){:|:&};:",  # Fork bomb
        ]

        for cmd in dangerous_commands:
            with pytest.raises(CommandSecurityError, match="dangerous pattern"):
                validate_command_safety(cmd, allow_shell_features=True)

    def test_injection_patterns_detected(self):
        """Command injection patterns should be detected when shell features disabled."""
        injection_commands = [
            "ls; rm file",
            "cat file && rm file",
            "echo `rm file`",
            "echo $(rm file)",
        ]

        for cmd in injection_commands:
            with pytest.raises(CommandSecurityError):
                validate_command_safety(cmd, allow_shell_features=False)

    def test_shell_features_allowed_when_enabled(self):
        """Shell features should be allowed when explicitly enabled."""
        shell_commands = [
            "ls | grep txt",
            "cat file > output.txt",
            "python script.py < input.txt",
        ]

        for cmd in shell_commands:
            # Should not raise exception when shell features allowed
            validate_command_safety(cmd, allow_shell_features=True)

    def test_dangerous_characters_blocked_when_strict(self):
        """Dangerous characters should be blocked in strict mode."""
        risky_commands = [
            "echo hello; echo world",
            "ls && echo done",
            "echo `date`",
            "echo $HOME",
            "ls {*.txt,*.py}",
        ]

        for cmd in risky_commands:
            with pytest.raises(CommandSecurityError):
                validate_command_safety(cmd, allow_shell_features=False)


class TestSecureSubprocess:
    """Test secure subprocess wrappers."""

    @patch("tunacode.utils.security.subprocess.run")
    def test_safe_subprocess_run_with_validation(self, mock_run):
        """Test safe_subprocess_run with validation enabled."""
        mock_run.return_value = MagicMock(returncode=0)

        # Safe command should execute
        safe_subprocess_run("ls -la", shell=True, validate=True)
        mock_run.assert_called_once()

        # Reset mock
        mock_run.reset_mock()

        # Dangerous command should not execute
        with pytest.raises(CommandSecurityError):
            safe_subprocess_run("rm -rf /", shell=True, validate=True)
        mock_run.assert_not_called()

    @patch("tunacode.utils.security.subprocess.run")
    def test_safe_subprocess_run_without_validation(self, mock_run):
        """Test safe_subprocess_run with validation disabled."""
        mock_run.return_value = MagicMock(returncode=0)

        # Even dangerous command should execute when validation disabled
        safe_subprocess_run("rm -rf /", shell=True, validate=False)
        mock_run.assert_called_once()

    @patch("tunacode.utils.security.subprocess.Popen")
    def test_safe_subprocess_popen_with_validation(self, mock_popen):
        """Test safe_subprocess_popen with validation enabled."""
        mock_popen.return_value = MagicMock()

        # Safe command should execute
        safe_subprocess_popen("ls -la", shell=True, validate=True)
        mock_popen.assert_called_once()

        # Reset mock
        mock_popen.reset_mock()

        # Dangerous command should not execute
        with pytest.raises(CommandSecurityError):
            safe_subprocess_popen("rm -rf /", shell=True, validate=True)
        mock_popen.assert_not_called()

    def test_command_args_sanitization(self):
        """Test command argument sanitization."""
        args = ["file name with spaces.txt", "file'with'quotes.txt", "file;with;semicolons.txt"]
        sanitized = sanitize_command_args(args)

        # All args should be properly quoted
        assert "'file name with spaces.txt'" in sanitized[0]
        assert (
            "\"file'with'quotes.txt\"" in sanitized[1]
            or "'file'\"'\"'with'\"'\"'quotes.txt'" in sanitized[1]
        )
        assert "'file;with;semicolons.txt'" in sanitized[2]


class TestSecurityIntegration:
    """Integration tests for security features."""

    @patch("tunacode.utils.security.subprocess.run")
    @patch("tunacode.utils.security.logger")
    def test_security_logging(self, mock_logger, mock_run):
        """Test that security events are logged."""
        mock_run.return_value = MagicMock(returncode=0)

        # Execute safe command
        safe_subprocess_run("ls -la", shell=True, validate=True)

        # Verify logging occurred
        mock_logger.info.assert_called()

        # Reset mocks
        mock_logger.reset_mock()
        mock_run.reset_mock()

        # Try dangerous command
        with pytest.raises(CommandSecurityError):
            safe_subprocess_run("rm -rf /", shell=True, validate=True)

        # Verify error logging occurred
        mock_logger.error.assert_called()

    def test_error_context_preservation(self):
        """Test that security errors preserve context."""
        try:
            validate_command_safety("rm -rf /")
        except CommandSecurityError as e:
            assert "dangerous pattern" in str(e).lower()
            assert len(str(e)) > 10  # Should have meaningful message


if __name__ == "__main__":
    pytest.main([__file__])
