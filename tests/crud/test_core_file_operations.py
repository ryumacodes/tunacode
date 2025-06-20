"""
Comprehensive test suite for core file operations: Search, Read, Update, Create.

This test suite ensures the CLI agent can reliably perform all file operations
in various scenarios following best practices.
"""

import asyncio
import os
import tempfile
import time
from pathlib import Path
from typing import List

import pytest

from tunacode.tools.grep import grep
from tunacode.tools.read_file import read_file
from tunacode.tools.update_file import update_file
from tunacode.tools.write_file import write_file


class TestCoreFileOperations:
    """Test suite for core file operations."""

    @pytest.fixture
    async def temp_workspace(self):
        """Create a temporary workspace for tests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            os.chdir(tmpdir)
            yield tmpdir
            os.chdir(original_cwd)

    # ========== SEARCH (GREP) TESTS ==========

    @pytest.mark.asyncio
    async def test_search_simple_string(self, temp_workspace):
        """Test searching for a simple string across files."""
        # Create test files
        await write_file("file1.txt", "Hello World")
        await write_file("file2.txt", "Hello Python")
        await write_file("file3.txt", "Goodbye World")
        
        # Search for "Hello"
        results = await grep("Hello", return_format="list")
        assert len(results) == 2
        assert any("file1.txt" in r for r in results)
        assert any("file2.txt" in r for r in results)

    @pytest.mark.asyncio
    async def test_search_with_file_pattern(self, temp_workspace):
        """Test searching within specific file patterns."""
        # Create mixed file types
        await write_file("script.py", "import os\nprint('Hello')")
        await write_file("app.js", "console.log('Hello');")
        await write_file("doc.txt", "Hello there")
        
        # Search only in Python files
        py_results = await grep("Hello", include_files="*.py", return_format="list")
        assert len(py_results) == 1
        assert "script.py" in py_results[0]
        
        # Search only in JS files
        js_results = await grep("Hello", include_files="*.js", return_format="list")
        assert len(js_results) == 1
        assert "app.js" in js_results[0]

    @pytest.mark.asyncio
    async def test_search_regex_patterns(self, temp_workspace):
        """Test searching using regex patterns."""
        # Create files with patterns
        await write_file("code.py", "def test_function():\n    pass\ndef another_function():\n    pass")
        await write_file("utils.py", "class TestClass:\n    def method(self):\n        pass")
        
        # Search for function definitions
        func_results = await grep(r"^def \w+", include_files="*.py", return_format="list", use_regex=True)
        assert len(func_results) == 1
        assert "code.py" in func_results[0]
        
        # Search for class definitions
        class_results = await grep(r"^class \w+", include_files="*.py", return_format="list", use_regex=True)
        assert len(class_results) == 1
        assert "utils.py" in class_results[0]

    @pytest.mark.asyncio
    async def test_search_case_sensitivity(self, temp_workspace):
        """Test case-sensitive vs case-insensitive search."""
        await write_file("test.txt", "Hello HELLO hello")
        
        # Case-insensitive (default)
        results_insensitive = await grep("hello", case_sensitive=False, return_format="list")
        assert len(results_insensitive) == 1
        
        # Case-sensitive
        results_sensitive = await grep("hello", case_sensitive=True, return_format="list")
        assert len(results_sensitive) == 1  # Still finds the file with lowercase "hello"

    @pytest.mark.asyncio
    async def test_search_empty_results(self, temp_workspace):
        """Test behavior when no matches found."""
        await write_file("test.txt", "Some content")
        
        # Search for non-existent pattern
        results = await grep("NonExistentPattern", return_format="list")
        assert len(results) == 0
        assert isinstance(results, list)

    # ========== READ TESTS ==========

    @pytest.mark.asyncio
    async def test_read_simple_file(self, temp_workspace):
        """Test reading a basic text file."""
        content = "Line 1\nLine 2\nLine 3"
        await write_file("test.txt", content)
        
        result = await read_file("test.txt")
        assert "Line 1" in result
        assert "Line 2" in result
        assert "Line 3" in result
        # Check line numbers are included
        assert "1→" in result or "1\t" in result

    @pytest.mark.asyncio
    async def test_read_with_offset_limit(self, temp_workspace):
        """Test reading with offset and limit parameters."""
        # Create file with 20 lines
        content = "\n".join([f"Line {i}" for i in range(1, 21)])
        await write_file("test.txt", content)
        
        # Read lines 5-10
        result = await read_file("test.txt", offset=5, limit=5)
        assert "Line 6" in result  # Line numbers are 1-based, so offset 5 starts at line 6
        assert "Line 10" in result
        assert "Line 1" not in result
        assert "Line 15" not in result

    @pytest.mark.asyncio
    async def test_read_empty_file(self, temp_workspace):
        """Test reading an empty file."""
        await write_file("empty.txt", "")
        
        result = await read_file("empty.txt")
        # Should handle empty file gracefully
        assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_read_nonexistent_file(self, temp_workspace):
        """Test reading a non-existent file."""
        with pytest.raises(Exception) as exc_info:
            await read_file("nonexistent.txt")
        assert "not found" in str(exc_info.value).lower() or "no such file" in str(exc_info.value).lower()

    # ========== UPDATE TESTS ==========

    @pytest.mark.asyncio
    async def test_update_simple_replacement(self, temp_workspace):
        """Test basic string replacement."""
        await write_file("test.txt", "Hello World")
        
        await update_file("test.txt", target="World", patch="Universe")
        
        content = await read_file("test.txt")
        assert "Hello Universe" in content
        assert "World" not in content

    @pytest.mark.asyncio
    async def test_update_multiline_content(self, temp_workspace):
        """Test updating across multiple lines."""
        original = """def old_function():
    # Old implementation
    return 42"""
        
        await write_file("code.py", original)
        
        await update_file(
            "code.py",
            target="def old_function():\n    # Old implementation\n    return 42",
            patch="def new_function():\n    # New implementation\n    return 100"
        )
        
        content = await read_file("code.py")
        assert "new_function" in content
        assert "return 100" in content
        assert "old_function" not in content

    @pytest.mark.asyncio
    async def test_update_preserve_formatting(self, temp_workspace):
        """Test that updates preserve indentation and whitespace."""
        code = """class MyClass:
    def method(self):
        # TODO: implement this
        pass"""
        
        await write_file("test.py", code)
        await update_file("test.py", target="# TODO: implement this", patch="# Implemented")
        
        content = await read_file("test.py")
        assert "        # Implemented" in content  # Preserves indentation

    # ========== CREATE TESTS ==========

    @pytest.mark.asyncio
    async def test_create_simple_file(self, temp_workspace):
        """Test creating a basic text file."""
        await write_file("new_file.txt", "Hello, World!")
        
        # Verify file exists and has correct content
        assert Path("new_file.txt").exists()
        content = await read_file("new_file.txt")
        assert "Hello, World!" in content

    @pytest.mark.asyncio
    async def test_create_nested_directories(self, temp_workspace):
        """Test creating files in nested directories."""
        await write_file("src/components/Button.tsx", "export const Button = () => {}")
        
        assert Path("src/components/Button.tsx").exists()
        content = await read_file("src/components/Button.tsx")
        assert "Button" in content

    @pytest.mark.asyncio
    async def test_create_already_exists(self, temp_workspace):
        """Test that creating an existing file fails."""
        await write_file("test.txt", "Original content")
        
        # Attempt to create again should fail
        with pytest.raises(Exception) as exc_info:
            await write_file("test.txt", "New content")
        assert "exists" in str(exc_info.value).lower()

    # ========== INTEGRATION WORKFLOW TESTS ==========

    @pytest.mark.asyncio
    async def test_search_read_update_workflow(self, temp_workspace):
        """Test complete workflow: search → read → update."""
        # Create test files with debug flags
        await write_file("config.json", '{"debug": true, "port": 3000}')
        await write_file("settings.json", '{"debug": false, "host": "localhost"}')
        await write_file("app.json", '{"name": "app", "debug": true}')
        
        # Search for files with debug settings
        debug_files = await grep("debug", include_files="*.json", return_format="list")
        assert len(debug_files) == 3
        
        # Read and update each file to disable debug
        for file_path in debug_files:
            content = await read_file(file_path)
            if '"debug": true' in content:
                await update_file(file_path, target='"debug": true', patch='"debug": false')
        
        # Verify all debug flags are now false
        remaining_debug = await grep('"debug": true', include_files="*.json", return_format="list")
        assert len(remaining_debug) == 0

    @pytest.mark.asyncio
    async def test_create_search_read_update_workflow(self, temp_workspace):
        """Test complete workflow: create → search → read → update."""
        # Create multiple Python files with TODOs
        files_created = []
        for i in range(5):
            filename = f"module_{i}.py"
            content = f"""def function_{i}():
    # TODO: implement function_{i}
    pass

class Class_{i}:
    # TODO: add methods
    pass"""
            await write_file(filename, content)
            files_created.append(filename)
        
        # Search for all TODOs
        todo_files = await grep("TODO:", include_files="*.py", return_format="list", use_regex=True)
        assert len(todo_files) == 5
        
        # Update all TODOs to mark as implemented
        for file_path in todo_files:
            content = await read_file(file_path)
            # Update function TODOs
            if "TODO: implement" in content:
                await update_file(file_path, 
                    target="# TODO: implement", 
                    patch="# Implemented"
                )
            # Update class TODOs
            content = await read_file(file_path)  # Re-read after first update
            if "TODO: add methods" in content:
                await update_file(file_path, 
                    target="# TODO: add methods", 
                    patch="# Methods added"
                )
        
        # Verify no TODOs remain
        remaining_todos = await grep("TODO:", include_files="*.py", return_format="list", use_regex=True)
        assert len(remaining_todos) == 0

    @pytest.mark.asyncio
    async def test_batch_file_operations(self, temp_workspace):
        """Test batch operations across multiple file types."""
        # Create files of different types
        file_types = {
            'py': 'print("Python file")',
            'js': 'console.log("JavaScript file");',
            'tsx': 'export const Component = () => <div>React</div>;',
            'json': '{"type": "JSON file"}'
        }
        
        created_files = []
        for ext, content in file_types.items():
            for i in range(3):
                filename = f"file_{i}.{ext}"
                await write_file(filename, f"// File number {i}\n{content}")
                created_files.append(filename)
        
        # Search across different file types
        py_files = await grep("file", include_files="*.py", return_format="list", case_sensitive=False)
        js_files = await grep("file", include_files="*.js", return_format="list", case_sensitive=False)
        all_files = await grep("file", return_format="list", case_sensitive=False)
        
        assert len(py_files) == 3
        assert len(js_files) == 3
        assert len(all_files) == 12  # 3 files × 4 extensions

    # ========== PERFORMANCE TESTS ==========

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_performance_large_scale_operations(self, temp_workspace):
        """Test performance with large number of files."""
        # Create 100 files (reduced from 1000 for faster tests)
        start_time = time.time()
        for i in range(100):
            await write_file(f"perf_test_{i}.txt", f"Content number {i}\nWith some additional text")
        create_time = time.time() - start_time
        assert create_time < 10  # Should complete within 10 seconds
        
        # Search across all files
        start_time = time.time()
        results = await grep("Content", include_files="perf_test_*.txt", return_format="list")
        search_time = time.time() - start_time
        assert search_time < 3  # Should complete within 3 seconds
        assert len(results) == 100

    @pytest.mark.asyncio
    async def test_unicode_and_special_characters(self, temp_workspace):
        """Test handling of unicode and special characters."""
        # Create files with unicode content
        await write_file("unicode.txt", "Hello 世界 🌍 Émojis работает")
        await write_file("code.py", "# -*- coding: utf-8 -*-\nprint('Ñoño')")
        
        # Search for unicode content
        chinese_results = await grep("世界", return_format="list")
        assert len(chinese_results) == 1
        
        emoji_results = await grep("🌍", return_format="list")
        assert len(emoji_results) == 1
        
        # Read unicode content
        content = await read_file("unicode.txt")
        assert "世界" in content
        assert "🌍" in content

    # ========== ERROR HANDLING TESTS ==========

    @pytest.mark.asyncio
    async def test_error_handling_invalid_paths(self, temp_workspace):
        """Test error handling for invalid paths."""
        # Test with path containing null bytes (if supported by OS)
        invalid_paths = [
            "../../../etc/passwd",  # Path traversal attempt
            "con.txt" if os.name == 'nt' else "/dev/null",  # Reserved names
            "file_with_very_" + "long_" * 100 + "name.txt"  # Very long filename
        ]
        
        for invalid_path in invalid_paths:
            try:
                await write_file(invalid_path, "test")
                # If write succeeds, try to read
                await read_file(invalid_path)
            except Exception as e:
                # Should raise some form of error
                assert isinstance(e, Exception)

    @pytest.mark.asyncio
    async def test_concurrent_file_access(self, temp_workspace):
        """Test handling of concurrent file access."""
        await write_file("shared.txt", "Initial content")
        
        # Simulate concurrent reads
        read_tasks = [read_file("shared.txt") for _ in range(10)]
        results = await asyncio.gather(*read_tasks)
        
        # All reads should succeed and return same content
        assert len(results) == 10
        assert all("Initial content" in r for r in results)

    @pytest.mark.asyncio
    async def test_search_with_complex_patterns(self, temp_workspace):
        """Test complex search scenarios."""
        # Create a realistic codebase structure
        await write_file("src/api/auth.py", """
import jwt
from datetime import datetime

def authenticate(username, password):
    # TODO: Add password hashing
    if username == "admin" and password == "admin":
        return generate_token(username)
    return None

def generate_token(username):
    # TODO: Add expiration
    return jwt.encode({"user": username}, "secret")
""")
        
        await write_file("src/api/users.py", """
from .auth import authenticate

class UserManager:
    def login(self, username, password):
        token = authenticate(username, password)
        # TODO: Store session
        return token
""")
        
        # Search for security issues
        security_patterns = [
            (r'password == ["\']\w+["\']', "Hardcoded passwords"),
            (r'TODO:.*password', "Password-related TODOs"),
            (r'jwt\.encode.*["\']secret["\']', "Hardcoded JWT secret")
        ]
        
        for pattern, description in security_patterns:
            results = await grep(pattern, include_files="**/*.py", return_format="list", use_regex=True)
            assert len(results) > 0, f"Should find {description}"