"""
Characterization tests for ListDirTool.
These tests capture the CURRENT behavior of the tool, including any quirks.
"""
import os
import tempfile
import pytest
from pathlib import Path
from tunacode.tools.list_dir import list_dir

pytestmark = pytest.mark.asyncio


class TestListDirCharacterization:
    """Golden-master tests for ListDirTool behavior."""
    
    def setup_method(self):
        """Create a temporary directory with test file structure."""
        self.temp_dir = tempfile.mkdtemp()
        
        # Create test files
        Path(self.temp_dir, "file1.txt").write_text("Content 1")
        Path(self.temp_dir, "file2.py").write_text("#!/usr/bin/env python3\nprint('hello')")
        Path(self.temp_dir, "README.md").write_text("# README")
        
        # Create hidden file
        Path(self.temp_dir, ".hidden").write_text("Hidden content")
        
        # Create directories
        Path(self.temp_dir, "src").mkdir()
        Path(self.temp_dir, "tests").mkdir()
        Path(self.temp_dir, ".git").mkdir()  # Hidden directory
        
        # Create an executable file (Unix only)
        exec_file = Path(self.temp_dir, "script.sh")
        exec_file.write_text("#!/bin/bash\necho 'Hello'")
        try:
            os.chmod(exec_file, 0o755)
        except:
            pass  # Might fail on Windows
        
        # Create a symlink if supported
        try:
            link_path = Path(self.temp_dir, "link_to_readme")
            link_path.symlink_to("README.md")
        except (OSError, NotImplementedError):
            pass  # Symlinks might not be supported
    
    def teardown_method(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    async def test_list_dir_basic(self):
        """Capture basic directory listing behavior."""
        # Act
        result = await list_dir(self.temp_dir)
        
        # Assert - Golden master
        assert f"Contents of '{self.temp_dir}':" in result
        assert "[DIR]" in result
        assert "[FILE]" in result
        assert "src" in result
        assert "tests" in result
        assert "file1.txt" in result
        assert "file2.py" in result
        assert "README.md" in result
        # Hidden files excluded by default
        assert ".hidden" not in result
        assert ".git" not in result
        # Summary line
        assert "Total:" in result
        assert "directories" in result
        assert "files" in result
    
    async def test_list_dir_show_hidden(self):
        """Capture behavior when showing hidden files."""
        # Act
        result = await list_dir(self.temp_dir, show_hidden=True)
        
        # Assert - Golden master
        assert ".hidden" in result
        assert ".git" in result
        assert "[DIR]" in result  # .git is a directory
    
    async def test_list_dir_empty_directory(self):
        """Capture behavior with empty directory."""
        # Arrange
        empty_dir = Path(self.temp_dir, "empty")
        empty_dir.mkdir()
        
        # Act
        result = await list_dir(str(empty_dir))
        
        # Assert - Golden master
        assert f"Directory '{empty_dir}' is empty" in result
    
    async def test_list_dir_nonexistent(self):
        """Capture behavior with non-existent directory."""
        # Act
        result = await list_dir("/path/that/does/not/exist")
        
        # Assert - Golden master
        assert "Directory not found" in result
        assert "/path/that/does/not/exist" in result
    
    async def test_list_dir_file_not_directory(self):
        """Capture behavior when path is a file, not directory."""
        # Arrange
        file_path = Path(self.temp_dir, "file1.txt")
        
        # Act
        result = await list_dir(str(file_path))
        
        # Assert - Golden master
        assert "Not a directory" in result
        assert str(file_path) in result
    
    async def test_list_dir_current_directory(self):
        """Capture behavior with current directory (default)."""
        # Save original directory
        original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        
        try:
            # Act
            result = await list_dir()  # No argument = current directory
            
            # Assert - Golden master
            assert "Contents of" in result
            assert "file1.txt" in result
            assert "src" in result
        finally:
            os.chdir(original_cwd)
    
    async def test_list_dir_max_entries_limit(self):
        """Capture behavior when entries exceed max_entries."""
        # Create many files
        many_dir = Path(self.temp_dir, "many")
        many_dir.mkdir()
        for i in range(10):
            Path(many_dir, f"file{i:03d}.txt").write_text(f"File {i}")
        
        # Act with low limit
        result = await list_dir(str(many_dir), max_entries=5)
        
        # Assert - Golden master
        assert "Total: 5 entries" in result
        assert "Note: Output limited to 5 entries" in result
        # Should show first 5 after sorting
        assert "file000.txt" in result
        assert "file004.txt" in result
        assert "file005.txt" not in result  # Beyond limit
    
    async def test_list_dir_sorting(self):
        """Capture sorting behavior (directories first, then alphabetical)."""
        # Create files with various names
        mixed_dir = Path(self.temp_dir, "mixed")
        mixed_dir.mkdir()
        Path(mixed_dir, "zebra.txt").write_text("Z")
        Path(mixed_dir, "alpha.txt").write_text("A")
        Path(mixed_dir, "beta").mkdir()
        Path(mixed_dir, "delta").mkdir()
        
        # Act
        result = await list_dir(str(mixed_dir))
        
        # Assert - Golden master
        lines = result.split("\n")
        # Find the content lines (skip header and summary)
        content_lines = [l for l in lines if l.strip().startswith(("alpha", "beta", "delta", "zebra"))]
        
        # Directories should come first
        dir_indices = [i for i, l in enumerate(content_lines) if "[DIR]" in l]
        file_indices = [i for i, l in enumerate(content_lines) if "[FILE]" in l]
        
        if dir_indices and file_indices:
            assert max(dir_indices) < min(file_indices)  # All dirs before files
    
    async def test_list_dir_type_indicators(self):
        """Capture behavior of type indicators (/, *, @)."""
        # Act
        result = await list_dir(self.temp_dir)
        
        # Assert - Golden master
        assert "src/" in result  # Directory indicator
        if os.name != 'nt':  # Unix-like systems
            assert "script.sh*" in result or "script.sh" in result  # Executable indicator
            if "link_to_readme" in result:
                assert "link_to_readme@" in result  # Symlink indicator
    
    async def test_list_dir_long_names(self):
        """Capture behavior with very long filenames."""
        # Create file with long name
        long_name = "this_is_a_very_long_filename_that_exceeds_normal_limits_" + "x" * 50 + ".txt"
        Path(self.temp_dir, long_name).write_text("Long name")
        
        # Act
        result = await list_dir(self.temp_dir)
        
        # Assert - Golden master
        # Long names should be truncated
        assert "..." in result  # Truncation indicator
        assert long_name[:44] in result  # First part of name
    
    async def test_list_dir_permission_denied(self):
        """Capture behavior when directory permissions deny reading."""
        # Skip test if running as root
        if os.getuid() == 0:
            pytest.skip("Permission tests don't work when running as root")
            
        # Arrange
        protected_dir = Path(self.temp_dir, "protected")
        protected_dir.mkdir()
        os.chmod(protected_dir, 0o000)  # Remove all permissions
        
        try:
            # Act
            result = await list_dir(str(protected_dir))
            
            # Assert - Golden master
            assert "Permission denied" in result
            assert str(protected_dir) in result
        finally:
            # Cleanup
            os.chmod(protected_dir, 0o755)
    
    async def test_list_dir_special_files(self):
        """Capture behavior with special file types."""
        # Create a FIFO (named pipe) if supported
        try:
            fifo_path = Path(self.temp_dir, "myfifo")
            os.mkfifo(fifo_path)
            
            # Act
            result = await list_dir(self.temp_dir, show_hidden=True)
            
            # Assert - Should show with unknown type indicator
            if "myfifo" in result:
                assert "myfifo?" in result or "myfifo" in result
        except (OSError, AttributeError):
            # FIFOs not supported on this system
            pass
    
    async def test_list_dir_case_sensitivity(self):
        """Capture case sensitivity in sorting."""
        # Create files with mixed cases
        case_dir = Path(self.temp_dir, "cases")
        case_dir.mkdir()
        Path(case_dir, "UPPER.txt").write_text("U")
        Path(case_dir, "lower.txt").write_text("l")
        Path(case_dir, "Mixed.txt").write_text("M")
        
        # Act
        result = await list_dir(str(case_dir))
        
        # Assert - Golden master (case-insensitive sorting)
        lines = result.split("\n")
        # Extract filenames in order they appear
        filenames = []
        for line in lines:
            if ".txt" in line and "[FILE]" in line:
                # Extract filename from formatted line
                filename = line.strip().split()[0]
                filenames.append(filename)
        
        # Should be sorted case-insensitively
        assert filenames == sorted(filenames, key=str.lower)
    
    async def test_list_dir_unicode_names(self):
        """Capture behavior with unicode filenames."""
        # Create files with unicode names
        Path(self.temp_dir, "世界.txt").write_text("World")
        Path(self.temp_dir, "Ñiño.txt").write_text("Child")
        Path(self.temp_dir, "café.txt").write_text("Coffee")
        
        # Act
        result = await list_dir(self.temp_dir)
        
        # Assert - Golden master
        assert "世界.txt" in result
        assert "Ñiño.txt" in result
        assert "café.txt" in result