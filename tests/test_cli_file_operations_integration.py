"""
Integration tests for CLI file operations.
Tests end-to-end scenarios combining search, read, update, and create operations.
"""
import os
import tempfile
import pytest
from pathlib import Path
from tunacode.tools.glob import glob
from tunacode.tools.grep import grep
from tunacode.tools.read_file import read_file
from tunacode.tools.write_file import write_file
from tunacode.tools.update_file import update_file
from tunacode.tools.list_dir import list_dir
from pydantic_ai import ModelRetry

pytestmark = pytest.mark.asyncio


class TestFileOperationsIntegration:
    """Integration tests for file operation workflows."""
    
    def setup_method(self):
        """Create a temporary directory for test files."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
    
    def teardown_method(self):
        """Clean up temporary files and restore directory."""
        os.chdir(self.original_cwd)
        import shutil
        shutil.rmtree(self.temp_dir)
    
    async def test_search_read_update_workflow(self):
        """Test workflow: Search for files → Read content → Update content → Verify."""
        # Arrange - Create test files
        await write_file("module1.py", "def hello():\n    return 'Hello World'")
        await write_file("module2.py", "def greet():\n    return 'Hello World'")
        await write_file("test_module.py", "# Test for modules\nassert hello() == 'Hello World'")
        
        # Act 1: Search for files containing 'Hello World'
        files_with_hello = await grep("Hello World", include_files="*.py", return_format="list")
        
        # Assert 1: Found all files
        assert len(files_with_hello) == 3
        assert all(f.endswith('.py') for f in files_with_hello)
        
        # Act 2: Read each file and update 'Hello World' to 'Hello Universe'
        for file_path in files_with_hello:
            content = await read_file(file_path)
            assert 'Hello World' in content
            
            await update_file(
                file_path,
                target='Hello World',
                patch='Hello Universe'
            )
        
        # Act 3: Verify updates
        for file_path in files_with_hello:
            updated_content = await read_file(file_path)
            assert 'Hello Universe' in updated_content
            assert 'Hello World' not in updated_content
        
        # Act 4: Search again to confirm no 'Hello World' remains
        files_with_old = await grep("Hello World", include_files="*.py", return_format="list")
        assert len(files_with_old) == 0
        
        # Act 5: Confirm 'Hello Universe' is found
        files_with_new = await grep("Hello Universe", include_files="*.py", return_format="list")
        assert len(files_with_new) == 3
    
    async def test_create_search_read_update_workflow(self):
        """Test workflow: Create new file → Search for it → Read to verify → Update it."""
        # Act 1: Create a configuration file
        config_content = """{
    "version": "1.0.0",
    "debug": false,
    "server": {
        "host": "localhost",
        "port": 8080
    }
}"""
        await write_file("config.json", config_content)
        
        # Act 2: Search for JSON files
        json_files = await glob("**/*.json")
        assert "config.json" in json_files
        
        # Act 3: Read and verify content
        content = await read_file("config.json")
        assert '"version": "1.0.0"' in content
        assert '"port": 8080' in content
        
        # Act 4: Update the port number
        await update_file(
            "config.json",
            target='"port": 8080',
            patch='"port": 9090'
        )
        
        # Act 5: Read and verify update
        updated = await read_file("config.json")
        assert '"port": 9090' in updated
        assert '"port": 8080' not in updated
        
        # Act 6: Create another config and search for all configs
        await write_file("config.dev.json", '{"env": "development"}')
        all_configs = await glob("config*.json")
        assert len(all_configs) == 2
        assert "config.json" in all_configs
        assert "config.dev.json" in all_configs
    
    async def test_batch_file_operations(self):
        """Test batch operations: Create multiple files → Search → Update all matches."""
        # Act 1: Create multiple test files with similar content
        test_files = []
        for i in range(5):
            filename = f"test_{i}.py"
            content = f"""import unittest

class Test{i}(unittest.TestCase):
    def test_placeholder(self):
        # TODO: implement test
        pass
"""
            await write_file(filename, content)
            test_files.append(filename)
        
        # Act 2: Search for all files with TODO comments
        todo_files = await grep("TODO:", include_files="test_*.py", return_format="list")
        assert len(todo_files) == 5
        
        # Act 3: Read all files and update TODO to actual test
        for file_path in todo_files:
            await update_file(
                file_path,
                target="# TODO: implement test\n        pass",
                patch="self.assertEqual(1 + 1, 2)"
            )
        
        # Act 4: Verify all files were updated
        for file_path in test_files:
            content = await read_file(file_path)
            assert "self.assertEqual(1 + 1, 2)" in content
            assert "TODO" not in content
        
        # Act 5: Search to confirm no TODOs remain
        remaining_todos = await grep("TODO", include_files="test_*.py", return_format="list")
        assert len(remaining_todos) == 0
    
    async def test_nested_directory_operations(self):
        """Test operations on nested directory structures."""
        # Act 1: Create nested directory structure
        structure = {
            "src/main.py": "from .utils import helper\n\ndef main():\n    return helper()",
            "src/utils.py": "def helper():\n    return 'Helper function'",
            "src/models/user.py": "class User:\n    pass",
            "src/models/product.py": "class Product:\n    pass",
            "tests/test_main.py": "from src.main import main\n\ndef test_main():\n    assert main() == 'Helper function'",
            "docs/api.md": "# API Documentation\n\n## User Model\n## Product Model",
        }
        
        for path, content in structure.items():
            file_path = Path(path)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            await write_file(str(file_path), content)
        
        # Act 2: List directory to verify structure
        root_items = await list_dir(".")
        assert "src/" in root_items
        assert "tests/" in root_items
        assert "docs/" in root_items
        
        # Act 3: Search for Python files recursively
        py_files = await glob("**/*.py")
        assert len(py_files) == 5
        assert all(f.endswith('.py') for f in py_files)
        
        # Act 4: Search for class definitions
        class_files = await grep(r"^class \w+:", include_files="**/*.py", return_format="list", use_regex=True)
        assert len(class_files) == 2
        assert all("models" in f for f in class_files)
        
        # Act 5: Update imports in main.py
        await update_file(
            "src/main.py",
            target="from .utils import helper",
            patch="from .utils import helper\nfrom .models.user import User"
        )
        
        # Act 6: Verify the update
        main_content = await read_file("src/main.py")
        assert "from .models.user import User" in main_content
    
    async def test_file_not_found_error_handling(self):
        """Test error handling for non-existent files."""
        # Test read non-existent file
        result = await read_file("does_not_exist.txt")
        assert "File not found" in result
        
        # Test update non-existent file
        with pytest.raises(ModelRetry) as exc_info:
            await update_file("does_not_exist.txt", target="foo", patch="bar")
        assert "not found" in str(exc_info.value)
        
        # Test glob with non-existent pattern
        results = await glob("*.nonexistent")
        assert len(results) == 0
        
        # Test grep in non-existent directory
        results = await grep("pattern", path="nonexistent_dir", return_format="list")
        assert len(results) == 0
    
    async def test_unicode_content_operations(self):
        """Test operations with unicode content and filenames."""
        # Create files with unicode content
        await write_file("unicode.txt", "Hello 世界 🌍\nПривет мир\nΓειά σου κόσμε")
        await write_file("emoji.py", "# 🐍 Python\ndef greet():\n    return '👋 Hello!'")
        
        # Search for unicode content
        chinese_files = await grep("世界", return_format="list")
        assert "unicode.txt" in chinese_files
        
        emoji_files = await grep("🐍", include_files="*.py", return_format="list")
        assert "emoji.py" in emoji_files
        
        # Read and verify unicode preservation
        content = await read_file("unicode.txt")
        assert "世界" in content
        assert "Привет" in content
        assert "Γειά" in content
        
        # Update unicode content
        await update_file(
            "unicode.txt",
            target="Hello 世界 🌍",
            patch="你好 World 🌏"
        )
        
        updated = await read_file("unicode.txt")
        assert "你好 World 🌏" in updated
    
    async def test_concurrent_read_operations(self):
        """Test multiple concurrent read operations."""
        # Create multiple files
        files = []
        for i in range(10):
            filename = f"file_{i}.txt"
            await write_file(filename, f"Content of file {i}")
            files.append(filename)
        
        # Read all files (simulating concurrent reads)
        contents = []
        for filename in files:
            content = await read_file(filename)
            contents.append(content)
        
        # Verify all reads succeeded
        assert len(contents) == 10
        for i, content in enumerate(contents):
            assert f"Content of file {i}" in content
    
    async def test_search_with_complex_patterns(self):
        """Test searching with complex regex patterns."""
        # Create test files with various patterns
        await write_file("email.txt", "Contact: user@example.com or admin@test.org")
        await write_file("phone.txt", "Call: +1-555-123-4567 or (555) 987-6543")
        await write_file("code.py", "def validate_email(email):\n    # Check for @\n    return '@' in email")
        
        # Search for email patterns
        email_pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
        email_files = await grep(email_pattern, return_format="list", use_regex=True)
        assert "email.txt" in email_files
        
        # Search for phone patterns
        phone_pattern = r"(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}"
        phone_files = await grep(phone_pattern, return_format="list", use_regex=True)
        assert "phone.txt" in phone_files
        
        # Search for function definitions
        func_pattern = r"^def\s+\w+\s*\([^)]*\):"
        func_files = await grep(func_pattern, include_files="*.py", return_format="list", use_regex=True)
        assert "code.py" in func_files