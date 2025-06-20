"""
Characterization tests for WriteFileTool.
These tests capture the CURRENT behavior of the tool, including any quirks.
"""
import os
import tempfile
import pytest
from pathlib import Path
from tunacode.tools.write_file import write_file
from pydantic_ai import ModelRetry

pytestmark = pytest.mark.asyncio


class TestWriteFileCharacterization:
    """Golden-master tests for WriteFileTool behavior."""
    
    def setup_method(self):
        """Create a temporary directory for test files."""
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    async def test_write_new_file(self):
        """Capture behavior when writing a new file."""
        # Arrange
        test_file = Path(self.temp_dir) / "new_file.txt"
        content = "This is new content\nWith multiple lines"
        
        # Act
        result = await write_file(str(test_file), content)
        
        # Assert - Golden master
        assert result == f"Successfully wrote to new file: {test_file}"
        assert test_file.exists()
        assert test_file.read_text() == content
    
    async def test_write_existing_file_raises_retry(self):
        """Capture behavior when trying to write to existing file."""
        # Arrange
        test_file = Path(self.temp_dir) / "existing.txt"
        test_file.write_text("Original content")
        
        # Act & Assert - Golden master (raises ModelRetry)
        with pytest.raises(ModelRetry) as exc_info:
            await write_file(str(test_file), "New content")
        
        assert "already exists" in str(exc_info.value)
        assert str(test_file) in str(exc_info.value)
        # Original content unchanged
        assert test_file.read_text() == "Original content"
    
    async def test_write_creates_parent_directories(self):
        """Capture behavior when parent directories don't exist."""
        # Arrange
        test_file = Path(self.temp_dir) / "deep" / "nested" / "dir" / "file.txt"
        content = "Content in deeply nested file"
        
        # Act
        result = await write_file(str(test_file), content)
        
        # Assert - Golden master
        assert result == f"Successfully wrote to new file: {test_file}"
        assert test_file.exists()
        assert test_file.read_text() == content
        assert test_file.parent.exists()
        assert test_file.parent.parent.exists()
    
    async def test_write_empty_content(self):
        """Capture behavior when writing empty content."""
        # Arrange
        test_file = Path(self.temp_dir) / "empty.txt"
        content = ""
        
        # Act
        result = await write_file(str(test_file), content)
        
        # Assert - Golden master
        assert result == f"Successfully wrote to new file: {test_file}"
        assert test_file.exists()
        assert test_file.read_text() == ""
        assert test_file.stat().st_size == 0
    
    async def test_write_unicode_content(self):
        """Capture behavior when writing unicode content."""
        # Arrange
        test_file = Path(self.temp_dir) / "unicode.txt"
        content = "Unicode: 世界 🌍 Ñiño café"
        
        # Act
        result = await write_file(str(test_file), content)
        
        # Assert - Golden master
        assert result == f"Successfully wrote to new file: {test_file}"
        assert test_file.exists()
        assert test_file.read_text(encoding='utf-8') == content
    
    async def test_write_with_newlines(self):
        """Capture behavior with different newline styles."""
        # Arrange
        test_file = Path(self.temp_dir) / "newlines.txt"
        # Mix of newline styles
        content = "Line 1\nLine 2\r\nLine 3"
        
        # Act
        result = await write_file(str(test_file), content)
        
        # Assert - Golden master (preserves exact content)
        assert result == f"Successfully wrote to new file: {test_file}"
        assert test_file.exists()
        # Windows newlines are normalized to Unix newlines
        assert test_file.read_text() == content.replace('\r\n', '\n')
    
    async def test_write_no_trailing_newline(self):
        """Capture behavior when content has no trailing newline."""
        # Arrange
        test_file = Path(self.temp_dir) / "no_newline.txt"
        content = "No trailing newline"
        
        # Act
        result = await write_file(str(test_file), content)
        
        # Assert - Golden master
        assert result == f"Successfully wrote to new file: {test_file}"
        assert test_file.exists()
        assert test_file.read_text() == content
        assert not test_file.read_text().endswith('\n')
    
    async def test_write_very_long_content(self):
        """Capture behavior with large content."""
        # Arrange
        test_file = Path(self.temp_dir) / "large.txt"
        # 100KB of content
        content = "x" * (100 * 1024)
        
        # Act
        result = await write_file(str(test_file), content)
        
        # Assert - Golden master
        assert result == f"Successfully wrote to new file: {test_file}"
        assert test_file.exists()
        assert test_file.read_text() == content
        assert test_file.stat().st_size == len(content)
    
    async def test_write_with_tabs_and_spaces(self):
        """Capture behavior with mixed whitespace."""
        # Arrange
        test_file = Path(self.temp_dir) / "whitespace.py"
        content = "def function():\n\tprint('tab')\n    print('spaces')"
        
        # Act
        result = await write_file(str(test_file), content)
        
        # Assert - Golden master (preserves exact whitespace)
        assert result == f"Successfully wrote to new file: {test_file}"
        assert test_file.exists()
        assert test_file.read_text() == content
        assert "\t" in test_file.read_text()
        assert "    " in test_file.read_text()
    
    async def test_write_relative_path(self):
        """Capture behavior when using relative paths."""
        # Arrange
        content = "Relative path content"
        
        # Save current directory
        original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        
        try:
            # Act
            result = await write_file("relative.txt", content)
            
            # Assert - Golden master
            assert "Successfully wrote to new file" in result
            assert Path("relative.txt").exists()
            assert Path("relative.txt").read_text() == content
        finally:
            # Restore directory
            os.chdir(original_cwd)
    
    async def test_write_with_permission_denied(self):
        """Capture behavior when directory permissions deny writing."""
        # Skip test if running as root (root can write anywhere)
        if os.getuid() == 0:
            pytest.skip("Permission tests don't work when running as root")
            
        # Arrange
        protected_dir = Path(self.temp_dir) / "protected"
        protected_dir.mkdir()
        os.chmod(protected_dir, 0o555)  # Read/execute only
        test_file = protected_dir / "file.txt"
        
        try:
            # Act - write_file returns error string, not exception
            result = await write_file(str(test_file), "Content")
            
            # Golden master - captures the error message
            assert "Permission" in result or "permission" in result or "error" in result.lower()
        finally:
            # Cleanup - restore permissions
            os.chmod(protected_dir, 0o755)
    
    async def test_write_file_with_null_bytes(self):
        """Capture behavior when content contains null bytes."""
        # Arrange
        test_file = Path(self.temp_dir) / "null_bytes.txt"
        content = "Before\x00null\x00After"
        
        # Act
        result = await write_file(str(test_file), content)
        
        # Assert - Golden master
        assert result == f"Successfully wrote to new file: {test_file}"
        assert test_file.exists()
        # File should contain the null bytes
        assert test_file.read_bytes() == content.encode('utf-8')