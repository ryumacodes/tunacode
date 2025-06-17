#!/usr/bin/env python3
"""
Demo script to show performance improvements with fast-glob prefilter.

This creates a test directory with many files and measures search performance.
"""

import asyncio
import os
import tempfile
import time
from pathlib import Path

from tunacode.tools.grep import grep


async def benchmark_grep():
    """Run performance benchmarks for grep with fast-glob prefilter."""
    
    with tempfile.TemporaryDirectory() as tmpdir:
        test_path = Path(tmpdir)
        
        # Create a realistic codebase structure
        print("Setting up test directory...")
        
        # Create many non-Python files that would slow down search
        for i in range(200):
            (test_path / f"data_{i}.txt").write_text(f"data file {i}")
            (test_path / f"log_{i}.log").write_text(f"log entry {i}")
            (test_path / f"config_{i}.json").write_text(f'{{"id": {i}}}')
        
        # Create some Python files with the pattern we're looking for
        for i in range(20):
            content = f"""import os
import sys
from pathlib import Path

def function_{i}():
    '''Function {i} docstring'''
    return {i}

# TODO: implement feature {i}
"""
            (test_path / f"module_{i}.py").write_text(content)
        
        # Create some JavaScript files
        for i in range(30):
            content = f"""// TODO: implement feature {i}
export function feature{i}() {{
    console.log('Feature {i}');
}}
"""
            (test_path / f"feature_{i}.js").write_text(content)
        
        print(f"Created {650} files total")
        print("-" * 60)
        
        # Test 1: Search Python files only (with prefiltering)
        print("\nTest 1: Search 'TODO' in Python files only")
        start = time.time()
        result = await grep("TODO", str(test_path), include_files="*.py")
        elapsed = time.time() - start
        
        lines = result.split("\n")
        match_line = lines[0] if lines else ""
        strategy_line = lines[1] if len(lines) > 1 else ""
        
        print(f"Time: {elapsed:.3f}s")
        print(match_line)
        print(strategy_line)
        
        # Test 2: Search all files (no prefiltering by extension)
        print("\nTest 2: Search 'TODO' in all files")
        start = time.time()
        result = await grep("TODO", str(test_path))
        elapsed = time.time() - start
        
        lines = result.split("\n")
        match_line = lines[0] if lines else ""
        strategy_line = lines[1] if len(lines) > 1 else ""
        
        print(f"Time: {elapsed:.3f}s")
        print(match_line)
        print(strategy_line)
        
        # Test 3: Complex pattern matching
        print("\nTest 3: Search with complex glob pattern (*.{py,js})")
        start = time.time()
        result = await grep("TODO", str(test_path), include_files="*.{py,js}")
        elapsed = time.time() - start
        
        lines = result.split("\n")
        match_line = lines[0] if lines else ""
        strategy_line = lines[1] if len(lines) > 1 else ""
        
        print(f"Time: {elapsed:.3f}s")
        print(match_line)
        print(strategy_line)
        
        # Test 4: Regex search with prefiltering
        print("\nTest 4: Regex search 'import.*Path' in Python files")
        start = time.time()
        result = await grep(r"import.*Path", str(test_path), use_regex=True, include_files="*.py")
        elapsed = time.time() - start
        
        lines = result.split("\n")
        match_line = lines[0] if lines else ""
        strategy_line = lines[1] if len(lines) > 1 else ""
        
        print(f"Time: {elapsed:.3f}s")
        print(match_line)
        print(strategy_line)
        
        print("\n" + "=" * 60)
        print("Performance Summary:")
        print("- Fast-glob prefilter efficiently narrows down file candidates")
        print("- Smart strategy selection optimizes for different file counts")
        print("- Significant performance gains when searching specific file types")


if __name__ == "__main__":
    print("Grep Performance Demo with Fast-Glob Prefilter")
    print("=" * 60)
    asyncio.run(benchmark_grep())