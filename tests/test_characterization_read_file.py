"""
Characterization tests for ReadFileTool.
These tests capture the CURRENT behavior of the tool, including any quirks.
"""
import os
import tempfile
import pytest
from pathlib import Path
from tunacode.tools.read_file import read_file
from tunacode.exceptions import ToolExecutionError

pytestmark = pytest.mark.asyncio


class TestReadFileCharacterization:
    """Golden-master tests for ReadFileTool behavior."""
    
    def setup_method(self):
        """Create a temporary directory for test files."""
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    async def test_read_simple_file(self):
        """Capture behavior when reading a simple text file."""
        # Arrange
        test_file = Path(self.temp_dir) / "simple.txt"
        test_content = "Hello, World!\nThis is a test file."
        test_file.write_text(test_content)
        
        # Act
        result = await read_file(str(test_file))
        
        # Assert - Golden master
        assert result == test_content
        assert isinstance(result, str)
    
    async def test_read_empty_file(self):
        """Capture behavior when reading an empty file."""
        # Arrange
        test_file = Path(self.temp_dir) / "empty.txt"
        test_file.write_text("")
        
        # Act
        result = await read_file(str(test_file))
        
        # Assert - Golden master
        assert result == ""
        assert isinstance(result, str)
    
    async def test_read_nonexistent_file(self):
        """Capture behavior when reading a file that doesn't exist."""
        # Arrange
        nonexistent_file = Path(self.temp_dir) / "does_not_exist.txt"
        
        # Act
        result = await read_file(str(nonexistent_file))
        
        # Assert - Golden master (returns error string, not exception)
        assert "File not found" in result
        assert str(nonexistent_file) in result
        assert isinstance(result, str)
    
    async def test_read_large_file_exceeds_limit(self):
        """Capture behavior when file exceeds MAX_FILE_SIZE."""
        # Arrange
        test_file = Path(self.temp_dir) / "large.txt"
        # Create a file larger than MAX_FILE_SIZE (assuming it's 1MB)
        large_content = "x" * (1024 * 1024 + 1)  # 1MB + 1 byte
        test_file.write_text(large_content)
        
        # Act
        result = await read_file(str(test_file))
        
        # Assert - Golden master (returns error string)
        assert "too large" in result.lower()
        assert str(test_file) in result
        assert isinstance(result, str)
    
    async def test_read_binary_file(self):
        """Capture behavior when reading a binary file."""
        # Arrange
        test_file = Path(self.temp_dir) / "binary.bin"
        test_file.write_bytes(b'\x00\x01\x02\x03\xff\xfe\xfd')
        
        # Act
        result = await read_file(str(test_file))
        
        # Assert - Golden master (returns error string for decode error)
        assert "decode" in result.lower() or "utf-8" in result.lower()
        assert str(test_file) in result
        assert isinstance(result, str)
    
    async def test_read_file_with_unicode(self):
        """Capture behavior when reading files with unicode characters."""
        # Arrange
        test_file = Path(self.temp_dir) / "unicode.txt"
        unicode_content = "Hello 世界! 🌍\nÜñíçödé têxt"
        test_file.write_text(unicode_content, encoding='utf-8')
        
        # Act
        result = await read_file(str(test_file))
        
        # Assert - Golden master
        assert result == unicode_content
        assert isinstance(result, str)
    
    async def test_read_file_with_newlines(self):
        """Capture behavior with different newline styles."""
        # Arrange
        test_file = Path(self.temp_dir) / "newlines.txt"
        # Mix of Unix and Windows newlines
        content = "Line 1\nLine 2\r\nLine 3\r\nLine 4"
        test_file.write_text(content)
        
        # Act
        result = await read_file(str(test_file))
        
        # Assert - Golden master (preserves exact content)
        # Windows newlines are converted to Unix newlines
        assert result == content.replace('\r\n', '\n')
        assert "\n" in result
    
    async def test_read_file_no_trailing_newline(self):
        """Capture behavior when file has no trailing newline."""
        # Arrange
        test_file = Path(self.temp_dir) / "no_newline.txt"
        content = "No trailing newline"
        test_file.write_bytes(content.encode('utf-8'))  # Ensure no newline added
        
        # Act
        result = await read_file(str(test_file))
        
        # Assert - Golden master
        assert result == content
        assert not result.endswith('\n')
    
    async def test_read_file_with_permission_denied(self):
        """Capture behavior when file permissions deny reading."""
        # Skip test if running as root (root can read anything)
        if os.getuid() == 0:
            pytest.skip("Permission tests don't work when running as root")
            
        # Arrange
        test_file = Path(self.temp_dir) / "no_read.txt"
        test_file.write_text("Secret content")
        os.chmod(test_file, 0o000)  # Remove all permissions
        
        try:
            # Act
            result = await read_file(str(test_file))
            
            # Assert - Golden master (returns error string)
            assert "permission" in result.lower() or "error" in result.lower()
            assert str(test_file) in result
            assert isinstance(result, str)
        finally:
            # Cleanup - restore permissions
            os.chmod(test_file, 0o644)
    
    async def test_read_relative_path(self):
        """Capture behavior when using relative paths."""
        # Arrange
        test_file = Path(self.temp_dir) / "relative.txt"
        content = "Relative path content"
        test_file.write_text(content)
        
        # Save current directory
        original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        
        try:
            # Act
            result = await read_file("relative.txt")
            
            # Assert - Golden master
            assert result == content
        finally:
            # Restore directory
            os.chdir(original_cwd)
    
    async def test_read_file_with_tabs_and_spaces(self):
        """Capture behavior with mixed whitespace."""
        # Arrange
        test_file = Path(self.temp_dir) / "whitespace.txt"
        content = "def function():\n\tindented_with_tab\n    indented_with_spaces"
        test_file.write_text(content)
        
        # Act
        result = await read_file(str(test_file))
        
        # Assert - Golden master (preserves exact whitespace)
        assert result == content
        assert "\t" in result
        assert "    " in result