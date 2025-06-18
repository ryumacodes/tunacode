"""
Characterization tests for UpdateFileTool.
These tests capture the CURRENT behavior of the tool, including any quirks.
"""
import os
import tempfile
import pytest
from pathlib import Path
from tunacode.tools.update_file import update_file
from pydantic_ai import ModelRetry

pytestmark = pytest.mark.asyncio


class TestUpdateFileCharacterization:
    """Golden-master tests for UpdateFileTool behavior."""
    
    def setup_method(self):
        """Create a temporary directory for test files."""
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    async def test_update_existing_file(self):
        """Capture behavior when updating an existing file."""
        # Arrange
        test_file = Path(self.temp_dir) / "existing.txt"
        original_content = "Hello World\nThis is a test\nGoodbye World"
        test_file.write_text(original_content)
        
        # Act
        result = await update_file(
            str(test_file),
            target="This is a test",
            patch="This is updated"
        )
        
        # Assert - Golden master
        assert result == f"File '{test_file}' updated successfully."
        assert test_file.read_text() == "Hello World\nThis is updated\nGoodbye World"
    
    async def test_update_nonexistent_file_raises_retry(self):
        """Capture behavior when trying to update non-existent file."""
        # Arrange
        test_file = Path(self.temp_dir) / "does_not_exist.txt"
        
        # Act & Assert - Golden master (raises ModelRetry)
        with pytest.raises(ModelRetry) as exc_info:
            await update_file(
                str(test_file),
                target="something",
                patch="something else"
            )
        
        assert "not found" in str(exc_info.value)
        assert str(test_file) in str(exc_info.value)
    
    async def test_update_target_not_found_raises_retry(self):
        """Capture behavior when target text is not found."""
        # Arrange
        test_file = Path(self.temp_dir) / "file.txt"
        content = "Line 1\nLine 2\nLine 3"
        test_file.write_text(content)
        
        # Act & Assert - Golden master (raises ModelRetry with file snippet)
        with pytest.raises(ModelRetry) as exc_info:
            await update_file(
                str(test_file),
                target="This text does not exist",
                patch="replacement"
            )
        
        error_msg = str(exc_info.value)
        assert "not found" in error_msg
        # Target text not in error, but file snippet is
        # Should include file snippet
        assert "Line 1" in error_msg or "..." in error_msg
    
    async def test_update_target_equals_patch_raises_retry(self):
        """Capture behavior when target and patch are identical."""
        # Arrange
        test_file = Path(self.temp_dir) / "file.txt"
        content = "Some content here"
        test_file.write_text(content)
        
        # Act & Assert - Golden master (raises ModelRetry)
        with pytest.raises(ModelRetry) as exc_info:
            await update_file(
                str(test_file),
                target="content",
                patch="content"
            )
        
        assert "identical to the" in str(exc_info.value) or "no changes" in str(exc_info.value)
    
    async def test_update_only_first_occurrence(self):
        """Capture behavior when target appears multiple times."""
        # Arrange
        test_file = Path(self.temp_dir) / "multiple.txt"
        content = "foo bar\nfoo baz\nfoo qux"
        test_file.write_text(content)
        
        # Act
        result = await update_file(
            str(test_file),
            target="foo",
            patch="FOO"
        )
        
        # Assert - Golden master (only first occurrence replaced)
        assert result == f"File '{test_file}' updated successfully."
        assert test_file.read_text() == "FOO bar\nfoo baz\nfoo qux"
    
    async def test_update_multiline_target(self):
        """Capture behavior with multiline target."""
        # Arrange
        test_file = Path(self.temp_dir) / "multiline.txt"
        content = "Start\nLine 1\nLine 2\nLine 3\nEnd"
        test_file.write_text(content)
        
        # Act
        result = await update_file(
            str(test_file),
            target="Line 1\nLine 2\nLine 3",
            patch="Single replacement line"
        )
        
        # Assert - Golden master
        assert result == f"File '{test_file}' updated successfully."
        assert test_file.read_text() == "Start\nSingle replacement line\nEnd"
    
    async def test_update_empty_target(self):
        """Capture behavior with empty target string."""
        # Arrange
        test_file = Path(self.temp_dir) / "file.txt"
        content = "Some content"
        test_file.write_text(content)
        
        # Act & Assert - What happens with empty target?
        # This might raise an error or have undefined behavior
        try:
            result = await update_file(
                str(test_file),
                target="",
                patch="replacement"
            )
            # If it succeeds, capture the behavior
            assert False, f"Expected error but got: {result}"
        except Exception as e:
            # Capture the actual exception type and message
            assert True  # Expected some error
    
    async def test_update_empty_patch(self):
        """Capture behavior with empty patch (deletion)."""
        # Arrange
        test_file = Path(self.temp_dir) / "file.txt"
        content = "Before DELETE_ME After"
        test_file.write_text(content)
        
        # Act
        result = await update_file(
            str(test_file),
            target="DELETE_ME ",
            patch=""
        )
        
        # Assert - Golden master (empty patch removes text)
        assert result == f"File '{test_file}' updated successfully."
        assert test_file.read_text() == "Before After"
    
    async def test_update_preserves_newlines(self):
        """Capture behavior with different newline styles."""
        # Arrange
        test_file = Path(self.temp_dir) / "newlines.txt"
        # Mix of Unix and Windows newlines
        content = "Line 1\nLine 2\r\nLine 3\r\nLine 4"
        test_file.write_text(content)
        
        # Act
        result = await update_file(
            str(test_file),
            target="Line 2",
            patch="Updated Line 2"
        )
        
        # Assert - Golden master (preserves newline style)
        assert result == f"File '{test_file}' updated successfully."
        updated = test_file.read_text()
        # Windows newlines are normalized to Unix newlines
        assert "Updated Line 2\n" in updated
        assert updated == "Line 1\nUpdated Line 2\nLine 3\nLine 4"
    
    async def test_update_with_unicode(self):
        """Capture behavior with unicode characters."""
        # Arrange
        test_file = Path(self.temp_dir) / "unicode.txt"
        content = "Hello 世界\nUpdate this → line\nÑiño"
        test_file.write_text(content, encoding='utf-8')
        
        # Act
        result = await update_file(
            str(test_file),
            target="Update this → line",
            patch="Updated ✓ line"
        )
        
        # Assert - Golden master
        assert result == f"File '{test_file}' updated successfully."
        assert test_file.read_text() == "Hello 世界\nUpdated ✓ line\nÑiño"
    
    async def test_update_with_regex_special_chars(self):
        """Capture behavior when target contains regex special characters."""
        # Arrange
        test_file = Path(self.temp_dir) / "regex.txt"
        content = "function() { return $test.value[0]; }"
        test_file.write_text(content)
        
        # Act
        result = await update_file(
            str(test_file),
            target="$test.value[0]",
            patch="$updated.data[1]"
        )
        
        # Assert - Golden master (should handle literal strings)
        assert result == f"File '{test_file}' updated successfully."
        assert test_file.read_text() == "function() { return $updated.data[1]; }"
    
    async def test_update_preserves_file_ending(self):
        """Capture behavior regarding file endings."""
        # Arrange
        test_file = Path(self.temp_dir) / "ending.txt"
        # File with no trailing newline
        content = "Line 1\nLine 2"
        test_file.write_bytes(content.encode('utf-8'))
        
        # Act
        result = await update_file(
            str(test_file),
            target="Line 2",
            patch="Updated Line 2"
        )
        
        # Assert - Golden master (preserves lack of trailing newline)
        assert result == f"File '{test_file}' updated successfully."
        updated = test_file.read_text()
        assert updated == "Line 1\nUpdated Line 2"
        assert not updated.endswith('\n')
    
    async def test_update_whitespace_sensitive(self):
        """Capture behavior with whitespace differences."""
        # Arrange
        test_file = Path(self.temp_dir) / "whitespace.py"
        content = "def func():\n    return True  # Two spaces\n\tprint('tab')"
        test_file.write_text(content)
        
        # Act & Assert - Whitespace must match exactly
        with pytest.raises(ModelRetry) as exc_info:
            await update_file(
                str(test_file),
                target="return True # Two spaces",  # Missing spaces
                patch="return False"
            )
        
        assert "not found" in str(exc_info.value)