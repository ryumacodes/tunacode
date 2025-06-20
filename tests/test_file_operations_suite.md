# File Operations Test Suite

## Overview

This test suite ensures the CLI agent can reliably perform all core file operations: **Search (grep)**, **Read**, **Update**, and **Create**. Each operation should be tested in various scenarios to ensure robustness and reliability.

## Test Categories

### 1. Search Operations (grep)

#### Basic Search Tests
- **test_search_simple_string**: Search for a simple string across all files
- **test_search_with_file_pattern**: Search within specific file patterns (*.py, *.js)
- **test_search_regex_patterns**: Search using regex patterns with `use_regex=True`
- **test_search_case_sensitive**: Test case-sensitive vs case-insensitive search
- **test_search_empty_results**: Verify behavior when no matches found
- **test_search_return_formats**: Test both string and list return formats

#### Advanced Search Tests
- **test_search_nested_directories**: Search in deeply nested directory structures
- **test_search_large_files**: Search in files > 10MB
- **test_search_binary_files**: Handle binary files gracefully
- **test_search_with_excludes**: Test exclude patterns
- **test_search_unicode_content**: Search for unicode/emoji content
- **test_search_performance**: Ensure search completes within 3-second deadline

### 2. Read Operations

#### Basic Read Tests
- **test_read_simple_file**: Read a basic text file
- **test_read_with_line_numbers**: Verify line numbers are included
- **test_read_partial_file**: Read with offset and limit parameters
- **test_read_empty_file**: Handle empty files correctly
- **test_read_nonexistent_file**: Appropriate error for missing files

#### Advanced Read Tests
- **test_read_large_file**: Read files > 100MB efficiently
- **test_read_binary_detection**: Detect and handle binary files
- **test_read_various_encodings**: UTF-8, UTF-16, Latin-1, etc.
- **test_read_special_characters**: Files with null bytes, control characters
- **test_read_permission_errors**: Handle permission denied gracefully
- **test_read_symlinks**: Follow or not follow symlinks appropriately

### 3. Update Operations

#### Basic Update Tests
- **test_update_simple_replacement**: Basic string replacement
- **test_update_multiline_content**: Update across multiple lines
- **test_update_preserve_formatting**: Maintain indentation and whitespace
- **test_update_file_not_exists**: Error when updating non-existent file
- **test_update_empty_to_content**: Update empty file with content

#### Advanced Update Tests
- **test_update_concurrent_edits**: Handle concurrent modifications
- **test_update_large_files**: Update in files > 50MB
- **test_update_regex_patterns**: Update using regex patterns
- **test_update_preserve_permissions**: Maintain file permissions/ownership
- **test_update_backup_creation**: Create backups before updates
- **test_update_atomic_operations**: Ensure updates are atomic

### 4. Create Operations

#### Basic Create Tests
- **test_create_simple_file**: Create basic text file
- **test_create_with_content**: Create file with initial content
- **test_create_nested_directories**: Create dirs as needed
- **test_create_already_exists**: Fail when file exists
- **test_create_empty_file**: Create empty file

#### Advanced Create Tests
- **test_create_with_permissions**: Set specific permissions
- **test_create_various_types**: .py, .js, .json, .md, etc.
- **test_create_unicode_filenames**: Handle unicode in filenames
- **test_create_large_content**: Create with > 10MB content
- **test_create_special_paths**: Handle spaces, special chars in paths
- **test_create_atomic_creation**: Ensure atomic file creation

## Integration Test Scenarios

### Workflow Tests

#### 1. Search → Read → Update
```python
async def test_search_read_update_workflow():
    # Create test files
    await create_file("config.json", '{"debug": true}')
    await create_file("settings.json", '{"debug": false}')
    
    # Search for files with "debug"
    files = await grep("debug", include_files="*.json", return_format="list")
    assert len(files) == 2
    
    # Read each file and update
    for file in files:
        content = await read_file(file)
        updated = content.replace('"debug": true', '"debug": false')
        await update_file(file, content, updated)
    
    # Verify updates
    results = await grep('"debug": true', include_files="*.json", return_format="list")
    assert len(results) == 0
```

#### 2. Create → Search → Read → Update
```python
async def test_create_search_read_update_workflow():
    # Create multiple files with patterns
    files_created = []
    for i in range(5):
        filename = f"test_{i}.py"
        content = f"def function_{i}():\n    # TODO: implement\n    pass"
        await create_file(filename, content)
        files_created.append(filename)
    
    # Search for TODO comments
    todo_files = await grep("TODO:", include_files="*.py", return_format="list")
    assert len(todo_files) == 5
    
    # Read and update each file
    for file in todo_files:
        content = await read_file(file)
        updated = content.replace("# TODO: implement", "# Implemented")
        await update_file(file, content, updated)
    
    # Verify no TODOs remain
    remaining = await grep("TODO:", include_files="*.py", return_format="list")
    assert len(remaining) == 0
```

#### 3. Batch Operations
```python
async def test_batch_file_operations():
    # Create batch of files
    created_files = []
    for ext in ['py', 'js', 'tsx', 'json']:
        for i in range(3):
            filename = f"component_{i}.{ext}"
            await create_file(filename, f"// File {i}")
            created_files.append(filename)
    
    # Search across different file types
    py_files = await grep("File", include_files="*.py", return_format="list")
    js_files = await grep("File", include_files="*.js", return_format="list")
    all_files = await grep("File", return_format="list")
    
    assert len(py_files) == 3
    assert len(js_files) == 3
    assert len(all_files) == 12
```

## Error Handling Tests

### 1. Permission Errors
- Test read/write operations on files without permissions
- Verify appropriate error messages

### 2. Path Validation
- Test with invalid paths (null bytes, too long, invalid chars)
- Test with relative vs absolute paths

### 3. Concurrent Access
- Multiple reads of same file
- Read while another process is writing
- Update conflicts

### 4. Resource Limits
- Max file size handling
- Max search results
- Memory usage with large operations

## Performance Tests

### 1. Large Scale Operations
```python
async def test_performance_large_scale():
    # Create 1000 files
    start = time.time()
    for i in range(1000):
        await create_file(f"perf_test_{i}.txt", f"Content {i}")
    create_time = time.time() - start
    assert create_time < 30  # Should complete within 30 seconds
    
    # Search across all files
    start = time.time()
    results = await grep("Content", include_files="perf_test_*.txt", return_format="list")
    search_time = time.time() - start
    assert search_time < 3  # Should complete within 3 seconds
    assert len(results) == 1000
```

### 2. Parallel Operations
```python
async def test_parallel_read_operations():
    # Create test files
    files = []
    for i in range(10):
        filename = f"parallel_{i}.txt"
        await create_file(filename, f"Content {i}" * 1000)
        files.append(filename)
    
    # Read all files in parallel
    start = time.time()
    read_tasks = [read_file(f) for f in files]
    contents = await asyncio.gather(*read_tasks)
    parallel_time = time.time() - start
    
    # Compare with sequential
    start = time.time()
    sequential_contents = []
    for f in files:
        content = await read_file(f)
        sequential_contents.append(content)
    sequential_time = time.time() - start
    
    # Parallel should be significantly faster
    assert parallel_time < sequential_time * 0.5
    assert contents == sequential_contents
```

## Best Practices

### 1. Test Data Management
- Use temporary directories for test files
- Clean up after each test
- Use meaningful test file names and content

### 2. Assertions
- Check both positive and negative cases
- Verify file contents, not just operation success
- Test edge cases and boundary conditions

### 3. Error Messages
- Verify error messages are helpful and specific
- Test error recovery mechanisms
- Ensure no data loss on errors

### 4. Performance
- Set reasonable timeouts
- Test with realistic file sizes
- Monitor memory usage

### 5. Platform Compatibility
- Test path separators (/ vs \)
- Handle line endings (LF vs CRLF)
- Consider file system limitations

## Test Implementation Template

```python
import asyncio
import tempfile
import os
from pathlib import Path
import pytest

class TestFileOperations:
    """Comprehensive test suite for file operations."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for tests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            os.chdir(tmpdir)
            yield tmpdir
            os.chdir(original_cwd)
    
    async def test_example_workflow(self, temp_dir):
        """Example test following best practices."""
        # Arrange - Create test data
        test_content = "Hello, World!"
        test_file = "test.txt"
        
        # Act - Perform operations
        await create_file(test_file, test_content)
        files = await grep("Hello", return_format="list")
        content = await read_file(test_file)
        await update_file(test_file, "Hello", "Hi")
        
        # Assert - Verify results
        assert len(files) == 1
        assert test_file in files[0]
        assert "Hello, World!" in content
        
        # Verify update
        updated_content = await read_file(test_file)
        assert "Hi, World!" in updated_content
        assert "Hello" not in updated_content
```

## Coverage Goals

- **Line Coverage**: > 90% for all file operation tools
- **Branch Coverage**: > 85% for error handling paths
- **Integration Coverage**: All major workflows tested
- **Performance Benchmarks**: Established baselines for all operations

## Continuous Improvement

1. **Monitor Failures**: Track flaky tests and improve reliability
2. **Add Scenarios**: As bugs are found, add regression tests
3. **Performance Tracking**: Monitor performance over time
4. **User Feedback**: Add tests based on real-world usage patterns