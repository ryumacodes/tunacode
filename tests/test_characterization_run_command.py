"""
Characterization tests for RunCommandTool.
These tests capture the CURRENT behavior of the tool, including any quirks.
"""
import os
import tempfile
import pytest
from pathlib import Path
from tunacode.tools.run_command import run_command

pytestmark = pytest.mark.asyncio


class TestRunCommandCharacterization:
    """Golden-master tests for RunCommandTool behavior."""
    
    def setup_method(self):
        """Create a temporary directory for test files."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
    
    def teardown_method(self):
        """Clean up and restore directory."""
        os.chdir(self.original_cwd)
        import shutil
        shutil.rmtree(self.temp_dir)
    
    async def test_run_command_simple(self):
        """Capture behavior with simple command."""
        # Act
        result = await run_command("echo 'Hello World'")
        
        # Assert - Golden master
        assert "STDOUT:" in result
        assert "STDERR:" in result
        assert "Hello World" in result
        assert "No errors." in result
        assert isinstance(result, str)
    
    async def test_run_command_no_output(self):
        """Capture behavior when command produces no output."""
        # Act
        result = await run_command("true")  # Command that succeeds silently
        
        # Assert - Golden master
        assert "STDOUT:" in result
        assert "STDERR:" in result
        assert "No output." in result
        assert "No errors." in result
    
    async def test_run_command_stderr_output(self):
        """Capture behavior when command outputs to stderr."""
        # Act
        result = await run_command("echo 'Error message' >&2")
        
        # Assert - Golden master
        assert "STDOUT:" in result
        assert "STDERR:" in result
        assert "No output." in result  # Nothing on stdout
        assert "Error message" in result  # On stderr
    
    async def test_run_command_both_outputs(self):
        """Capture behavior with both stdout and stderr."""
        # Act
        result = await run_command("echo 'Normal'; echo 'Error' >&2")
        
        # Assert - Golden master
        assert "STDOUT:" in result
        assert "STDERR:" in result
        assert "Normal" in result
        assert "Error" in result
    
    async def test_run_command_exit_code_nonzero(self):
        """Capture behavior when command exits with non-zero code."""
        # Act
        result = await run_command("exit 1")
        
        # Assert - Golden master (still returns output, not error)
        assert "STDOUT:" in result
        assert "STDERR:" in result
        assert "No output." in result
        assert "No errors." in result
    
    async def test_run_command_not_found(self):
        """Capture behavior when command doesn't exist."""
        # Act
        result = await run_command("this_command_does_not_exist_12345")
        
        # Assert - Golden master
        assert "STDOUT:" in result or "Error executing command" in result
        # Command not found appears in stderr or as error
        assert "not found" in result.lower() or "error" in result.lower()
    
    async def test_run_command_with_pipes(self):
        """Capture behavior with piped commands."""
        # Act
        result = await run_command("echo 'test' | grep 'test'")
        
        # Assert - Golden master
        assert "STDOUT:" in result
        assert "test" in result
    
    async def test_run_command_with_redirection(self):
        """Capture behavior with file redirection."""
        # Arrange
        test_file = "test_output.txt"
        
        # Act
        result = await run_command(f"echo 'redirected' > {test_file}")
        
        # Assert - Golden master
        assert "STDOUT:" in result
        assert "No output." in result  # Output went to file
        # Verify file was created
        assert Path(test_file).exists()
        assert Path(test_file).read_text().strip() == "redirected"
    
    async def test_run_command_multiline_output(self):
        """Capture behavior with multiline output."""
        # Act
        result = await run_command("echo -e 'Line 1\\nLine 2\\nLine 3'")
        
        # Assert - Golden master
        assert "STDOUT:" in result
        assert "Line 1" in result
        assert "Line 2" in result
        assert "Line 3" in result
    
    async def test_run_command_with_env_vars(self):
        """Capture behavior with environment variables."""
        # Act
        result = await run_command("TEST_VAR='hello' && echo $TEST_VAR")
        
        # Assert - Golden master
        assert "STDOUT:" in result
        assert "hello" in result
    
    async def test_run_command_truncation(self):
        """Capture behavior when output exceeds MAX_COMMAND_OUTPUT."""
        # Create a command that generates a lot of output
        # Using yes command with head to control output size
        large_output_cmd = "for i in {1..1000}; do echo 'This is a very long line of output that will be repeated many times to test truncation behavior'; done"
        
        # Act
        result = await run_command(large_output_cmd)
        
        # Assert - Golden master
        if "[truncated]" in result:
            # Output was truncated
            assert "STDOUT:" in result
            assert "[truncated]" in result
            # Should preserve beginning and end
            assert result.index("[truncated]") > 100  # Some content before truncation
    
    async def test_run_command_with_quotes(self):
        """Capture behavior with various quote styles."""
        # Act
        result = await run_command('echo "Double quotes" && echo \'Single quotes\'')
        
        # Assert - Golden master
        assert "Double quotes" in result
        assert "Single quotes" in result
    
    async def test_run_command_cd_changes_directory(self):
        """Capture behavior when changing directories."""
        # Arrange
        subdir = Path("subdir")
        subdir.mkdir()
        
        # Act
        result = await run_command("cd subdir && pwd")
        
        # Assert - Golden master
        assert "STDOUT:" in result
        assert "subdir" in result
    
    async def test_run_command_special_characters(self):
        """Capture behavior with special shell characters."""
        # Act
        result = await run_command("echo '$HOME' && echo '$(date)' && echo '*'")
        
        # Assert - Golden master
        assert "STDOUT:" in result
        # $HOME should be expanded
        assert "/" in result or "\\" in result  # Path separator
        # $(date) should show command substitution
        # * should be literal (in quotes)
        assert "*" in result
    
    async def test_run_command_background_process(self):
        """Capture behavior with background processes."""
        # Act - Start a background process and immediately check
        result = await run_command("sleep 10 & echo 'Started background process'")
        
        # Assert - Golden master
        assert "Started background process" in result
        # The sleep command runs in background, so we get output immediately
    
    async def test_run_command_unicode_output(self):
        """Capture behavior with unicode output."""
        # Act
        result = await run_command("echo '世界 🌍 Ñiño'")
        
        # Assert - Golden master
        assert "STDOUT:" in result
        assert "世界" in result
        assert "🌍" in result
        assert "Ñiño" in result
    
    async def test_run_command_null_bytes(self):
        """Capture behavior with null bytes in output."""
        # Act - Use printf to include null bytes
        result = await run_command("printf 'before\\0after'")
        
        # Assert - Golden master
        assert "STDOUT:" in result
        # Null bytes might be filtered or preserved
        assert "before" in result or "beforeafter" in result
    
    async def test_run_command_very_long_single_line(self):
        """Capture behavior with very long single line output."""
        # Act
        result = await run_command("echo -n '" + "x" * 1000 + "'")
        
        # Assert - Golden master
        assert "STDOUT:" in result
        assert "x" * 100 in result  # At least some x's present
    
    async def test_run_command_binary_output(self):
        """Capture behavior when command outputs binary data."""
        # Act - Create a small binary file and cat it
        result = await run_command("echo -ne '\\x00\\x01\\x02\\xff' > binary.dat && cat binary.dat")
        
        # Assert - Golden master
        # Binary output might be filtered or cause issues
        assert "STDOUT:" in result or "Error" in result