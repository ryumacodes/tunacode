"""
Characterization tests for BashTool.
These tests capture the CURRENT behavior of the tool, including any quirks.
"""
import os
import tempfile
import pytest
import time
from pathlib import Path
from tunacode.tools.bash import bash
from pydantic_ai import ModelRetry

pytestmark = pytest.mark.asyncio


class TestBashCharacterization:
    """Golden-master tests for BashTool behavior."""
    
    def setup_method(self):
        """Create a temporary directory for test files."""
        self.temp_dir = tempfile.mkdtemp()
        # Set a safe working directory
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
    
    def teardown_method(self):
        """Clean up and restore directory."""
        os.chdir(self.original_cwd)
        import shutil
        shutil.rmtree(self.temp_dir)
    
    async def test_bash_simple_command(self):
        """Capture behavior of simple command execution."""
        # Act
        result = await bash("echo 'Hello World'")
        
        # Assert - Golden master
        assert "Exit Code: 0" in result
        assert "Hello World" in result
        assert "STDOUT:" in result
        assert "STDERR:" in result
        assert isinstance(result, str)
    
    async def test_bash_command_with_exit_code(self):
        """Capture behavior when command returns non-zero exit code."""
        # Act
        result = await bash("exit 42")
        
        # Assert - Golden master
        assert "Exit Code: 42" in result
        assert isinstance(result, str)
    
    async def test_bash_command_not_found(self):
        """Capture behavior when command doesn't exist."""
        # Act
        result = await bash("this_command_does_not_exist_12345")
        
        # Assert - Golden master
        assert "Exit Code:" in result
        assert result.split("Exit Code: ")[1].split()[0] != "0"  # Non-zero exit
        assert "command not found" in result.lower() or "not found" in result.lower()
    
    async def test_bash_with_timeout(self):
        """Capture behavior when command times out."""
        # Act & Assert - Command that would run longer than timeout
        with pytest.raises(ModelRetry) as exc_info:
            await bash("sleep 5", timeout=1)
        
        # Assert - Golden master
        assert "timed out" in str(exc_info.value)
        assert "1 seconds" in str(exc_info.value)
    
    async def test_bash_timeout_validation(self):
        """Capture behavior with invalid timeout values."""
        # Act & Assert - Timeout too high
        with pytest.raises(ModelRetry) as exc_info:
            await bash("echo test", timeout=301)
        assert "300 seconds" in str(exc_info.value)
        
        # Act & Assert - Timeout too low (results in immediate timeout)
        with pytest.raises(ModelRetry) as exc_info:
            await bash("echo test", timeout=0)
        assert "timed out after 0 seconds" in str(exc_info.value)
    
    async def test_bash_with_working_directory(self):
        """Capture behavior when specifying working directory."""
        # Arrange
        sub_dir = Path(self.temp_dir) / "subdir"
        sub_dir.mkdir()
        (sub_dir / "test.txt").write_text("content")
        
        # Act
        result = await bash("ls", cwd=str(sub_dir))
        
        # Assert - Golden master
        assert "Exit Code: 0" in result
        assert "test.txt" in result
    
    async def test_bash_invalid_working_directory(self):
        """Capture behavior with non-existent working directory."""
        # Act & Assert
        with pytest.raises(ModelRetry) as exc_info:
            await bash("echo test", cwd="/this/does/not/exist")
        
        assert "does not exist" in str(exc_info.value)
    
    async def test_bash_with_environment_variables(self):
        """Capture behavior when setting environment variables."""
        # Act
        result = await bash(
            "echo $MY_VAR",
            env={"MY_VAR": "custom_value"}
        )
        
        # Assert - Golden master
        assert "Exit Code: 0" in result
        assert "custom_value" in result
    
    async def test_bash_destructive_command_blocked(self):
        """Capture behavior when trying destructive commands."""
        # Act & Assert - rm -rf
        with pytest.raises(ModelRetry) as exc_info:
            await bash("rm -rf /")
        assert "destructive" in str(exc_info.value).lower()
        
        # Act & Assert - force remove
        with pytest.raises(ModelRetry) as exc_info:
            await bash("rm -rf --no-preserve-root /")
        assert "destructive" in str(exc_info.value).lower()
    
    async def test_bash_stderr_output(self):
        """Capture behavior when command writes to stderr."""
        # Act
        result = await bash("echo 'Error message' >&2")
        
        # Assert - Golden master
        assert "Exit Code: 0" in result
        assert "STDERR:" in result
        assert "Error message" in result
    
    async def test_bash_mixed_output(self):
        """Capture behavior with both stdout and stderr."""
        # Act
        result = await bash("echo 'To stdout'; echo 'To stderr' >&2")
        
        # Assert - Golden master
        assert "Exit Code: 0" in result
        assert "STDOUT:" in result
        assert "To stdout" in result
        assert "STDERR:" in result
        assert "To stderr" in result
    
    async def test_bash_large_output_truncation(self):
        """Capture behavior when output exceeds MAX_COMMAND_OUTPUT."""
        # Act - Generate large output (assuming MAX is around 50KB)
        result = await bash("for i in {1..10000}; do echo 'Line '$i; done")
        
        # Assert - Golden master
        assert "Exit Code: 0" in result
        # Check for truncation indicator
        if len(result) > 50000:  # Approximate MAX_COMMAND_OUTPUT
            assert "truncated" in result.lower() or "..." in result
    
    async def test_bash_multiline_command(self):
        """Capture behavior with multiline bash commands."""
        # Act
        result = await bash("""
echo "Line 1"
echo "Line 2"
echo "Line 3"
""")
        
        # Assert - Golden master
        assert "Exit Code: 0" in result
        assert "Line 1" in result
        assert "Line 2" in result
        assert "Line 3" in result
    
    async def test_bash_pipe_commands(self):
        """Capture behavior with piped commands."""
        # Arrange
        Path("test.txt").write_text("apple\nbanana\napple\ncherry")
        
        # Act
        result = await bash("cat test.txt | grep apple | wc -l")
        
        # Assert - Golden master
        assert "Exit Code: 0" in result
        assert "2" in result  # Two lines contain 'apple'
    
    async def test_bash_background_process(self):
        """Capture behavior when trying to run background processes."""
        # Act
        result = await bash("sleep 1 &")
        
        # Assert - Golden master
        # Background processes might complete or be killed
        assert "Exit Code:" in result
    
    async def test_bash_interactive_command(self):
        """Capture behavior with commands that expect input."""
        # Act - Command that would normally wait for input
        result = await bash("read -p 'Enter name: ' name", timeout=2)
        
        # Assert - Golden master
        # Should timeout or complete without input
        assert "Exit Code:" in result
    
    async def test_bash_command_with_quotes(self):
        """Capture behavior with complex quoting."""
        # Act
        result = await bash('echo "Hello \'World\'" && echo \'Single "quotes"\'')
        
        # Assert - Golden master
        assert "Exit Code: 0" in result
        assert "Hello 'World'" in result
        assert 'Single "quotes"' in result
    
    async def test_bash_capture_output_false(self):
        """Capture behavior when capture_output is False."""
        # Act
        result = await bash("echo 'Should not capture'", capture_output=False)
        
        # Assert - Golden master
        assert "Exit Code: 0" in result
        # Output might be empty or have different format
        assert isinstance(result, str)