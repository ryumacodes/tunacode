#!/usr/bin/env python3
"""
Example demonstrating the list_dir tool functionality.
"""

import asyncio
import tempfile
from pathlib import Path

from tunacode.tools.list_dir import list_dir


async def main():
    """Demonstrate list_dir tool capabilities."""
    print("=== List Dir Tool Demo ===\n")
    
    # 1. List current directory
    print("1. Listing current directory:")
    result = await list_dir()
    print(result[:300] + "...\n" if len(result) > 300 else result + "\n")
    
    # 2. Create a demo directory structure
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test structure
        Path(tmpdir, "src").mkdir()
        Path(tmpdir, "src", "main.py").touch()
        Path(tmpdir, "src", "utils.py").touch()
        Path(tmpdir, "tests").mkdir()
        Path(tmpdir, "tests", "test_main.py").touch()
        Path(tmpdir, "README.md").touch()
        Path(tmpdir, ".gitignore").touch()
        Path(tmpdir, "setup.py").touch()
        
        # Make setup.py executable
        Path(tmpdir, "setup.py").chmod(0o755)
        
        # 2. List without hidden files
        print("2. Listing directory (without hidden files):")
        result = await list_dir(tmpdir)
        print(result + "\n")
        
        # 3. List with hidden files
        print("3. Listing directory (with hidden files):")
        result = await list_dir(tmpdir, show_hidden=True)
        print(result + "\n")
        
        # 4. List with limited entries
        print("4. Listing directory (max 3 entries):")
        result = await list_dir(tmpdir, max_entries=3, show_hidden=True)
        print(result + "\n")
    
    # 5. Error handling - non-existent directory
    print("5. Attempting to list non-existent directory:")
    result = await list_dir("/path/that/does/not/exist")
    print(result + "\n")
    
    # 6. Error handling - file instead of directory
    print("6. Attempting to list a file instead of directory:")
    result = await list_dir(__file__)
    print(result)


if __name__ == "__main__":
    asyncio.run(main())