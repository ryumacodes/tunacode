"""Test @ file reference integration with files_in_context tracking."""

import os
import tempfile
from pathlib import Path

import pytest

from tunacode.core.state import StateManager
from tunacode.utils.text_utils import expand_file_refs


class TestFileReferenceContextTracking:
    """Test cases for @ file reference context tracking integration."""

    def test_expand_file_refs_tracks_files(self):
        """Test that expand_file_refs returns tracked file paths."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("def test():\n    pass")
            f.flush()
            
            try:
                text = f"Please review @{f.name}"
                expanded, files = expand_file_refs(text)
                
                # Check that file was expanded
                assert "```python" in expanded
                assert "def test():" in expanded
                
                # Check that file path was tracked
                assert len(files) == 1
                assert os.path.abspath(f.name) == files[0]
            finally:
                os.unlink(f.name)

    def test_files_in_context_integration(self):
        """Test that @ file references are added to files_in_context."""
        state_manager = StateManager()
        
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f1, \
             tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False) as f2:
            
            f1.write("# Python code")
            f1.flush()
            
            f2.write("// JavaScript code")
            f2.flush()
            
            try:
                # Initially, files_in_context should be empty
                assert len(state_manager.session.files_in_context) == 0
                
                # Expand file references
                text = f"Review @{f1.name} and @{f2.name}"
                expanded, files = expand_file_refs(text)
                
                # Manually add files to context (simulating what repl.py does)
                for file_path in files:
                    state_manager.session.files_in_context.add(file_path)
                
                # Check that files are tracked
                assert len(state_manager.session.files_in_context) == 2
                assert os.path.abspath(f1.name) in state_manager.session.files_in_context
                assert os.path.abspath(f2.name) in state_manager.session.files_in_context
                
            finally:
                os.unlink(f1.name)
                os.unlink(f2.name)

    def test_absolute_path_consistency(self):
        """Test that relative paths are converted to absolute paths."""
        # Create a temporary directory structure
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            test_file = tmppath / "test.py"
            test_file.write_text("# Test file")
            
            # Save current directory
            original_cwd = os.getcwd()
            
            try:
                # Change to the temp directory
                os.chdir(tmpdir)
                
                # Use relative path
                text = "@test.py"
                expanded, files = expand_file_refs(text)
                
                # Check that absolute path is returned
                assert len(files) == 1
                assert files[0] == str(test_file.resolve())
                assert os.path.isabs(files[0])
                
            finally:
                # Restore original directory
                os.chdir(original_cwd)

    def test_duplicate_file_references(self):
        """Test handling of duplicate @ references to the same file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("# Python file")
            f.flush()
            
            try:
                # Reference the same file multiple times
                text = f"First look at @{f.name}, then check @{f.name} again"
                expanded, files = expand_file_refs(text)
                
                # Files list should contain both occurrences
                assert len(files) == 2
                assert files[0] == files[1]
                assert os.path.abspath(f.name) == files[0]
                
                # When added to a set (like files_in_context), duplicates are removed
                file_set = set(files)
                assert len(file_set) == 1
                
            finally:
                os.unlink(f.name)

    def test_mixed_file_types(self):
        """Test tracking of various file types."""
        test_files = []
        try:
            # Create various file types
            extensions = [".py", ".js", ".md", ".json", ".yaml"]
            for ext in extensions:
                f = tempfile.NamedTemporaryFile(mode="w", suffix=ext, delete=False)
                f.write(f"Content for {ext} file")
                f.flush()
                f.close()
                test_files.append(f.name)
            
            # Create text with all file references
            text = " ".join(f"@{fname}" for fname in test_files)
            expanded, files = expand_file_refs(text)
            
            # Check all files were tracked
            assert len(files) == len(test_files)
            for fname in test_files:
                assert os.path.abspath(fname) in [os.path.abspath(f) for f in files]
            
        finally:
            # Clean up all test files
            for fname in test_files:
                if os.path.exists(fname):
                    os.unlink(fname)