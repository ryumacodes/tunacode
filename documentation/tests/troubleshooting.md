# Testing Troubleshooting Guide

This guide covers common testing issues and their solutions in the TunaCode project.

## Common Import Errors

### `ModuleNotFoundError: No module named 'prompt_toolkit.application.application'`

**Problem**: The test stubs in `tests/conftest.py` are missing required classes.

**Solution**: Add the missing class to the appropriate stub module:

```python
# In tests/conftest.py
application = types.ModuleType("prompt_toolkit.application")

class Application:
    def __init__(self, *args, **kwargs):
        pass
    async def run_async(self):
        return None

application.Application = Application
```

### `ModuleNotFoundError: No module named 'defusedxml'`

**Problem**: Missing dependency that's not in the main requirements.

**Solution**: Add the dependency using UV:

```bash
uv add defusedxml
uv sync
```

### `ImportError: cannot import name 'StyleAndTextTuples'`

**Problem**: Missing type alias in the prompt_toolkit stub.

**Solution**: Add the type alias to the stub:

```python
# In tests/conftest.py, in the formatted_text section
StyleAndTextTuples = list
formatted_text.StyleAndTextTuples = StyleAndTextTuples
```

## Test Environment Issues

### Tests Not Finding Dependencies

**Problem**: Dependencies installed but not found during test runs.

**Diagnosis**: Check if using the correct environment:

```bash
# Check if dependency is available
uv run python -c "import defusedxml; print('Available')"

# Run tests with UV
uv run pytest tests/path/to/test.py -v
```

**Solution**: Always use `uv run` for test execution to ensure correct environment.

### Characterization Tests Failing After Code Changes

**Problem**: Tests fail because they document old behavior.

**Diagnosis**: Determine if the behavior change is intentional:

1. **Is the new behavior better for users?** → Update the test
2. **Is this a regression?** → Fix the code
3. **Unclear?** → Investigate requirements

**Example Fix**: Update test to match new (better) behavior:

```python
# Before: Expected strict validation
mock_error.assert_called_once()
assert "provider prefix" in str(mock_error.call_args)

# After: Documents actual search behavior
mock_registry.search_models.assert_called_once_with("gpt-4")
mock_error.assert_called_once_with("No models found matching 'gpt-4'")
```

## Mock-Related Issues

### Mock Not Being Called

**Problem**: `mock.assert_called_once()` fails even though the function should be called.

**Diagnosis**: Check the mock target path:

```python
# ❌ Wrong path - might not match actual import
with mock.patch("tunacode.ui.error") as mock_error:

# ✅ Correct path - matches how it's imported
with mock.patch("tunacode.ui.console.error") as mock_error:
```

### Registry Not Loading in Tests

**Problem**: ModelsRegistry fails to load during tests.

**Solution**: Mock the registry instead of trying to load it:

```python
# Don't try to load real registry
mock_registry = mock.Mock()
mock_registry.get_model.return_value = None
mock_registry.search_models.return_value = []
cmd.registry = mock_registry
cmd._registry_loaded = True
```

## Async Test Issues

### `RuntimeError: Event loop is closed`

**Problem**: Async test cleanup issues.

**Solution**: Ensure proper async test setup:

```python
# Use pytest-asyncio
@pytest.mark.asyncio
async def test_async_function(self):
    result = await some_async_function()
    assert result is not None
```

### Mock Async Functions

**Problem**: Mocking async functions incorrectly.

**Solution**: Use `AsyncMock` for async functions:

```python
from unittest.mock import AsyncMock

# For async functions
mock_func = AsyncMock(return_value="result")

# For regular functions
mock_func = mock.Mock(return_value="result")
```

## Test Data Issues

### Using Non-Existent Model IDs

**Problem**: Tests use model IDs that don't exist in the registry.

**Solution**: Use realistic model IDs or mock appropriately:

```python
# ❌ Non-existent model
"anthropic:claude-3"

# ✅ Realistic model ID
"anthropic:claude-3.5-sonnet"

# ✅ Or mock the registry
mock_registry.get_model.return_value = MockModel()
```

## Debugging Test Failures

### Enable Verbose Output

```bash
uv run pytest -v tests/path/to/test.py
```

### Capture Print Statements

```bash
uv run pytest -s tests/path/to/test.py
```

### Run Single Test

```bash
uv run pytest tests/path/to/test.py::TestClass::test_method -v
```

### Debug with Print Statements

```python
async def test_something(self):
    result = await cmd.execute(["arg"], context)
    print(f"Result: {result}")  # Will show with -s flag
    print(f"Mock calls: {mock_func.call_args_list}")
    assert result is not None
```

## Environment Setup Checklist

When setting up testing environment:

1. ✅ Install all dependencies: `uv sync`
2. ✅ Check test stubs in `tests/conftest.py` are complete
3. ✅ Use `uv run pytest` for test execution
4. ✅ Mock external dependencies (network, filesystem)
5. ✅ Use realistic test data or proper mocks

## Getting Help

If you encounter issues not covered here:

1. Check the test output carefully for specific error messages
2. Look at similar working tests for patterns
3. Verify mock target paths match actual imports
4. Consider whether behavior changes are intentional
5. Update documentation when you solve new issues
