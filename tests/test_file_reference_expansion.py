"""Test @ file reference expansion functionality."""

import os
import tempfile
from pathlib import Path

import pytest

from tunacode.utils.text_utils import expand_file_refs


class TestFileReferenceExpansion:
    """Test cases for @ file reference expansion."""

    def test_expand_simple_file_reference(self):
        """Test expanding a simple @ file reference."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("print('Hello, World!')")
            f.flush()
            
            try:
                text = f"Please analyze @{f.name}"
                expanded = expand_file_refs(text)
                
                assert "```python" in expanded
                assert "print('Hello, World!')" in expanded
                assert "```" in expanded
            finally:
                os.unlink(f.name)

    def test_expand_multiple_file_references(self):
        """Test expanding multiple @ file references."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f1, \
             tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False) as f2:
            
            f1.write("def hello():\n    return 'Hello'")
            f1.flush()
            
            f2.write("console.log('Hello');")
            f2.flush()
            
            try:
                text = f"Compare @{f1.name} with @{f2.name}"
                expanded = expand_file_refs(text)
                
                assert "```python" in expanded
                assert "def hello():" in expanded
                assert "```javascript" in expanded
                assert "console.log('Hello');" in expanded
            finally:
                os.unlink(f1.name)
                os.unlink(f2.name)

    def test_file_not_found_error(self):
        """Test error handling for non-existent files."""
        text = "Please analyze @/path/that/does/not/exist.py"
        
        with pytest.raises(ValueError) as exc_info:
            expand_file_refs(text)
        
        assert "File not found" in str(exc_info.value)

    def test_file_too_large_error(self):
        """Test error handling for files that are too large."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            # Write more than MAX_FILE_SIZE (10MB)
            f.write("x" * (10 * 1024 * 1024 + 1))
            f.flush()
            
            try:
                text = f"Please analyze @{f.name}"
                
                with pytest.raises(ValueError) as exc_info:
                    expand_file_refs(text)
                
                assert "too large" in str(exc_info.value)
            finally:
                os.unlink(f.name)

    def test_preserve_text_around_references(self):
        """Test that text around @ references is preserved."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("# Test File\nThis is a test.")
            f.flush()
            
            try:
                text = f"Before @{f.name} and after"
                expanded = expand_file_refs(text)
                
                assert "Before" in expanded
                assert "and after" in expanded
                assert "```text" in expanded  # .md files default to text
                assert "# Test File" in expanded
            finally:
                os.unlink(f.name)

    def test_various_file_extensions(self):
        """Test language detection for various file extensions."""
        test_cases = [
            (".py", "python"),
            (".js", "javascript"),
            (".ts", "typescript"),
            (".java", "java"),
            (".c", "c"),
            (".cpp", "cpp"),
            (".cs", "csharp"),
            (".html", "html"),
            (".css", "css"),
            (".json", "json"),
            (".yaml", "yaml"),
            (".yml", "yaml"),
            (".txt", "text"),
            (".unknown", "text"),  # Unknown extensions default to text
        ]
        
        for ext, expected_lang in test_cases:
            with tempfile.NamedTemporaryFile(mode="w", suffix=ext, delete=False) as f:
                f.write("test content")
                f.flush()
                
                try:
                    text = f"@{f.name}"
                    expanded = expand_file_refs(text)
                    
                    assert f"```{expected_lang}" in expanded
                    assert "test content" in expanded
                finally:
                    os.unlink(f.name)

    def test_relative_paths(self):
        """Test @ references with relative paths."""
        # Create a temporary directory structure
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            subdir = tmppath / "subdir"
            subdir.mkdir()
            
            # Create a file in the subdirectory
            test_file = subdir / "test.py"
            test_file.write_text("def test():\n    pass")
            
            # Save current directory
            original_cwd = os.getcwd()
            
            try:
                # Change to the temp directory
                os.chdir(tmpdir)
                
                # Test relative path reference
                text = "@subdir/test.py needs review"
                expanded = expand_file_refs(text)
                
                assert "```python" in expanded
                assert "def test():" in expanded
                assert "needs review" in expanded
            finally:
                # Restore original directory
                os.chdir(original_cwd)