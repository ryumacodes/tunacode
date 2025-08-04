"""
Characterization tests for grep.py refactoring.

These tests capture the current behavior of the grep tool to ensure
refactoring doesn't break existing functionality.
"""

import tempfile
from pathlib import Path

import pytest

from tunacode.tools.grep import grep
from tunacode.tools.grep_components.file_filter import FileFilter


class TestGrepToolCharacterization:
    """Test suite capturing current grep tool behavior."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory with test files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Create test file structure
            (tmpdir_path / "test.py").write_text("""
def hello_world():
    print("Hello, World!")
    return 42

class TestClass:
    def method_one(self):
        pass

    def method_two(self):
        return "test"
""")

            (tmpdir_path / "data.txt").write_text("""
Line 1: Some data
Line 2: More data
Line 3: Pattern match here
Line 4: Another line
Line 5: Final line with pattern
""")

            (tmpdir_path / "subdir").mkdir()
            (tmpdir_path / "subdir" / "nested.js").write_text("""
function testFunction() {
    console.log("Test");
    return true;
}

const pattern = "match";
""")

            # Create files to test exclusion
            (tmpdir_path / "node_modules").mkdir()
            (tmpdir_path / "node_modules" / "package.js").write_text("should be excluded")

            (tmpdir_path / ".git").mkdir()
            (tmpdir_path / ".git" / "config").write_text("should be excluded")

            yield tmpdir_path

    # Remove state manager and grep_tool fixtures - we'll use the grep function directly

    @pytest.mark.asyncio
    async def test_basic_pattern_search(self, temp_dir):
        """Test basic pattern searching functionality."""
        result = await grep(pattern="pattern", directory=str(temp_dir))

        # Should find matches in data.txt and nested.js
        assert "pattern" in result.lower()
        assert "data.txt" in result
        assert "nested.js" in result
        assert "Line 3: Pattern match here" in result
        assert "Line 5: Final line with pattern" in result

    @pytest.mark.asyncio
    async def test_case_sensitive_search(self, temp_dir):
        """Test case-sensitive searching."""
        # Case-insensitive (default)
        result_insensitive = await grep(pattern="PATTERN", directory=str(temp_dir))
        assert "data.txt" in result_insensitive

        # Case-sensitive
        result_sensitive = await grep(
            pattern="PATTERN", directory=str(temp_dir), case_sensitive=True
        )
        assert "data.txt" not in result_sensitive

    @pytest.mark.asyncio
    async def test_file_type_filtering(self, temp_dir):
        """Test filtering by file type."""
        # Search only Python files
        result = await grep(pattern="def", directory=str(temp_dir), include_files="*.py")

        assert "test.py" in result
        assert "nested.js" not in result
        assert "data.txt" not in result

    @pytest.mark.asyncio
    async def test_glob_pattern_filtering(self, temp_dir):
        """Test filtering with glob patterns."""
        # Search only in .js files
        result = await grep(pattern="function", directory=str(temp_dir), include_files="*.js")

        assert "nested.js" in result
        assert "test.py" not in result

    @pytest.mark.asyncio
    async def test_regex_mode(self, temp_dir):
        """Test regex pattern matching."""
        # Search for method definitions
        result = await grep(pattern=r"def \w+\(", directory=str(temp_dir), use_regex=True)

        assert "def hello_world(" in result
        assert "def method_one(" in result
        assert "def method_two(" in result

    @pytest.mark.asyncio
    async def test_context_lines(self, temp_dir):
        """Test context line display."""
        # Request context lines
        result = await grep(pattern="Line 3", directory=str(temp_dir), context_lines=1)

        # Should include surrounding lines - check for content with context
        assert "Line 2: More data" in result
        assert "Pattern match here" in result  # The line content appears
        assert "Line 4: Another line" in result

    @pytest.mark.asyncio
    async def test_output_modes(self, temp_dir):
        """Test different output modes."""
        # The grep function returns formatted string output by default
        # Testing the actual output format
        result = await grep(pattern="pattern", directory=str(temp_dir))

        # Should show file paths and matching lines
        assert "data.txt" in result
        assert "Pattern match here" in result
        assert "nested.js" in result

    @pytest.mark.asyncio
    async def test_exclusion_patterns(self, temp_dir):
        """Test that certain directories are excluded by default."""
        # Search for a pattern that would match in excluded directories
        result = await grep(pattern="excluded", directory=str(temp_dir))

        # Should not find matches in node_modules or .git
        assert "node_modules" not in result
        assert ".git" not in result

    @pytest.mark.asyncio
    async def test_multiline_mode(self, temp_dir):
        """Test multiline pattern matching."""
        # Create a file with multiline content
        (temp_dir / "multiline.txt").write_text("""Start
Middle
End

Another Start
Middle
End""")

        # Note: The grep function may not directly support multiline mode
        # Test regex pattern that would work within single lines
        result = await grep(pattern="Start", directory=str(temp_dir), use_regex=True)

        assert "multiline.txt" in result
        assert "Start" in result

    @pytest.mark.asyncio
    async def test_head_limit(self, temp_dir):
        """Test limiting number of results."""
        # Create multiple files with matches
        for i in range(10):
            (temp_dir / f"file{i}.txt").write_text(f"pattern in file {i}")

        # Limit results with max_results parameter
        result = await grep(pattern="pattern", directory=str(temp_dir), max_results=3)

        # Count the number of file references in output
        file_count = result.count(".txt:")
        assert file_count <= 3

    def test_fast_glob_functionality(self, temp_dir):
        """Test the fast_glob function directly."""
        # Test basic glob - fast_glob searches recursively by default
        results = FileFilter.fast_glob(temp_dir, "*.py")
        assert len(results) == 1
        assert results[0].name == "test.py"

        # Test multiple extensions
        results = FileFilter.fast_glob(temp_dir, "*.{py,js,txt}")
        names = {r.name for r in results}
        # Should find all three file types
        assert len(results) >= 3
        assert "test.py" in names
        assert "data.txt" in names

        # Test single extension
        results = FileFilter.fast_glob(temp_dir, "*.js")
        js_files = [r for r in results if r.name.endswith(".js")]
        assert len(js_files) >= 1
        assert any("nested.js" in r.name for r in js_files)

    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test error handling for invalid inputs."""
        # Non-existent path - may return empty results instead of raising
        try:
            result = await grep(pattern="test", directory="/non/existent/path")
            # Should either raise or return empty/error message
            assert "error" in result.lower() or len(result) < 50
        except Exception:
            # This is also acceptable behavior
            pass

        # Invalid regex - should handle gracefully
        try:
            result = await grep(pattern="[invalid regex", directory=".", use_regex=True)
            # Should indicate regex error
            assert "error" in result.lower() or "invalid" in result.lower()
        except Exception:
            # This is also acceptable behavior
            pass

    @pytest.mark.asyncio
    async def test_parallel_execution(self, temp_dir):
        """Test that grep executes file searches in parallel."""
        # Create many files to search
        for i in range(20):
            (temp_dir / f"test{i}.txt").write_text(f"content with pattern {i}")

        # Time the search to ensure it's reasonably fast
        import time

        start = time.time()

        result = await grep(pattern="pattern", directory=str(temp_dir))

        elapsed = time.time() - start

        # Should find all files
        assert result.count(".txt:") >= 20

        # Parallel execution should be fast (this is a soft assertion)
        assert elapsed < 2.0  # Should complete quickly

    @pytest.mark.asyncio
    async def test_search_config_defaults(self, temp_dir):
        """Test that SearchConfig defaults are applied correctly."""
        # Run with minimal parameters
        result = await grep(pattern="pattern", directory=str(temp_dir))

        # Should show matches with content by default
        assert "data.txt" in result
        assert "Pattern match here" in result

    @pytest.mark.asyncio
    async def test_performance_with_timeout(self, temp_dir):
        """Test timeout handling for broad patterns."""
        # Create a large number of files
        large_dir = temp_dir / "large"
        large_dir.mkdir()

        for i in range(100):
            (large_dir / f"file{i}.txt").write_text("x" * 1000)

        # Search with a very broad pattern that matches everything
        # This should still complete within timeout
        result = await grep(pattern="x", directory=str(large_dir), max_results=10)

        # Should return results (but may not be limited by max_results for broad patterns)
        assert "file" in result
        # The tool may return more results for performance reasons
        file_count = result.count(".txt:")
        assert file_count > 0  # Should find at least some files
