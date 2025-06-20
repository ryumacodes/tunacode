"""
Edge case tests for file operations.
Tests platform-specific cases, permissions, and unusual scenarios.
"""
import os
import sys
import tempfile
import pytest
from pathlib import Path
from tunacode.tools.glob import glob
from tunacode.tools.grep import grep
from tunacode.tools.read_file import read_file
from tunacode.tools.write_file import write_file
from tunacode.tools.update_file import update_file
from tunacode.tools.list_dir import list_dir
from pydantic_ai import ModelRetry

pytestmark = pytest.mark.asyncio


class TestFileOperationsEdgeCases:
    """Edge case tests for file operations."""
    
    def setup_method(self):
        """Create a temporary directory for test files."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
    
    def teardown_method(self):
        """Clean up temporary files."""
        os.chdir(self.original_cwd)
        import shutil
        shutil.rmtree(self.temp_dir)
    
    @pytest.mark.skipif(sys.platform != "win32", reason="Windows-specific test")
    async def test_windows_path_handling(self):
        """Test handling of Windows-specific paths."""
        # Test backslash paths
        Path("subdir").mkdir()
        await write_file("subdir\\windows_file.txt", "Windows path content")
        
        # Should work with forward slashes too
        content = await read_file("subdir/windows_file.txt")
        assert content == "Windows path content"
        
        # Test drive letter paths (if on Windows)
        import string
        for letter in string.ascii_uppercase:
            drive = f"{letter}:"
            if Path(drive).exists():
                # Test absolute path with drive letter
                temp_file = Path(drive) / "temp_test.txt"
                try:
                    if temp_file.parent.exists() and os.access(temp_file.parent, os.W_OK):
                        await write_file(str(temp_file), "Drive letter test")
                        content = await read_file(str(temp_file))
                        assert content == "Drive letter test"
                        temp_file.unlink()
                        break
                except Exception:
                    pass
    
    @pytest.mark.skipif(sys.platform == "win32", reason="Unix-specific test")
    async def test_unix_specific_paths(self):
        """Test Unix-specific path handling."""
        # Test paths with special characters
        special_paths = [
            "file with spaces.txt",
            "file-with-dashes.txt",
            "file.with.dots.txt",
            "file@with#special$chars.txt",
            "file(with)parens.txt",
            "file[with]brackets.txt"
        ]
        
        for path in special_paths:
            await write_file(path, f"Content for {path}")
            content = await read_file(path)
            assert content == f"Content for {path}"
        
        # Test searching for these files
        all_files = await glob("file*")
        assert len(all_files) == len(special_paths)
    
    async def test_case_sensitivity(self):
        """Test file operations with case sensitivity."""
        # Create files with different cases
        await write_file("lowercase.txt", "lowercase content")
        await write_file("UPPERCASE.TXT", "uppercase content")
        await write_file("MixedCase.Txt", "mixed case content")
        
        # Test reading with different cases
        if sys.platform == "win32" or sys.platform == "darwin":
            # Case-insensitive filesystems
            content = await read_file("LOWERCASE.txt")
            assert "content" in content.lower()
        else:
            # Case-sensitive filesystems
            result = await read_file("LOWERCASE.txt")
            assert "File not found" in result
        
        # Test glob with case patterns
        lower_files = await glob("lowercase.*")
        upper_files = await glob("UPPERCASE.*")
        
        assert len(lower_files) >= 1
        assert len(upper_files) >= 1
    
    async def test_file_locking_scenarios(self):
        """Test behavior with locked files."""
        # Create a file
        test_file = "locked_file.txt"
        await write_file(test_file, "Initial content")
        
        # Simulate file locking (platform-specific)
        if sys.platform == "win32":
            # On Windows, opening file in write mode locks it
            try:
                with open(test_file, 'r+') as f:
                    # File is now locked for writing
                    # Try to update it
                    with pytest.raises(Exception):
                        await update_file(test_file, target="Initial", patch="Updated")
            except Exception:
                # Some operations might not be supported
                pytest.skip("File locking test not supported on this system")
        else:
            # On Unix, we can use file locking
            import fcntl
            try:
                with open(test_file, 'r+') as f:
                    fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    # Try to read (should work)
                    content = await read_file(test_file)
                    assert "Initial content" in content
            except Exception:
                pytest.skip("File locking test not supported on this system")
    
    async def test_permission_edge_cases(self):
        """Test various permission scenarios."""
        if os.getuid() == 0:
            pytest.skip("Permission tests don't work when running as root")
        
        # Create files with different permissions
        test_cases = [
            ("readonly.txt", 0o444),      # Read-only
            ("writeonly.txt", 0o222),     # Write-only (unusual)
            ("noread.txt", 0o000),        # No permissions
            ("executable.txt", 0o755),    # Executable
        ]
        
        for filename, mode in test_cases:
            await write_file(filename, "Test content")
            os.chmod(filename, mode)
        
        # Test read-only file
        content = await read_file("readonly.txt")
        assert content == "Test content"
        
        with pytest.raises(ModelRetry):
            await update_file("readonly.txt", target="Test", patch="Updated")
        
        # Test no-permission file
        result = await read_file("noread.txt")
        assert "permission" in result.lower() or "error" in result.lower()
        
        # Cleanup - restore permissions
        for filename, _ in test_cases:
            try:
                os.chmod(filename, 0o644)
            except Exception:
                pass
    
    async def test_symlink_edge_cases(self):
        """Test symbolic link handling."""
        if sys.platform == "win32" and not os.environ.get("CI"):
            pytest.skip("Symlink creation may require admin rights on Windows")
        
        # Create a regular file
        await write_file("target.txt", "Target content")
        
        # Create symlinks
        try:
            Path("link_to_file.txt").symlink_to("target.txt")
            Path("link_to_nonexistent.txt").symlink_to("nonexistent.txt")
            
            # Test reading through symlink
            content = await read_file("link_to_file.txt")
            assert content == "Target content"
            
            # Test reading broken symlink
            result = await read_file("link_to_nonexistent.txt")
            assert "not found" in result.lower() or "error" in result.lower()
            
            # Test listing with symlinks
            items = await list_dir(".")
            symlink_items = [item for item in items if "@" in item]
            assert len(symlink_items) >= 2  # Should show symlink indicator
            
            # Test glob with symlinks
            all_links = await glob("link_*.txt")
            assert len(all_links) == 2
        except OSError:
            pytest.skip("Symlink creation not supported")
    
    async def test_special_filenames(self):
        """Test handling of special filenames."""
        special_names = [
            ".hidden",                    # Hidden file
            "..dots",                     # Starts with dots
            "file.",                      # Ends with dot
            "-file",                      # Starts with dash
            "file-",                      # Ends with dash
            "file name with spaces",      # Spaces
            "file\ttab",                  # Tab character
            "very_long_filename_" + "x" * 200,  # Very long name
        ]
        
        if sys.platform != "win32":
            # Unix allows more special characters
            special_names.extend([
                "file\nwith\nnewlines",   # Newlines (might fail)
                "file*with*asterisks",    # Asterisks
                "file?with?questions",    # Question marks
            ])
        
        for name in special_names:
            try:
                await write_file(name, f"Content for special file: {repr(name)}")
                content = await read_file(name)
                assert "Content for special file" in content
            except Exception as e:
                # Some names might not be supported on certain filesystems
                print(f"Special filename '{repr(name)}' not supported: {e}")
    
    async def test_empty_directory_edge_cases(self):
        """Test edge cases with empty directories."""
        # Create empty directory
        Path("empty_dir").mkdir()
        
        # List empty directory
        items = await list_dir("empty_dir")
        assert len(items) == 0
        
        # Search in empty directory
        files = await glob("empty_dir/*")
        assert len(files) == 0
        
        # Grep in empty directory
        matches = await grep("pattern", path="empty_dir", return_format="list")
        assert len(matches) == 0
        
        # Create nested empty directories
        Path("empty_dir/nested/deeply/empty").mkdir(parents=True)
        
        # Search recursively in empty tree
        all_files = await glob("empty_dir/**/*")
        assert all(Path(f).is_dir() or not Path(f).exists() for f in all_files)
    
    async def test_concurrent_file_modifications(self):
        """Test handling of concurrent file modifications."""
        # Create initial file
        filename = "concurrent_test.txt"
        await write_file(filename, "Line 1\nLine 2\nLine 3")
        
        # Simulate concurrent modification scenario
        # First read
        content1 = await read_file(filename)
        
        # External modification (simulated)
        Path(filename).write_text("Line 1\nModified Line 2\nLine 3")
        
        # Try to update based on old content
        with pytest.raises(ModelRetry) as exc_info:
            await update_file(filename, target="Line 2", patch="Updated Line 2")
        
        # The target "Line 2" no longer exists
        assert "not found" in str(exc_info.value)
        
        # Read current content
        current = await read_file(filename)
        assert "Modified Line 2" in current
    
    async def test_binary_file_edge_cases(self):
        """Test handling of binary files."""
        # Create binary file with various byte patterns
        binary_data = bytes(range(256))  # All possible bytes
        Path("binary_test.bin").write_bytes(binary_data)
        
        # Try to read as text (should fail gracefully)
        result = await read_file("binary_test.bin")
        assert "decode" in result.lower() or "binary" in result.lower()
        
        # Create file with null bytes
        null_content = "Before\x00Null\x00After"
        await write_file("null_bytes.txt", null_content)
        
        # Read file with null bytes
        content = await read_file("null_bytes.txt")
        assert "\x00" in content  # Should preserve null bytes
        
        # Search in file with null bytes
        matches = await grep("Null", include_files="null_bytes.txt", return_format="list")
        assert len(matches) == 1
    
    async def test_filesystem_limits(self):
        """Test behavior at filesystem limits."""
        # Test maximum path length (varies by OS)
        if sys.platform == "win32":
            max_path = 260
        else:
            max_path = 4096
        
        # Create path approaching the limit
        deep_path = "a/" * (max_path // 4 - 10)  # Leave some room
        try:
            Path(deep_path).mkdir(parents=True, exist_ok=True)
            test_file = deep_path + "test.txt"
            
            await write_file(test_file, "Deep path content")
            content = await read_file(test_file)
            assert content == "Deep path content"
        except OSError as e:
            # Hit filesystem limit
            assert "too long" in str(e).lower() or "name too long" in str(e).lower()
        
        # Test maximum filename length
        if sys.platform == "win32":
            max_filename = 255
        else:
            max_filename = 255
        
        long_name = "x" * (max_filename - 4) + ".txt"
        try:
            await write_file(long_name, "Long filename content")
            assert Path(long_name).exists()
        except OSError:
            # Filename too long
            pass
    
    async def test_special_file_types(self):
        """Test handling of special file types (FIFOs, devices, etc.)."""
        if sys.platform == "win32":
            pytest.skip("Special file types test not applicable on Windows")
        
        # Try to create and handle a FIFO (named pipe)
        try:
            os.mkfifo("test_fifo")
            
            # List should show it
            items = await list_dir(".")
            assert any("test_fifo" in item for item in items)
            
            # Try to read (should fail gracefully)
            result = await read_file("test_fifo")
            assert "error" in result.lower() or "timeout" in result.lower()
            
            os.remove("test_fifo")
        except OSError:
            # FIFO creation not supported
            pass
    
    async def test_encoding_edge_cases(self):
        """Test file operations with various encodings."""
        # Create files with different encodings
        test_cases = [
            ("utf8.txt", "UTF-8 content: 你好世界 🌍", "utf-8"),
            ("latin1.txt", "Latin-1: café señor", "latin-1"),
            ("utf16.txt", "UTF-16: Hello 世界", "utf-16"),
        ]
        
        for filename, content, encoding in test_cases:
            # Write with specific encoding
            Path(filename).write_text(content, encoding=encoding)
            
            # Read with our tool (assumes UTF-8)
            if encoding == "utf-8":
                result = await read_file(filename)
                assert content in result
            else:
                # Non-UTF-8 files might fail
                result = await read_file(filename)
                # Should either decode with errors or return error message
                assert isinstance(result, str)