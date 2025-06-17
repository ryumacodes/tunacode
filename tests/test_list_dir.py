"""Tests for the list_dir tool."""

import os
import tempfile
from pathlib import Path

import pytest

from tunacode.tools.list_dir import ListDirTool, list_dir


@pytest.mark.asyncio
async def test_list_empty_directory():
    """Test listing an empty directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        result = await list_dir(tmpdir)
        assert f"Directory '{tmpdir}' is empty" in result


@pytest.mark.asyncio
async def test_list_directory_with_files():
    """Test listing a directory with files and subdirectories."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create some test files and directories
        Path(tmpdir, "file1.txt").touch()
        Path(tmpdir, "file2.py").touch()
        Path(tmpdir, ".hidden").touch()
        
        subdir = Path(tmpdir, "subdir")
        subdir.mkdir()
        Path(subdir, "nested.txt").touch()
        
        # Test without hidden files
        result = await list_dir(tmpdir)
        
        # Check output contains expected elements
        assert f"Contents of '{tmpdir}':" in result
        assert "file1.txt" in result
        assert "file2.py" in result
        assert "subdir/" in result  # Directory indicator
        assert ".hidden" not in result  # Hidden file should not appear
        assert "[FILE]" in result
        assert "[DIR]" in result
        assert "Total: 3 entries (1 directories, 2 files)" in result


@pytest.mark.asyncio
async def test_list_directory_with_hidden_files():
    """Test listing a directory including hidden files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test files
        Path(tmpdir, "visible.txt").touch()
        Path(tmpdir, ".hidden").touch()
        
        # Test with hidden files
        result = await list_dir(tmpdir, show_hidden=True)
        
        assert "visible.txt" in result
        assert ".hidden" in result


@pytest.mark.asyncio
async def test_list_directory_max_entries():
    """Test listing a directory with max_entries limit."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create many files
        for i in range(10):
            Path(tmpdir, f"file{i:02d}.txt").touch()
        
        # Test with limit
        result = await list_dir(tmpdir, max_entries=5)
        
        # Should only show 5 entries
        assert "Total: 5 entries" in result
        assert "Note: Output limited to 5 entries" in result
        
        # Check files are sorted
        assert "file00.txt" in result
        assert "file01.txt" in result
        assert "file09.txt" not in result  # Should be cut off


@pytest.mark.asyncio
async def test_list_nonexistent_directory():
    """Test listing a non-existent directory."""
    result = await list_dir("/nonexistent/path/that/should/not/exist")
    assert "Directory not found" in result


@pytest.mark.asyncio
async def test_list_file_instead_of_directory():
    """Test listing a file instead of a directory."""
    with tempfile.NamedTemporaryFile(delete=False) as tmpfile:
        try:
            result = await list_dir(tmpfile.name)
            assert "Not a directory" in result
        finally:
            os.unlink(tmpfile.name)


@pytest.mark.asyncio
async def test_list_current_directory():
    """Test listing current directory (default behavior)."""
    result = await list_dir()
    assert "Contents of" in result
    # Should contain at least this test file
    assert "test_list_dir.py" in result or "tests" in result


@pytest.mark.asyncio
async def test_list_directory_with_symlinks():
    """Test listing a directory with symlinks."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a file and directory
        file_path = Path(tmpdir, "original.txt")
        file_path.touch()
        
        dir_path = Path(tmpdir, "original_dir")
        dir_path.mkdir()
        
        # Create symlinks
        link_to_file = Path(tmpdir, "link_to_file")
        link_to_file.symlink_to(file_path)
        
        link_to_dir = Path(tmpdir, "link_to_dir")
        link_to_dir.symlink_to(dir_path)
        
        result = await list_dir(tmpdir)
        
        # Check symlinks are indicated
        assert "link_to_file@" in result
        assert "link_to_dir@" in result


@pytest.mark.asyncio
async def test_list_directory_executable_files():
    """Test listing a directory with executable files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create an executable file
        exec_file = Path(tmpdir, "script.sh")
        exec_file.touch()
        exec_file.chmod(0o755)
        
        # Create regular file
        regular_file = Path(tmpdir, "regular.txt")
        regular_file.touch()
        
        result = await list_dir(tmpdir)
        
        # On Unix systems, executable should be marked
        if os.name != 'nt':  # Not Windows
            assert "script.sh*" in result


@pytest.mark.asyncio
async def test_tool_with_ui_logger():
    """Test ListDirTool with UI logger."""
    class MockUILogger:
        def __init__(self):
            self.messages = []
        
        async def info(self, message: str):
            self.messages.append(("info", message))
        
        async def error(self, message: str):
            self.messages.append(("error", message))
        
        async def warning(self, message: str):
            self.messages.append(("warning", message))
        
        async def debug(self, message: str):
            self.messages.append(("debug", message))
        
        async def success(self, message: str):
            self.messages.append(("success", message))
    
    ui = MockUILogger()
    tool = ListDirTool(ui)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        Path(tmpdir, "test.txt").touch()
        await tool.execute(tmpdir)
        
        # Check UI logging occurred
        assert len(ui.messages) > 0
        assert ui.messages[0][0] == "info"
        assert "ListDir" in ui.messages[0][1]