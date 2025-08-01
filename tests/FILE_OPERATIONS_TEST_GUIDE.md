# File Operations Test Guide

## Quick Reference

This guide provides best practices for testing the core file operations (Search/Read/Update/Create) in the TunaCode CLI agent.

## Test Organization

### 1. Test Files Structure
```
tests/
├── test_core_file_operations.py      # Main comprehensive test suite
├── test_file_operations_suite.md     # Detailed test plan documentation
├── FILE_OPERATIONS_TEST_GUIDE.md     # This guide
├── test_tool_combinations.py         # Integration workflow tests
├── test_cli_file_operations_integration.py  # CLI-specific integration tests
└── test_file_operations_edge_cases.py      # Edge case and error scenarios
```

### 2. Core Test Categories

#### Search (grep) Tests
- **Basic**: Simple string search, file patterns, return formats
- **Advanced**: Regex patterns, case sensitivity, unicode content
- **Performance**: Large-scale searches, 3-second deadline compliance

#### Read Tests
- **Basic**: Simple reads, line numbers, partial reads (offset/limit)
- **Advanced**: Large files, various encodings, binary detection
- **Error Handling**: Missing files, permission errors, invalid paths

#### Update Tests
- **Basic**: Simple replacements, multiline updates, formatting preservation
- **Advanced**: Concurrent updates, large files, atomic operations
- **Error Handling**: Non-existent files, invalid targets, conflicts

#### Create Tests
- **Basic**: Simple file creation, nested directories, content initialization
- **Advanced**: Various file types, unicode filenames, permissions
- **Error Handling**: Existing files, invalid paths, disk space

## Best Practices

### 1. Test Structure
```python
@pytest.mark.asyncio
async def test_operation_scenario(self, temp_workspace):
    """Clear description of what is being tested."""
    # Arrange - Set up test data
    await write_file("test.txt", "Initial content")

    # Act - Perform the operation
    result = await grep("content", return_format="list")

    # Assert - Verify results
    assert len(result) == 1
    assert "test.txt" in result[0]
```

### 2. Use Fixtures for Clean Environment
```python
@pytest.fixture
async def temp_workspace(self):
    """Create isolated workspace for each test."""
    with tempfile.TemporaryDirectory() as tmpdir:
        original_cwd = os.getcwd()
        os.chdir(tmpdir)
        yield tmpdir
        os.chdir(original_cwd)
```

### 3. Test Both Success and Failure Cases
```python
# Success case
async def test_read_existing_file(self):
    await write_file("exists.txt", "content")
    content = await read_file("exists.txt")
    assert "content" in content

# Failure case
async def test_read_missing_file(self):
    with pytest.raises(Exception) as exc_info:
        await read_file("missing.txt")
    assert "not found" in str(exc_info.value).lower()
```

### 4. Use Meaningful Test Data
```python
# Good - Clear what's being tested
await write_file("config.json", '{"debug": true, "port": 3000}')
results = await grep('"debug": true', include_files="*.json", return_format="list")

# Bad - Unclear test data
await write_file("test.txt", "xyz123")
results = await grep("xyz", return_format="list")
```

### 5. Test Workflows, Not Just Individual Operations
```python
async def test_complete_workflow(self):
    """Test realistic usage: search → read → update."""
    # Create files with issues
    await write_file("app.py", "# TODO: fix bug\nprint('hello')")

    # Find files with TODOs
    todo_files = await grep("TODO:", include_files="*.py", return_format="list")

    # Fix each TODO
    for file in todo_files:
        content = await read_file(file)
        await update_file(file, "# TODO: fix bug", "# Bug fixed")

    # Verify fix
    remaining = await grep("TODO:", include_files="*.py", return_format="list")
    assert len(remaining) == 0
```

## Common Patterns

### 1. Batch Operations
```python
# Create multiple files
for i in range(10):
    await write_file(f"file_{i}.txt", f"Content {i}")

# Process all files
files = await grep("Content", return_format="list")
for file in files:
    content = await read_file(file)
    # Process content...
```

### 2. File Type Filtering
```python
# Search only Python files
py_files = await grep("import", include_files="*.py", return_format="list")

# Search multiple extensions
code_files = await grep("function", include_files="*.{js,ts,py}", return_format="list")
```

### 3. Regex Pattern Searching
```python
# Find function definitions
functions = await grep(r"^def \w+", include_files="*.py", return_format="list", use_regex=True)

# Find class definitions
classes = await grep(r"^class \w+", include_files="*.py", return_format="list", use_regex=True)
```

### 4. Safe Updates
```python
# Read original content first
original = await read_file("config.json")

# Make update
await update_file("config.json", '"old_value"', '"new_value"')

# Verify update didn't break file
updated = await read_file("config.json")
assert updated != original
assert "new_value" in updated
```

## Performance Guidelines

### 1. Set Reasonable Timeouts
- File creation: < 1 second per file
- Search operations: < 3 seconds total
- Read operations: < 0.5 seconds for files < 10MB
- Update operations: < 1 second for files < 10MB

### 2. Test at Scale
```python
@pytest.mark.slow  # Mark slow tests
async def test_large_scale():
    # Create realistic number of files
    for i in range(100):
        await write_file(f"file_{i}.py", "content")

    # Ensure search is still fast
    start = time.time()
    results = await grep("content", return_format="list")
    assert time.time() - start < 3
```

### 3. Use Parallel Operations When Safe
```python
# Parallel reads are safe
files = ["file1.txt", "file2.txt", "file3.txt"]
contents = await asyncio.gather(*[read_file(f) for f in files])

# Sequential writes for safety
for i, content in enumerate(new_contents):
    await write_file(f"output_{i}.txt", content)
```

## Error Handling Checklist

- [ ] Test with non-existent files
- [ ] Test with permission errors
- [ ] Test with invalid paths (null bytes, too long)
- [ ] Test with full disk scenarios
- [ ] Test with concurrent access
- [ ] Test with various encodings
- [ ] Test with binary files
- [ ] Test with symbolic links
- [ ] Test with very large files

## Integration with CI/CD

### Running Tests
```bash
# Run all file operation tests
pytest tests/test_core_file_operations.py -v

# Run only fast tests
pytest tests/test_core_file_operations.py -v -m "not slow"

# Run with coverage
pytest tests/test_core_file_operations.py --cov=tunacode.tools --cov-report=html
```

### Test Markers
- `@pytest.mark.slow` - Tests that take > 5 seconds
- `@pytest.mark.integration` - Tests requiring multiple tools
- `@pytest.mark.edge_case` - Tests for unusual scenarios

## Debugging Failed Tests

### 1. Add Verbose Output
```python
async def test_with_debugging(self, temp_workspace):
    # Create test file
    await write_file("test.txt", "content")
    print(f"Created file in: {temp_workspace}")

    # Search
    results = await grep("content", return_format="list")
    print(f"Search results: {results}")

    assert len(results) == 1
```

### 2. Check Intermediate States
```python
# Read file after each operation
content1 = await read_file("file.txt")
print(f"Before update: {content1}")

await update_file("file.txt", "old", "new")

content2 = await read_file("file.txt")
print(f"After update: {content2}")
```

### 3. Use Smaller Test Cases
When a test fails, create a minimal reproduction:
```python
async def test_minimal_reproduction(self):
    # Simplest case that shows the issue
    await write_file("simple.txt", "fail here")
    result = await grep("fail", return_format="list")
    assert len(result) == 1  # Debug why this fails
```

## Maintenance

### Regular Tasks
1. **Weekly**: Review test failures, update flaky tests
2. **Monthly**: Add tests for reported bugs
3. **Quarterly**: Review coverage reports, add missing tests
4. **Yearly**: Refactor test organization, update best practices

### Adding New Tests
When adding new tests:
1. Follow existing naming conventions
2. Add docstring explaining the scenario
3. Use appropriate markers (@pytest.mark.slow, etc.)
4. Ensure cleanup in fixtures
5. Run locally before committing

## Resources

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://github.com/pytest-dev/pytest-asyncio)
- [Python tempfile](https://docs.python.org/3/library/tempfile.html)
- TunaCode tool documentation in `/src/tunacode/tools/`
