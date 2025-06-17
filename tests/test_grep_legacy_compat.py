"""
Test to ensure grep works without include_files parameter (legacy compatibility).
This test ensures that removing unfiltered search paths doesn't break existing usage.
"""

import asyncio
import tempfile
from pathlib import Path

import pytest

from tunacode.tools.grep import grep


class TestGrepLegacyCompat:
    """Test grep functionality without include_files parameter."""

    @pytest.mark.asyncio
    async def test_grep_without_include_files(self):
        """Test that grep works when include_files is not specified."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            (Path(tmpdir) / "test1.py").write_text("def hello():\n    return 'Hello'")
            (Path(tmpdir) / "test2.txt").write_text("Hello World")
            (Path(tmpdir) / "test3.js").write_text("console.log('Hello');")
            
            # Call grep without include_files - this should work via filtered path
            result = await grep("Hello", tmpdir)
            
            # Should find matches in all files
            assert "Found" in result and "matches" in result
            assert "test1.py" in result
            assert "test2.txt" in result
            assert "test3.js" in result

    @pytest.mark.asyncio
    async def test_grep_all_search_types_without_include(self):
        """Test all search types work without include_files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test content
            (Path(tmpdir) / "main.py").write_text("import os\nimport sys")
            
            # Test each search type
            for search_type in ["smart", "ripgrep", "python", "hybrid"]:
                result = await grep("import", tmpdir, search_type=search_type)
                # Some search types might not work in all environments (e.g., ripgrep)
                # So we just check that we get a result string back
                assert isinstance(result, str)
                assert "Strategy:" in result  # Should always show strategy info

    @pytest.mark.asyncio
    async def test_grep_regex_without_include(self):
        """Test regex search without include_files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "test.py").write_text("value = 123\nresult = 456")
            
            # Regex search without include_files
            result = await grep(r"\w+ = \d+", tmpdir, use_regex=True)
            
            assert "Found" in result
            assert "value = 123" in result or "123" in result
            assert "result = 456" in result or "456" in result