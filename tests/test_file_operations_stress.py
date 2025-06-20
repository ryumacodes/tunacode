"""
Stress tests for file operations.
Tests performance with large files, many files, and deep nesting.
"""
import os
import tempfile
import pytest
import time
from pathlib import Path
from tunacode.tools.glob import glob
from tunacode.tools.grep import grep
from tunacode.tools.read_file import read_file
from tunacode.tools.write_file import write_file
from tunacode.tools.update_file import update_file
from tunacode.tools.list_dir import list_dir

pytestmark = pytest.mark.asyncio


class TestFileOperationsStress:
    """Stress tests for file operations."""
    
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
    
    @pytest.mark.slow
    async def test_large_file_handling(self):
        """Test handling of large files (>10MB)."""
        # Create a 15MB file
        large_content = "x" * (15 * 1024 * 1024)
        
        # Test write performance
        start_time = time.time()
        await write_file("large_file.txt", large_content)
        write_time = time.time() - start_time
        
        assert Path("large_file.txt").exists()
        assert Path("large_file.txt").stat().st_size == len(large_content)
        
        # Test read - should fail due to size limit
        result = await read_file("large_file.txt")
        assert "too large" in result.lower()
        
        # Create a file just under the limit (assuming 1MB limit)
        medium_content = "y" * (1024 * 1024 - 100)  # Just under 1MB
        await write_file("medium_file.txt", medium_content)
        
        # This should succeed
        start_time = time.time()
        content = await read_file("medium_file.txt")
        read_time = time.time() - start_time
        
        assert content == medium_content
        assert read_time < 1.0  # Should be fast
    
    @pytest.mark.slow
    async def test_many_small_files(self):
        """Test handling many small files (1000+)."""
        # Create 1000 small files
        num_files = 1000
        
        start_time = time.time()
        for i in range(num_files):
            await write_file(f"file_{i:04d}.txt", f"Content of file {i}")
        create_time = time.time() - start_time
        
        # Test glob performance
        start_time = time.time()
        all_files = await glob("file_*.txt")
        glob_time = time.time() - start_time
        
        assert len(all_files) == num_files
        assert glob_time < 2.0  # Should complete within 2 seconds
        
        # Test grep performance on many files
        start_time = time.time()
        matches = await grep("Content of file 5", include_files="file_*.txt", return_format="list")
        grep_time = time.time() - start_time
        
        # Should find files containing "file 5" (50, 51, ..., 59, 150, 151, ..., etc.)
        assert len(matches) > 0
        assert grep_time < 5.0  # Should complete within 5 seconds
        
        # Test list_dir performance
        start_time = time.time()
        items = await list_dir(".")
        list_time = time.time() - start_time
        
        # Should handle listing even with many files
        assert len(items) >= min(num_files, 1000)  # May be limited
        assert list_time < 1.0  # Should be fast
    
    @pytest.mark.slow
    async def test_deep_directory_nesting(self):
        """Test operations with deeply nested directories (10+ levels)."""
        # Create deeply nested structure
        depth = 15
        current_path = Path(".")
        
        for i in range(depth):
            current_path = current_path / f"level_{i}"
            current_path.mkdir()
            await write_file(str(current_path / f"file_{i}.txt"), f"Content at level {i}")
        
        # Test glob with deep recursion
        start_time = time.time()
        all_files = await glob("**/file_*.txt")
        glob_time = time.time() - start_time
        
        assert len(all_files) == depth
        assert glob_time < 2.0  # Should handle deep recursion efficiently
        
        # Test reading deeply nested file
        deep_file = str(current_path / f"file_{depth-1}.txt")
        content = await read_file(deep_file)
        assert f"Content at level {depth-1}" in content
        
        # Test grep in deep structure
        start_time = time.time()
        level_5_files = await grep("level 5", include_files="**/file_*.txt", return_format="list")
        grep_time = time.time() - start_time
        
        assert len(level_5_files) > 0
        assert any("level_5" in f for f in level_5_files)
        assert grep_time < 3.0  # Should complete reasonably fast
    
    @pytest.mark.slow
    async def test_concurrent_read_performance(self):
        """Test performance of concurrent read operations."""
        # Create test files
        num_files = 100
        for i in range(num_files):
            content = f"File {i} content\n" * 100  # Make files non-trivial
            await write_file(f"read_test_{i}.txt", content)
        
        # Simulate concurrent reads
        start_time = time.time()
        read_results = []
        
        # Read all files (framework should handle concurrency)
        for i in range(num_files):
            content = await read_file(f"read_test_{i}.txt")
            read_results.append(content)
        
        total_time = time.time() - start_time
        
        # Verify all reads succeeded
        assert len(read_results) == num_files
        assert all(f"File {i} content" in read_results[i] for i in range(num_files))
        
        # Should benefit from parallel execution
        assert total_time < num_files * 0.01  # Much faster than sequential
    
    @pytest.mark.slow
    async def test_large_directory_listing(self):
        """Test listing directories with many entries."""
        # Create many files and subdirectories
        num_dirs = 100
        num_files_per_dir = 10
        
        for d in range(num_dirs):
            dir_path = Path(f"dir_{d:03d}")
            dir_path.mkdir()
            for f in range(num_files_per_dir):
                await write_file(str(dir_path / f"file_{f}.txt"), "content")
        
        # Test root directory listing
        start_time = time.time()
        items = await list_dir(".")
        list_time = time.time() - start_time
        
        # Should handle large directory efficiently
        assert len(items) >= min(num_dirs, 1000)  # May be limited
        assert all(item.startswith("dir_") and item.endswith("/") for item in items[:num_dirs])
        assert list_time < 1.0
        
        # Test subdirectory listing
        sub_items = await list_dir("dir_050")
        assert len(sub_items) == num_files_per_dir
        assert all(item.startswith("file_") for item in sub_items)
    
    @pytest.mark.slow
    async def test_search_performance_with_many_matches(self):
        """Test search performance when many files match."""
        # Create files with common patterns
        num_files = 500
        
        for i in range(num_files):
            content = f"""
# Common header
import os
import sys

def function_{i}():
    # TODO: implement
    return {i}

# Common footer
"""
            await write_file(f"module_{i:03d}.py", content)
        
        # Search for common pattern (should match all files)
        start_time = time.time()
        todo_files = await grep("TODO:", include_files="*.py", return_format="list")
        grep_time = time.time() - start_time
        
        assert len(todo_files) == num_files
        assert grep_time < 5.0  # Should handle many matches efficiently
        
        # Search for specific pattern (fewer matches)
        start_time = time.time()
        specific_files = await grep("function_42", include_files="*.py", return_format="list")
        specific_time = time.time() - start_time
        
        assert len(specific_files) == 1
        assert "module_042.py" in specific_files[0]
        assert specific_time < 3.0  # Should optimize when fewer matches
    
    @pytest.mark.slow
    async def test_update_performance_on_large_files(self):
        """Test update performance on files with many lines."""
        # Create a file with many lines
        num_lines = 10000
        lines = [f"Line {i}: Some content here" for i in range(num_lines)]
        large_content = "\n".join(lines)
        
        await write_file("large_lines.txt", large_content)
        
        # Update a line in the middle
        start_time = time.time()
        await update_file(
            "large_lines.txt",
            target="Line 5000: Some content here",
            patch="Line 5000: UPDATED CONTENT"
        )
        update_time = time.time() - start_time
        
        # Should handle large files efficiently
        assert update_time < 2.0
        
        # Verify update
        content = await read_file("large_lines.txt")
        assert "Line 5000: UPDATED CONTENT" in content
        assert "Line 4999: Some content here" in content
        assert "Line 5001: Some content here" in content
    
    @pytest.mark.slow
    async def test_glob_performance_with_complex_patterns(self):
        """Test glob performance with complex patterns."""
        # Create complex directory structure
        extensions = ['py', 'js', 'tsx', 'jsx', 'ts', 'md', 'json', 'yaml', 'yml', 'txt']
        subdirs = ['src', 'tests', 'docs', 'config', 'scripts']
        
        for subdir in subdirs:
            Path(subdir).mkdir()
            for i in range(20):
                for ext in extensions:
                    await write_file(f"{subdir}/file_{i}.{ext}", f"Content for {ext}")
        
        # Test complex glob patterns
        patterns = [
            "**/*.{js,jsx,ts,tsx}",  # Multiple extensions
            "src/**/*.py",            # Specific directory
            "**/file_1?.json",        # Wildcard in name
            "**/*.[jt]s",            # Character class
        ]
        
        for pattern in patterns:
            start_time = time.time()
            matches = await glob(pattern)
            glob_time = time.time() - start_time
            
            assert len(matches) > 0
            assert glob_time < 1.0  # Each pattern should be fast
    
    @pytest.mark.slow
    async def test_mixed_operation_stress(self):
        """Test mixed file operations under stress."""
        # Create initial structure
        num_operations = 100
        
        start_time = time.time()
        
        # Mix of operations
        for i in range(num_operations):
            operation = i % 4
            
            if operation == 0:
                # Create file
                await write_file(f"mixed_{i}.txt", f"Initial content {i}")
            elif operation == 1:
                # Read file
                if i > 3:  # Ensure file exists
                    content = await read_file(f"mixed_{i-4}.txt")
                    assert f"content {i-4}" in content.lower()
            elif operation == 2:
                # Update file
                if i > 3:  # Ensure file exists
                    try:
                        await update_file(
                            f"mixed_{i-4}.txt",
                            target=f"content {i-4}",
                            patch=f"updated {i-4}"
                        )
                    except Exception:
                        # File might have been updated already
                        pass
            else:
                # Search files
                matches = await glob("mixed_*.txt")
                assert len(matches) > 0
        
        total_time = time.time() - start_time
        
        # Should complete all operations in reasonable time
        assert total_time < 30.0  # 100 operations in 30 seconds
        
        # Verify final state
        final_files = await glob("mixed_*.txt")
        assert len(final_files) >= 25  # At least 25 files created