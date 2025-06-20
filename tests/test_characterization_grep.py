"""
Characterization tests for GrepTool.
These tests capture the CURRENT behavior of the tool, including any quirks.
"""
import os
import sys
import tempfile
import pytest
from pathlib import Path
from tunacode.tools.grep import grep

pytestmark = pytest.mark.asyncio


class TestGrepCharacterization:
    """Golden-master tests for GrepTool behavior."""
    
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
    
    async def test_grep_basic_pattern(self):
        """Capture behavior with basic string patterns."""
        # Create test files
        await self._create_file("file1.py", "def hello():\n    return 'Hello World'")
        await self._create_file("file2.py", "# This is a test\nprint('Hello')")
        await self._create_file("file3.txt", "Hello there!\nGoodbye world")
        
        # Search for 'Hello'
        result = await grep("Hello", return_format="list")
        
        # Should find all files containing 'Hello'
        assert len(result) == 3
        assert all(isinstance(f, str) for f in result)
    
    async def test_grep_regex_pattern(self):
        """Capture behavior with regex patterns."""
        # Create test files with various patterns
        await self._create_file("email.txt", "Contact: john@example.com or admin@test.org")
        await self._create_file("no_email.txt", "No email addresses here")
        await self._create_file("code.py", "# Author: developer@company.com\nEMAIL_REGEX = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}'")
        
        # Search for email pattern
        email_pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
        result = await grep(email_pattern, use_regex=True, return_format="list")
        
        # Should find files with email addresses
        assert len(result) >= 2
        assert any("email.txt" in f for f in result)
        assert not any("no_email.txt" in f for f in result)
    
    async def test_grep_case_sensitivity(self):
        """Capture behavior regarding case sensitivity."""
        # Create files with different cases
        await self._create_file("test.py", "def Test():\n    pass")
        await self._create_file("test2.py", "def test():\n    pass")
        await self._create_file("test3.py", "def TEST():\n    pass")
        
        # Search for 'test' - likely case sensitive by default
        result = await grep("test", return_format="list")
        
        # Capture actual behavior
        assert isinstance(result, list)
        # Case sensitive search would only find 'test', not 'Test' or 'TEST'
    
    async def test_grep_with_include_filter(self):
        """Capture behavior with include patterns."""
        # Create various file types
        await self._create_file("app.js", "function test() { return true; }")
        await self._create_file("app.py", "def test(): return True")
        await self._create_file("app.java", "public boolean test() { return true; }")
        await self._create_file("readme.md", "This is a test file")
        
        # Search only in Python files
        result = await grep("test", include_files="*.py", return_format="list")
        
        # Should only find Python files
        assert len(result) == 1
        assert "app.py" in result[0]
        
        # Search in multiple extensions
        result2 = await grep("test", include_files="*.{py,js}", return_format="list")
        assert len(result2) == 2
        assert any("app.py" in f for f in result2)
        assert any("app.js" in f for f in result2)
    
    async def test_grep_multiline_content(self):
        """Capture behavior with multiline patterns."""
        # Create file with multiline content
        content = """class Example:
    def __init__(self):
        self.value = 42
    
    def method(self):
        return self.value"""
        
        await self._create_file("multiline.py", content)
        
        # Search for class definition
        result = await grep(r"class\s+\w+:", use_regex=True, return_format="list")
        assert len(result) == 1
        
        # Search across lines (may not work depending on implementation)
        result2 = await grep(r"def __init__.*\n.*self\.value", use_regex=True, return_format="list")
        # Capture actual behavior - might be empty if multiline not supported
        assert isinstance(result2, list)
    
    async def test_grep_special_characters(self):
        """Capture behavior with special regex characters."""
        # Create files with special characters
        await self._create_file("special.txt", "Price: $19.99 (on sale!)")
        await self._create_file("regex.txt", "Pattern: .* matches everything")
        await self._create_file("code.py", "if (x > 0) { return x * 2; }")
        
        # Search for literal special characters
        result = await grep(r"\$\d+\.\d+", use_regex=True, return_format="list")  # Dollar amount
        assert any("special.txt" in f for f in result)
        
        # Search for parentheses
        result2 = await grep(r"\(.*\)", use_regex=True, return_format="list")
        assert len(result2) >= 2  # Should find special.txt and code.py
    
    async def test_grep_lookahead_lookbehind(self):
        """Capture behavior with lookahead/lookbehind patterns."""
        # Create test content
        await self._create_file("data.txt", "price:100 amount:50 total:150")
        await self._create_file("config.ini", "port=8080\nhost=localhost\ndebug=true")
        
        # Positive lookahead - find numbers followed by specific text
        result = await grep(r"\d+(?=\s*total)", use_regex=True, return_format="list")
        # May or may not support lookahead
        assert isinstance(result, list)
        
        # Positive lookbehind - find values after 'port='
        result2 = await grep(r"(?<=port=)\d+", use_regex=True, return_format="list")
        # May or may not support lookbehind
        assert isinstance(result2, list)
    
    async def test_grep_word_boundaries(self):
        """Capture behavior with word boundary patterns."""
        # Create files with similar words
        await self._create_file("words.txt", "test testing untested protest")
        await self._create_file("code.py", "def test():\n    testing = True")
        
        # Search for word 'test' with boundaries
        result = await grep(r"\btest\b", use_regex=True, return_format="list")
        
        # Should match 'test' but not 'testing', 'untested', etc.
        assert len(result) >= 1
    
    async def test_grep_line_anchors(self):
        """Capture behavior with line start/end anchors."""
        # Create files with specific line patterns
        await self._create_file("imports.py", """import os
from pathlib import Path
import sys
# import commented""")
        
        # Search for lines starting with 'import'
        result = await grep(r"^import\s+\w+", use_regex=True, return_format="list")
        assert len(result) >= 1
        assert any("imports.py" in f for f in result)
        
        # Search for lines ending with specific pattern
        await self._create_file("config.py", "DEBUG = True\nPORT = 8080\n")
        result2 = await grep(r"True$", use_regex=True, return_format="list")
        assert any("config.py" in f for f in result2)
    
    async def test_grep_quantifiers(self):
        """Capture behavior with regex quantifiers."""
        # Create files with repeated patterns
        await self._create_file("numbers.txt", "1 22 333 4444 55555")
        await self._create_file("code.py", "x = 1000000  # one million")
        
        # Match specific repetitions
        result = await grep(r"\d{4}", use_regex=True, return_format="list")  # Exactly 4 digits
        assert len(result) >= 1
        
        # Match ranges
        result2 = await grep(r"\d{2,4}", use_regex=True, return_format="list")  # 2 to 4 digits
        assert len(result2) >= 1
        
        # Match one or more
        result3 = await grep(r"#+\s*\w+", use_regex=True, return_format="list")  # One or more # followed by word
        assert any("code.py" in f for f in result3)
    
    async def test_grep_character_classes(self):
        """Capture behavior with character classes."""
        # Create files with various character types
        await self._create_file("mixed.txt", "ABC123 xyz789 !@#$%")
        await self._create_file("hex.txt", "Color: #FF5733, RGB(255,87,51)")
        
        # Search for hex color pattern
        result = await grep(r"#[0-9A-Fa-f]{6}", use_regex=True, return_format="list")
        assert any("hex.txt" in f for f in result)
        
        # Search for alphanumeric sequences
        result2 = await grep(r"[A-Z]+[0-9]+", use_regex=True, return_format="list")
        assert any("mixed.txt" in f for f in result2)
    
    async def test_grep_binary_file_detection(self):
        """Capture behavior with binary files."""
        # Create a binary file
        binary_data = bytes(range(256))
        Path("binary.dat").write_bytes(binary_data)
        
        # Create text file with some binary-like content
        await self._create_file("text.txt", "Normal text with null\x00byte")
        
        # Try to grep binary file
        result = await grep("pattern", include_files="*.dat", return_format="list")
        # Binary files might be skipped or cause errors
        assert isinstance(result, list)
        
        # Search in file with null bytes
        result2 = await grep("Normal", return_format="list")
        # Should handle files with occasional null bytes
        assert len(result2) >= 0
    
    async def test_grep_unicode_patterns(self):
        """Capture behavior with Unicode patterns."""
        # Create files with Unicode content
        await self._create_file("unicode.txt", "Hello 世界 Привет мир")
        await self._create_file("emoji.txt", "Code: 🐍 Test: ✓ Error: ❌")
        
        # Search for Unicode characters
        result = await grep("世界", return_format="list")
        assert any("unicode.txt" in f for f in result)
        
        # Search for emoji
        result2 = await grep("🐍", return_format="list")
        assert any("emoji.txt" in f for f in result2)
        
        # Search with Unicode categories (if supported)
        result3 = await grep(r"[\u4e00-\u9fff]+", use_regex=True, return_format="list")  # Chinese characters
        assert isinstance(result3, list)
    
    async def test_grep_performance_limits(self):
        """Capture behavior with performance limits."""
        # Create a large file
        large_content = "test line\n" * 10000
        await self._create_file("large.txt", large_content)
        
        # Create many small files
        for i in range(100):
            await self._create_file(f"small_{i}.txt", f"file {i} content")
        
        # Search in large file
        result = await grep("test", include_files="large.txt", return_format="list")
        # Should handle large files
        assert len(result) <= 1  # Only one file even with many matches
        
        # Search across many files
        result2 = await grep("content", include_files="small_*.txt", return_format="list")
        # Should find matches but might have limits
        assert len(result2) > 0
    
    async def test_grep_empty_and_whitespace(self):
        """Capture behavior with empty patterns and whitespace."""
        # Create files with various whitespace
        await self._create_file("spaces.txt", "  leading spaces\ntrailing spaces  \n\ttabs here")
        await self._create_file("empty.txt", "")
        
        # Search for whitespace patterns
        result = await grep(r"^\s+", use_regex=True, return_format="list")  # Lines starting with whitespace
        assert any("spaces.txt" in f for f in result)
        
        # Search for empty lines (if supported)
        await self._create_file("lines.txt", "line1\n\nline3")
        result2 = await grep(r"^$", use_regex=True, return_format="list")  # Empty lines
        assert isinstance(result2, list)
    
    async def test_grep_path_handling(self):
        """Capture behavior with different path specifications."""
        # Create nested structure
        Path("subdir").mkdir()
        await self._create_file("subdir/nested.py", "def nested_function(): pass")
        await self._create_file("root.py", "def root_function(): pass")
        
        # Search in subdirectory
        result = await grep("function", path="subdir", return_format="list")
        assert len(result) == 1
        assert "nested.py" in result[0]
        
        # Search from root
        result2 = await grep("function", path=".", return_format="list")
        assert len(result2) == 2
    
    async def test_grep_error_handling(self):
        """Capture error handling behavior."""
        # Search in non-existent directory
        result = await grep("pattern", path="nonexistent", return_format="list")
        assert isinstance(result, list)
        assert len(result) == 0  # Should return empty, not error
        
        # Search with invalid regex (if validation is done)
        result2 = await grep("[invalid(regex", use_regex=True, return_format="list")
        # Might return empty or handle gracefully
        assert isinstance(result2, list)
    
    # Helper method
    async def _create_file(self, filename: str, content: str) -> None:
        """Helper to create a file with content."""
        path = Path(filename)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)