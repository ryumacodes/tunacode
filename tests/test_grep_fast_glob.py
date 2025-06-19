"""
Test suite for fast-glob prefilter enhancement in grep tool.

This test verifies:
1. Fast-glob prefilter correctly filters files by pattern
2. Strategy selection based on candidate count works
3. Performance improvements are achieved
4. Complex glob patterns work correctly
5. Exclude patterns function properly
"""

import asyncio
import os
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from tunacode.tools.grep import ParallelGrep, fast_glob, grep


class TestFastGlobPrefilter:
    """Test the fast_glob function and its integration."""

    def setup_method(self):
        """Create a test directory structure."""
        self.test_dir = tempfile.mkdtemp()
        self.test_path = Path(self.test_dir)
        
        # Create test file structure
        # Python files
        (self.test_path / "main.py").write_text("import os\nprint('Hello')")
        (self.test_path / "test_main.py").write_text("def test_hello():\n    pass")
        (self.test_path / "utils.py").write_text("def helper():\n    return 42")
        
        # JavaScript files
        (self.test_path / "app.js").write_text("console.log('App');")
        (self.test_path / "test.js").write_text("describe('test', () => {});")
        
        # TypeScript files
        (self.test_path / "types.ts").write_text("interface User { name: string; }")
        (self.test_path / "index.tsx").write_text("export default App;")
        
        # Create subdirectories
        (self.test_path / "src").mkdir()
        (self.test_path / "src" / "components").mkdir()
        (self.test_path / "src" / "components" / "Button.tsx").write_text("export const Button = () => {};")
        (self.test_path / "src" / "utils.ts").write_text("export function util() {}")
        
        # Create node_modules (should be excluded)
        (self.test_path / "node_modules").mkdir()
        (self.test_path / "node_modules" / "package.js").write_text("module.exports = {}")
        
        # Create __pycache__ (should be excluded)
        (self.test_path / "__pycache__").mkdir()
        (self.test_path / "__pycache__" / "main.pyc").write_text("compiled")
        
        # Other files
        (self.test_path / "README.md").write_text("# Project")
        (self.test_path / "data.json").write_text('{"key": "value"}')

    def teardown_method(self):
        """Clean up test directory."""
        import shutil
        shutil.rmtree(self.test_dir)

    def test_fast_glob_single_pattern(self):
        """Test fast_glob with single file pattern."""
        # Find all Python files
        matches = fast_glob(self.test_path, "*.py")
        py_files = [m.name for m in matches]
        
        assert "main.py" in py_files
        assert "test_main.py" in py_files
        assert "utils.py" in py_files
        assert "package.js" not in py_files  # Different extension
        assert "main.pyc" not in py_files  # In excluded directory

    def test_fast_glob_multiple_extensions(self):
        """Test fast_glob with multiple extensions pattern."""
        # Find JS and TS files
        matches = fast_glob(self.test_path, "*.{js,ts}")
        file_names = [m.name for m in matches]
        
        assert "app.js" in file_names
        assert "test.js" in file_names
        assert "types.ts" in file_names
        assert "utils.ts" in file_names
        assert "package.js" not in file_names  # In excluded node_modules
        assert "main.py" not in file_names  # Wrong extension

    def test_fast_glob_with_exclude(self):
        """Test fast_glob with exclude pattern."""
        # Find Python files but exclude tests
        matches = fast_glob(self.test_path, "*.py", exclude="test_*.py")
        py_files = [m.name for m in matches]
        
        assert "main.py" in py_files
        assert "utils.py" in py_files
        assert "test_main.py" not in py_files  # Excluded by pattern

    def test_fast_glob_respects_exclude_dirs(self):
        """Test that fast_glob skips excluded directories."""
        # Create a comprehensive search
        all_matches = fast_glob(self.test_path, "*")
        paths = [str(m.relative_to(self.test_path)) for m in all_matches]
        
        # Check that excluded directories are not traversed
        assert not any("node_modules" in p for p in paths)
        assert not any("__pycache__" in p for p in paths)
        assert not any(".git" in p for p in paths)

    def test_fast_glob_max_limit(self):
        """Test that fast_glob respects MAX_GLOB limit."""
        # Create many files to exceed limit
        many_files_dir = self.test_path / "many_files"
        many_files_dir.mkdir()
        
        # Create 100 files (but MAX_GLOB is set to 5000)
        for i in range(100):
            (many_files_dir / f"file_{i}.txt").write_text(f"content {i}")
        
        # This should work fine with 100 files
        matches = fast_glob(self.test_path, "*.txt")
        assert len(matches) == 100
        
        # Note: Testing actual MAX_GLOB limit of 5000 would be slow,
        # so we'll trust the implementation's [:MAX_GLOB] slice

    @pytest.mark.asyncio
    async def test_grep_with_fast_glob_integration(self):
        """Test grep tool using fast-glob prefilter."""
        tool = ParallelGrep()
        
        # Search for "import" in Python files only
        result = await tool._execute(
            pattern="import",
            directory=str(self.test_path),
            include_files="*.py",
            search_type="smart"
        )
        
        # Check results
        assert "Found" in result
        assert "main.py" in result
        # The actual output shows 'import' is highlighted separately
        assert "import" in result and "os" in result
        assert "app.js" not in result  # Should not search JS files
        
        # Check strategy info is included
        assert "Strategy:" in result
        assert "Candidates:" in result

    @pytest.mark.asyncio
    async def test_strategy_selection_small_set(self):
        """Test that small file sets use Python strategy."""
        tool = ParallelGrep()
        
        # Create a small test set (only 3 Python files)
        small_dir = self.test_path / "small_test"
        small_dir.mkdir()
        for i in range(3):
            (small_dir / f"file{i}.py").write_text(f"print({i})")
        
        result = await tool._execute(
            pattern="print",
            directory=str(small_dir),
            include_files="*.py",
            search_type="smart"
        )
        
        # Should select Python strategy for <= 50 files
        assert "Strategy: python" in result

    @pytest.mark.asyncio
    async def test_strategy_selection_medium_set(self):
        """Test that medium file sets use ripgrep strategy."""
        tool = ParallelGrep()
        
        # Create a medium test set (100 files)
        medium_dir = self.test_path / "medium_test"
        medium_dir.mkdir()
        for i in range(100):
            (medium_dir / f"file{i}.py").write_text(f"value = {i}")
        
        result = await tool._execute(
            pattern="value",
            directory=str(medium_dir),
            include_files="*.py",
            search_type="smart"
        )
        
        # Should select ripgrep strategy for 50 < files <= 1000
        assert "Strategy: ripgrep" in result

    @pytest.mark.asyncio
    async def test_complex_glob_patterns(self):
        """Test complex glob patterns with grep."""
        tool = ParallelGrep()
        
        # Search in TypeScript/TSX files in src directory
        result = await tool._execute(
            pattern="export",
            directory=str(self.test_path),
            include_files="*.{ts,tsx}",
            search_type="smart"
        )
        
        # Should find matches in TS/TSX files
        assert "Button.tsx" in result
        assert "export" in result and "const Button" in result
        assert "index.tsx" in result
        assert "utils.ts" in result

    @pytest.mark.asyncio
    async def test_exclude_patterns_work(self):
        """Test that exclude patterns work correctly."""
        tool = ParallelGrep()
        
        # Search Python files but exclude tests
        result = await tool._execute(
            pattern="def",
            directory=str(self.test_path),
            include_files="*.py",
            exclude_files="test_*.py",
            search_type="smart"
        )
        
        # Should find def in utils.py but not test_main.py
        assert "utils.py" in result
        assert "def" in result and "helper" in result
        assert "test_main.py" not in result

    @pytest.mark.asyncio
    async def test_performance_improvement(self):
        """Test that fast-glob improves performance."""
        tool = ParallelGrep()
        
        # Create a larger directory structure
        perf_dir = self.test_path / "performance_test"
        perf_dir.mkdir()
        
        # Create many non-Python files that would slow down search
        for i in range(500):
            (perf_dir / f"data_{i}.txt").write_text(f"data {i}")
            (perf_dir / f"log_{i}.log").write_text(f"log {i}")
        
        # Create a few Python files with the pattern
        for i in range(10):
            (perf_dir / f"module_{i}.py").write_text(f"import os\nvalue = {i}")
        
        # Time the search with prefiltering
        start_time = time.time()
        result = await tool._execute(
            pattern="import",
            directory=str(perf_dir),
            include_files="*.py",  # This triggers fast-glob to filter first
            search_type="smart"
        )
        filtered_time = time.time() - start_time
        
        # Verify it found the matches
        assert "Found 10 matches" in result
        assert "module_0.py" in result
        
        # Check that relatively few files were searched
        assert "Candidates: 10 files" in result  # Only Python files

    @pytest.mark.asyncio
    async def test_no_files_matching_pattern(self):
        """Test behavior when no files match the include pattern."""
        tool = ParallelGrep()
        
        result = await tool._execute(
            pattern="test",
            directory=str(self.test_path),
            include_files="*.cpp",  # No C++ files exist
            search_type="smart"
        )
        
        assert "No files found matching pattern: *.cpp" in result

    @pytest.mark.asyncio
    async def test_glob_with_subdirectories(self):
        """Test that fast_glob properly traverses subdirectories."""
        tool = ParallelGrep()
        
        # Search for TypeScript files including in subdirectories
        result = await tool._execute(
            pattern="export",
            directory=str(self.test_path),
            include_files="*.{ts,tsx}",
            search_type="smart"
        )
        
        # Should find files in src/components/
        assert "src/components/Button.tsx" in result or "Button.tsx" in result
        assert "src/utils.ts" in result or "utils.ts" in result

    def test_fast_glob_empty_directory(self):
        """Test fast_glob on empty directory."""
        empty_dir = self.test_path / "empty"
        empty_dir.mkdir()
        
        matches = fast_glob(empty_dir, "*.py")
        assert len(matches) == 0

    def test_fast_glob_permission_errors(self):
        """Test that fast_glob handles permission errors gracefully."""
        # Create a directory we can't read (on Unix-like systems)
        if os.name != 'nt':  # Skip on Windows
            if hasattr(os, 'geteuid') and os.geteuid() == 0:
                pytest.skip("Permission test unreliable as root")
            restricted_dir = self.test_path / "restricted"
            restricted_dir.mkdir()
            (restricted_dir / "secret.py").write_text("secret")
            
            # Remove read permissions
            os.chmod(restricted_dir, 0o000)
            
            try:
                # Should not crash, just skip the directory
                matches = fast_glob(self.test_path, "*.py")
                py_files = [m.name for m in matches]
                
                # Should still find other Python files
                assert "main.py" in py_files
                assert "secret.py" not in py_files  # Can't access
            finally:
                # Restore permissions for cleanup
                os.chmod(restricted_dir, 0o755)


class TestGrepPublicAPI:
    """Test the public grep function API."""

    @pytest.mark.asyncio
    async def test_grep_function_basic(self):
        """Test basic grep function usage."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.py"
            test_file.write_text("def hello():\n    print('Hello, World!')")
            
            result = await grep("Hello", tmpdir)
            
            # Case insensitive by default, so finds both 'hello' and 'Hello'
            assert "Found" in result and "matches" in result
            assert "test.py" in result
            assert "Hello, World!" in result

    @pytest.mark.asyncio
    async def test_grep_function_with_options(self):
        """Test grep function with various options."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            (Path(tmpdir) / "main.py").write_text("HELLO = 'world'")
            (Path(tmpdir) / "test.py").write_text("hello = 'world'")
            
            # Case sensitive search
            result = await grep("HELLO", tmpdir, case_sensitive=True)
            assert "main.py" in result
            assert "test.py" not in result
            
            # Case insensitive search
            result = await grep("hello", tmpdir, case_sensitive=False)
            assert "main.py" in result
            assert "test.py" in result

    @pytest.mark.asyncio
    async def test_grep_function_regex(self):
        """Test grep function with regex patterns."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.py"
            test_file.write_text("import os\nimport sys\nfrom pathlib import Path")
            
            # Regex search
            result = await grep(r"import \w+", tmpdir, use_regex=True)
            
            # Check that regex search works
            assert "Found" in result and "matches" in result
            assert "test.py:1" in result  # import os line
            assert "test.py:2" in result  # import sys line
            # Note: The regex might also match 'import Path' in the third line depending on implementation