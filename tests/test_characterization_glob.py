"""
Characterization tests for GlobTool.
These tests capture the CURRENT behavior of the tool, including any quirks.
"""
import os
import tempfile
import pytest
from pathlib import Path
from tunacode.tools.glob import glob
from tunacode.exceptions import ToolExecutionError

pytestmark = pytest.mark.asyncio


class TestGlobCharacterization:
    """Golden-master tests for GlobTool behavior."""
    
    def setup_method(self):
        """Create a temporary directory with test file structure."""
        self.temp_dir = tempfile.mkdtemp()
        
        # Create test directory structure
        # Root files
        Path(self.temp_dir, "file1.py").write_text("# Python file 1")
        Path(self.temp_dir, "file2.py").write_text("# Python file 2")
        Path(self.temp_dir, "readme.md").write_text("# README")
        Path(self.temp_dir, ".hidden.txt").write_text("Hidden file")
        
        # Subdirectories
        src_dir = Path(self.temp_dir, "src")
        src_dir.mkdir()
        Path(src_dir, "main.py").write_text("# Main")
        Path(src_dir, "utils.py").write_text("# Utils")
        Path(src_dir, "config.json").write_text("{}")
        
        # Nested subdirectories
        tests_dir = Path(self.temp_dir, "src", "tests")
        tests_dir.mkdir()
        Path(tests_dir, "test_main.py").write_text("# Test main")
        Path(tests_dir, "test_utils.py").write_text("# Test utils")
        Path(tests_dir, "conftest.py").write_text("# Pytest config")
        
        # Another branch
        docs_dir = Path(self.temp_dir, "docs")
        docs_dir.mkdir()
        Path(docs_dir, "api.md").write_text("# API docs")
        Path(docs_dir, "guide.md").write_text("# User guide")
        
        # Build directory (should be excluded by default)
        build_dir = Path(self.temp_dir, "build")
        build_dir.mkdir()
        Path(build_dir, "output.js").write_text("// Built file")
        
        # Node modules (should be excluded by default)
        node_dir = Path(self.temp_dir, "node_modules")
        node_dir.mkdir()
        Path(node_dir, "package.json").write_text("{}")
        
    def teardown_method(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    async def test_glob_simple_pattern(self):
        """Capture behavior with simple glob pattern."""
        # Act
        result = await glob("*.py", directory=self.temp_dir, recursive=False)
        
        # Assert - Golden master
        assert "Found 2 files matching pattern: *.py" in result
        assert "file1.py" in result
        assert "file2.py" in result
        assert "main.py" not in result  # Not in root directory
        assert isinstance(result, str)
    
    async def test_glob_recursive_pattern(self):
        """Capture behavior with recursive glob pattern."""
        # Act
        result = await glob("**/*.py", directory=self.temp_dir)
        
        # Assert - Golden master
        # Note: file1.py and file2.py in root are not found with **/*.py pattern
        # This pattern only matches files in subdirectories
        assert "Found 5 files matching pattern: **/*.py" in result
        assert "main.py" in result
        assert "utils.py" in result
        assert "test_main.py" in result
        assert "test_utils.py" in result
        assert "conftest.py" in result
        # Root files not included with **/*.py
        assert "file1.py" not in result.split("src/")[0]  # Not in root section
        assert "file2.py" not in result.split("src/")[0]  # Not in root section
        # Build directory should be excluded
        assert "output.js" not in result
    
    async def test_glob_multiple_extensions(self):
        """Capture behavior with brace expansion pattern."""
        # Act
        result = await glob("*.{py,md}", directory=self.temp_dir, recursive=False)
        
        # Assert - Golden master
        assert "Found 3 files matching pattern: *.{py,md}" in result
        assert "file1.py" in result
        assert "file2.py" in result
        assert "readme.md" in result
    
    async def test_glob_nested_pattern(self):
        """Capture behavior with specific nested pattern."""
        # Act
        result = await glob("src/**/test_*.py", directory=self.temp_dir)
        
        # Assert - Golden master
        assert "Found 2 files matching pattern: src/**/test_*.py" in result
        assert "test_main.py" in result
        assert "test_utils.py" in result
        assert "conftest.py" not in result  # Doesn't match test_* pattern
    
    async def test_glob_no_matches(self):
        """Capture behavior when no files match pattern."""
        # Act
        result = await glob("*.xyz", directory=self.temp_dir)
        
        # Assert - Golden master
        assert "No files found matching pattern: *.xyz" in result
    
    async def test_glob_hidden_files_excluded(self):
        """Capture behavior with hidden files (default excluded)."""
        # Act
        result = await glob("*.txt", directory=self.temp_dir)
        
        # Assert - Golden master
        assert "No files found matching pattern: *.txt" in result
        assert ".hidden.txt" not in result
    
    async def test_glob_hidden_files_included(self):
        """Capture behavior when including hidden files."""
        # Act
        result = await glob("*.txt", directory=self.temp_dir, include_hidden=True)
        
        # Assert - Golden master
        assert "Found 1 files matching pattern: *.txt" in result
        assert ".hidden.txt" in result
    
    async def test_glob_exclude_directories(self):
        """Capture behavior with default excluded directories."""
        # Act
        result = await glob("**/*.json", directory=self.temp_dir)
        
        # Assert - Golden master
        # config.json should be found, but not package.json in node_modules
        assert "config.json" in result
        assert "package.json" not in result  # In node_modules, excluded
    
    async def test_glob_custom_exclude_dirs(self):
        """Capture behavior with custom excluded directories."""
        # Act
        result = await glob("**/*.md", directory=self.temp_dir, exclude_dirs=["docs"])
        
        # Assert - Golden master
        # Note: **/*.md doesn't match files in root directory
        assert "No files found matching pattern: **/*.md" in result
        # Root readme.md is not matched by **/*.md pattern
    
    async def test_glob_nonexistent_directory(self):
        """Capture behavior with non-existent directory."""
        # Act
        result = await glob("*.py", directory="/path/that/does/not/exist")
        
        # Assert - Golden master
        assert "Error: Directory '/path/that/does/not/exist' does not exist" in result
    
    async def test_glob_file_as_directory(self):
        """Capture behavior when directory parameter is actually a file."""
        # Arrange
        test_file = Path(self.temp_dir, "file1.py")
        
        # Act
        result = await glob("*.py", directory=str(test_file))
        
        # Assert - Golden master
        assert f"Error: '{test_file}' is not a directory" in result
    
    async def test_glob_max_results_limit(self):
        """Capture behavior when results exceed max_results."""
        # Create many files
        many_dir = Path(self.temp_dir, "many")
        many_dir.mkdir()
        for i in range(10):
            Path(many_dir, f"file{i}.txt").write_text(f"File {i}")
        
        # Act with low limit
        result = await glob("**/*.txt", directory=self.temp_dir, max_results=5)
        
        # Assert - Golden master
        assert "Found 5 files matching pattern: **/*.txt" in result
        assert "(Results limited to 5 files)" in result
    
    async def test_glob_output_format(self):
        """Capture the output formatting behavior."""
        # Act
        result = await glob("**/*.py", directory=self.temp_dir)
        
        # Assert - Golden master formatting
        assert "📁" in result  # Directory emoji
        assert "  - " in result  # File indent
        assert "=" * 60 in result  # Separator line
        # Files should be grouped by directory
        lines = result.split("\n")
        # Check that directory headers come before files
        for i, line in enumerate(lines):
            if "📁" in line and i + 1 < len(lines):
                # Next line should be a file (indented with -)
                assert lines[i + 1].strip().startswith("- ") or lines[i + 1].strip() == ""
    
    async def test_glob_permission_denied(self):
        """Capture behavior when directory permissions deny reading."""
        # Skip test if running as root (root can read anything)
        if os.getuid() == 0:
            pytest.skip("Permission tests don't work when running as root")
            
        # Arrange
        protected_dir = Path(self.temp_dir, "protected")
        protected_dir.mkdir()
        Path(protected_dir, "secret.py").write_text("# Secret")
        os.chmod(protected_dir, 0o000)  # Remove all permissions
        
        try:
            # Act - should skip unreadable directories gracefully
            result = await glob("**/*.py", directory=self.temp_dir)
            
            # Assert - Golden master (skips unreadable dirs, no error)
            assert "secret.py" not in result
            assert "Error" not in result  # Should not error, just skip
        finally:
            # Cleanup - restore permissions
            os.chmod(protected_dir, 0o755)
    
    async def test_glob_case_insensitive(self):
        """Capture behavior with case sensitivity."""
        # Create files with different cases
        Path(self.temp_dir, "File.PY").write_text("# Upper case")
        Path(self.temp_dir, "another.Py").write_text("# Mixed case")
        
        # Act
        result = await glob("*.py", directory=self.temp_dir, recursive=False)
        
        # Assert - Golden master (case insensitive matching)
        assert "File.PY" in result
        assert "another.Py" in result
        # Original lowercase files still found
        assert "file1.py" in result
        assert "file2.py" in result
    
    async def test_glob_symlinks(self):
        """Capture behavior with symbolic links."""
        # Create a symlink (if supported)
        try:
            link_target = Path(self.temp_dir, "file1.py")
            link_path = Path(self.temp_dir, "link_to_file.py")
            link_path.symlink_to(link_target)
            
            # Act
            result = await glob("*.py", directory=self.temp_dir, recursive=False)
            
            # Assert - Golden master
            # Current behavior: symlinks are treated as regular files
            assert "file1.py" in result
            assert "file2.py" in result
            # Symlink may or may not be shown depending on OS behavior
        except (OSError, NotImplementedError):
            # Skip if symlinks not supported
            pytest.skip("Symbolic links not supported on this system")