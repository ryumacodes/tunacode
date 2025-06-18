#!/usr/bin/env python3
"""
Test for grep tool timeout handling functionality.

The grep tool has a 60-second timeout for finding the FIRST match.
This prevents the tool from hanging indefinitely on patterns that
match nothing or take too long to process.
"""
import asyncio
import sys
import os
import tempfile
from pathlib import Path
import time

# Add src to path so we can import tunacode modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_search_with_no_matches_completes():
    """Test that searching for non-existent pattern completes without timeout"""
    from tunacode.tools.grep import grep
    
    print("Testing search for non-existent pattern...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create some test files
        for i in range(10):
            Path(tmpdir, f"test_{i}.py").write_text(f"def function_{i}():\n    return {i}")
        
        start_time = time.time()
        
        # Search for something that doesn't exist
        result = asyncio.run(grep(
            pattern="DOES_NOT_EXIST_ANYWHERE",
            directory=tmpdir,
            include_files="*.py"
        ))
        
        elapsed = time.time() - start_time
        
        assert "No matches found" in result
        assert elapsed < 5.0, f"Search took too long: {elapsed:.2f}s"
        
        print(f"✓ Non-existent pattern search completed in {elapsed:.2f}s")

def test_normal_search_finds_matches_quickly():
    """Test that normal searches find first match quickly"""
    from tunacode.tools.grep import grep
    
    print("Testing normal search finds matches quickly...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test files with searchable content
        for i in range(50):
            content = f"import os\nimport sys\n# TODO: implement feature {i}\n"
            Path(tmpdir, f"module_{i}.py").write_text(content)
        
        start_time = time.time()
        
        # Search for a common pattern
        result = asyncio.run(grep(
            pattern="TODO",
            directory=tmpdir,
            include_files="*.py",
            max_results=10
        ))
        
        elapsed = time.time() - start_time
        
        assert "Found" in result and "matches" in result
        assert elapsed < 2.0, f"Search took too long: {elapsed:.2f}s"
        
        print(f"✓ Found matches in {elapsed:.2f}s")

def test_regex_search_performance():
    """Test that regex searches perform reasonably"""
    from tunacode.tools.grep import grep
    
    print("Testing regex search performance...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create files with various patterns
        for i in range(20):
            content = f"""
def process_{i}(data):
    result = calculate_{i}(data)
    value = transform_{i}(result)
    return finalize_{i}(value)
"""
            Path(tmpdir, f"processor_{i}.py").write_text(content)
        
        start_time = time.time()
        
        # Search with a regex pattern
        result = asyncio.run(grep(
            pattern=r"(calculate|transform|finalize)_\d+",
            directory=tmpdir,
            use_regex=True,
            include_files="*.py"
        ))
        
        elapsed = time.time() - start_time
        
        assert "Found" in result
        assert elapsed < 3.0, f"Regex search took too long: {elapsed:.2f}s"
        
        print(f"✓ Regex search completed in {elapsed:.2f}s")

def test_large_file_search():
    """Test searching in files with many lines"""
    from tunacode.tools.grep import grep
    
    print("Testing search in large files...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a large file
        lines = []
        for i in range(10000):
            if i == 5000:
                lines.append("# SPECIAL_MARKER: This is the line we're looking for")
            else:
                lines.append(f"# Regular line number {i}")
        
        Path(tmpdir, "large_file.py").write_text("\n".join(lines))
        
        start_time = time.time()
        
        # Search for the special marker
        result = asyncio.run(grep(
            pattern="SPECIAL_MARKER",
            directory=tmpdir,
            include_files="*.py"
        ))
        
        elapsed = time.time() - start_time
        
        assert "Found 1 matches" in result
        assert "line 5001" in result or "5001" in result
        assert elapsed < 2.0, f"Large file search took too long: {elapsed:.2f}s"
        
        print(f"✓ Large file search completed in {elapsed:.2f}s")

def test_search_with_excludes():
    """Test that searches with exclude patterns work efficiently"""
    from tunacode.tools.grep import grep
    
    print("Testing search with exclude patterns...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test structure
        (Path(tmpdir) / "src").mkdir()
        (Path(tmpdir) / "tests").mkdir()
        (Path(tmpdir) / "node_modules").mkdir()
        
        # Add files to each directory
        Path(tmpdir, "src/main.py").write_text("import unittest")
        Path(tmpdir, "tests/test_main.py").write_text("import unittest")
        Path(tmpdir, "node_modules/lib.py").write_text("import unittest")
        
        start_time = time.time()
        
        # Search excluding node_modules
        result = asyncio.run(grep(
            pattern="unittest",
            directory=tmpdir,
            include_files="*.py",
            exclude_files="node_modules/*"
        ))
        
        elapsed = time.time() - start_time
        
        assert "Found" in result
        assert "node_modules" not in result
        assert elapsed < 1.0, f"Search with excludes took too long: {elapsed:.2f}s"
        
        print(f"✓ Search with excludes completed in {elapsed:.2f}s")

# Tests are now pure pytest format - no main() function needed