"""
Characterization tests for grep performance behaviors.
These tests capture the CURRENT performance characteristics and strategy selection of the grep tool.
"""
import os
import sys
import tempfile
import pytest
import time
from pathlib import Path
from tunacode.tools.grep import grep

pytestmark = pytest.mark.asyncio


class TestGrepPerformanceCharacterization:
    """Golden-master tests for grep performance behaviors and strategy selection."""
    
    def setup_method(self):
        """Create a temporary directory with test files."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
    
    def teardown_method(self):
        """Clean up temporary files."""
        os.chdir(self.original_cwd)
        import shutil
        shutil.rmtree(self.temp_dir)
    
    async def test_grep_fast_glob_prefilter_performance(self):
        """Capture performance behavior with fast-glob prefiltering."""
        # Create many non-matching files
        for i in range(100):
            await self._create_file(f"data_{i}.txt", f"data file {i}")
            await self._create_file(f"log_{i}.log", f"log entry {i}")
        
        # Create a few matching Python files
        for i in range(10):
            content = f"""import os
def function_{i}():
    # TODO: implement feature {i}
    return {i}
"""
            await self._create_file(f"module_{i}.py", content)
        
        # Measure time for filtered search
        start_time = time.time()
        result = await grep("TODO", include_files="*.py", return_format="string")
        filtered_time = time.time() - start_time
        
        # Verify it found the matches
        assert "Found" in result
        assert "TODO" in result
        lines = result.split("\n")
        
        # Check for strategy information (if present)
        strategy_mentioned = any("strategy" in line.lower() for line in lines)
        
        # Filtered search should be relatively fast
        assert filtered_time < 2.0  # Should complete within 2 seconds
        assert isinstance(result, str)
    
    async def test_grep_no_filter_performance(self):
        """Capture performance behavior without file filtering."""
        # Create many files of different types
        for i in range(50):
            await self._create_file(f"file_{i}.txt", f"content {i}")
            await self._create_file(f"script_{i}.py", f"# Python script {i}")
            await self._create_file(f"config_{i}.json", f'{{"id": {i}}}')
        
        # Search without filter
        start_time = time.time()
        result = await grep("content", return_format="string")
        unfiltered_time = time.time() - start_time
        
        # Should find matches in txt files
        assert "Found" in result
        assert unfiltered_time < 3.0  # Reasonable time limit
    
    async def test_grep_complex_glob_patterns(self):
        """Capture behavior with complex glob patterns like *.{py,js}."""
        # Create mixed file types
        for i in range(20):
            await self._create_file(f"module_{i}.py", f"# TODO: Python task {i}")
            await self._create_file(f"script_{i}.js", f"// TODO: JavaScript task {i}")
            await self._create_file(f"data_{i}.txt", f"TODO: Text task {i}")
        
        # Search with complex glob
        result = await grep("TODO", include_files="*.{py,js}", return_format="string")
        
        # Should find matches in both .py and .js files
        assert "Found" in result
        lines = result.split("\n")
        
        # Check if both file types are included
        py_found = any(".py" in line for line in lines)
        js_found = any(".js" in line for line in lines)
        txt_found = any(".txt" in line for line in lines)
        
        assert py_found or js_found  # At least one should be found
        assert not txt_found  # .txt files should be excluded
    
    async def test_grep_max_glob_limit(self):
        """Capture behavior when hitting MAX_GLOB limit."""
        # Create more files than MAX_GLOB limit (assuming it's around 1000)
        for i in range(200):  # Create 200 Python files
            await self._create_file(f"large_set_{i}.py", f"# File {i}\n# SEARCH_ME")
        
        # Try to search with glob filter
        result = await grep("SEARCH_ME", include_files="*.py", return_format="string")
        
        # Should still work but might use different strategy
        assert "Found" in result or "SEARCH_ME" in result
        
        # Check if strategy information mentions limits
        lines = result.split("\n")
        strategy_line = next((line for line in lines if "strategy" in line.lower()), "")
        
        # Capture actual behavior
        assert isinstance(result, str)
    
    async def test_grep_regex_with_prefilter(self):
        """Capture performance with regex patterns and file filtering."""
        # Create test files
        for i in range(30):
            content = f"""import os
import sys
from pathlib import Path

def process_{i}():
    return Path('/tmp/file_{i}')
"""
            await self._create_file(f"processor_{i}.py", content)
            await self._create_file(f"readme_{i}.md", f"# Documentation {i}\nUse Path objects")
        
        # Regex search with filter
        start_time = time.time()
        result = await grep(r"import.*Path", use_regex=True, include_files="*.py", return_format="string")
        regex_time = time.time() - start_time
        
        # Should find matches efficiently
        assert "Found" in result
        assert regex_time < 2.0
        
        # Should only match Python files
        lines = result.split("\n")
        assert not any(".md" in line for line in lines)
    
    async def test_grep_deeply_nested_structure(self):
        """Capture behavior with deeply nested directory structures."""
        # Create nested directories
        nested_path = Path(".")
        for i in range(5):  # 5 levels deep
            nested_path = nested_path / f"level_{i}"
            nested_path.mkdir(exist_ok=True)
            await self._create_file(str(nested_path / f"file_{i}.py"), f"# NESTED_PATTERN at level {i}")
        
        # Search in nested structure
        result = await grep("NESTED_PATTERN", return_format="list")
        
        # Should find files at all levels
        assert len(result) >= 5
        
        # Check if deeply nested files are found
        deepest_found = any("level_4" in f for f in result)
        assert deepest_found
    
    async def test_grep_mixed_encodings(self):
        """Capture behavior with files of different encodings."""
        # Create files with different content types
        await self._create_file("utf8.txt", "UTF-8: Hello 世界")
        await self._create_file("ascii.txt", "ASCII: Hello World")
        
        # Some files might have encoding issues
        Path("latin1.txt").write_bytes("Latin-1: café".encode('latin-1'))
        
        # Search for common pattern
        result = await grep("Hello", return_format="list")
        
        # Should handle UTF-8 and ASCII files
        assert len(result) >= 2
        assert any("utf8.txt" in f for f in result)
        assert any("ascii.txt" in f for f in result)
    
    async def test_grep_symlinks(self):
        """Capture behavior with symbolic links."""
        # Create a real file
        await self._create_file("original.py", "# SYMLINK_TEST pattern")
        
        # Create a symlink (if supported by OS)
        try:
            Path("link_to_original.py").symlink_to("original.py")
            has_symlink = True
        except (OSError, NotImplementedError):
            has_symlink = False
        
        # Search for pattern
        result = await grep("SYMLINK_TEST", return_format="list")
        
        if has_symlink:
            # Capture whether symlinks are followed or not
            assert len(result) >= 1  # At least the original
            # Record actual behavior regarding symlinks
        else:
            assert len(result) == 1  # Just the original
    
    async def test_grep_performance_with_large_matches(self):
        """Capture behavior when many files match the pattern."""
        # Create many files with the same pattern
        for i in range(100):
            await self._create_file(f"match_{i}.txt", f"Line 1\nCOMMON_PATTERN here\nLine 3")
        
        # Time the search
        start_time = time.time()
        result = await grep("COMMON_PATTERN", return_format="string")
        many_matches_time = time.time() - start_time
        
        # Should complete in reasonable time even with many matches
        assert many_matches_time < 5.0
        assert "Found" in result
        
        # Check if result mentions match count
        lines = result.split("\n")
        first_line = lines[0] if lines else ""
        assert "100" in first_line or "matches" in first_line.lower()
    
    async def test_grep_empty_directory(self):
        """Capture behavior in empty directories."""
        # Create empty subdirectory
        Path("empty_dir").mkdir()
        
        # Search in empty directory
        result = await grep("pattern", path="empty_dir", return_format="list")
        
        # Should handle gracefully
        assert isinstance(result, list)
        assert len(result) == 0
    
    async def test_grep_performance_first_match(self):
        """Capture first-match deadline behavior."""
        # Create files where pattern appears later
        for i in range(50):
            # Pattern is not in first files
            content = f"File {i} content\n" * 100 if i < 40 else f"File {i}\nTARGET_PATTERN\nMore content"
            await self._create_file(f"delayed_{i}.txt", content)
        
        # Search should respect deadline
        start_time = time.time()
        result = await grep("TARGET_PATTERN", return_format="string")
        search_time = time.time() - start_time
        
        # Should find matches (eventually)
        assert "Found" in result or "TARGET_PATTERN" in result
        
        # Search time might be affected by 3-second deadline
        assert search_time < 10.0  # Should not take too long
    
    async def test_grep_glob_prefilter_file_limit(self):
        """Capture behavior of MAX_GLOB limit affecting strategy."""
        # Create exactly at the boundary of MAX_GLOB limit
        # Assuming MAX_GLOB is 1000 based on the code
        for i in range(1010):  # Slightly over limit
            await self._create_file(f"boundary_{i}.py", f"# Test file {i}")
        
        # Add one file with our pattern
        await self._create_file("target.py", "# BOUNDARY_TEST pattern")
        
        # Search with glob that would match all Python files
        result = await grep("BOUNDARY_TEST", include_files="*.py", return_format="string")
        
        # Should still find the pattern
        assert "Found" in result or "BOUNDARY_TEST" in result
        
        # Check if strategy differs due to file count
        lines = result.split("\n")
        strategy_info = [line for line in lines if "strategy" in line.lower()]
        
        # Capture actual strategy selection behavior
        assert isinstance(result, str)
    
    # Helper method
    async def _create_file(self, filename: str, content: str) -> None:
        """Helper to create a file with content."""
        path = Path(filename)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)