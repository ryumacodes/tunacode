# Test Mocking Strategies

This document outlines effective mocking strategies used in TunaCode tests to ensure reliable, fast, and predictable testing.

## Why Mock?

Mocking is essential for:
- **Speed**: Avoid slow network calls and file operations
- **Reliability**: Tests don't depend on external services
- **Predictability**: Control exact responses and behaviors
- **Isolation**: Test specific components without dependencies

## Core Mocking Patterns

### 1. UI Function Mocking

Mock UI output functions to verify they're called correctly:

```python
# Mock single UI function
with mock.patch("tunacode.ui.console.info") as mock_info:
    await cmd.execute([], context)
    mock_info.assert_called_with("Expected message")

# Mock multiple UI functions
with mock.patch("tunacode.ui.console.error") as mock_error, \
     mock.patch("tunacode.ui.console.muted") as mock_muted:
    await cmd.execute(["invalid"], context)
    mock_error.assert_called_once_with("No models found matching 'invalid'")
    mock_muted.assert_called_once_with("Try /model --list to see all available models")
```

### 2. Models Registry Mocking

The ModelsRegistry makes network calls, so always mock it:

```python
# Basic registry mock
mock_registry = mock.Mock()
mock_registry.get_model.return_value = None
mock_registry.search_models.return_value = []
cmd.registry = mock_registry
cmd._registry_loaded = True

# Registry with search results
mock_registry.search_models.return_value = [
    MockModel("openai:gpt-4", "GPT-4"),
    MockModel("anthropic:claude-3.5-sonnet", "Claude 3.5 Sonnet")
]

# Registry with specific model
mock_model = MockModel("anthropic:claude-3.5-sonnet", "Claude 3.5 Sonnet")
mock_registry.get_model.return_value = mock_model
```

### 3. Context Object Mocking

Mock the CommandContext for command tests:

```python
context = mock.Mock()
context.state_manager.session.current_model = "openai:gpt-3.5"
context.state_manager.session.yolo = False

# After command execution, verify changes
assert context.state_manager.session.current_model == "new-model"
```

### 4. Async Function Mocking

Use `AsyncMock` for async functions:

```python
from unittest.mock import AsyncMock

# Mock async function
mock_async_func = AsyncMock(return_value="result")

# Mock method on object
mock_obj = mock.Mock()
mock_obj.async_method = AsyncMock(return_value="result")

# Verify async mock was called
mock_async_func.assert_called_once_with("expected_arg")
```

## Specific TunaCode Mocking Patterns

### Command Testing Template

```python
async def test_command_behavior(self):
    """Test specific command behavior."""
    # 1. Create command instance
    cmd = commands.SomeCommand()

    # 2. Mock context
    context = mock.Mock()
    context.state_manager.session.some_property = "initial_value"

    # 3. Mock external dependencies
    mock_registry = mock.Mock()
    mock_registry.some_method.return_value = "expected_result"
    cmd.some_dependency = mock_registry

    # 4. Mock UI functions
    with mock.patch("tunacode.ui.console.info") as mock_info:
        # 5. Execute command
        result = await cmd.execute(["arg1", "arg2"], context)

        # 6. Verify behavior
        mock_info.assert_called_with("Expected message")
        assert context.state_manager.session.some_property == "expected_value"
        assert result == "expected_result"
```

### Model Selector Mocking

```python
# Mock the interactive model selector
with mock.patch("tunacode.ui.model_selector.select_model_interactive") as mock_selector:
    mock_selector.return_value = "selected:model-id"

    result = await cmd.execute([], context)

    mock_selector.assert_called_once_with(cmd.registry, "")
    assert context.state_manager.session.current_model == "selected:model-id"
```

### File System Mocking

```python
# Mock file operations
with mock.patch("pathlib.Path.exists") as mock_exists, \
     mock.patch("pathlib.Path.read_text") as mock_read:
    mock_exists.return_value = True
    mock_read.return_value = "file content"

    result = some_file_operation()

    assert result == "processed content"
```

## Mock Verification Patterns

### Verify Function Calls

```python
# Called once with specific arguments
mock_func.assert_called_once_with("expected", "args")

# Called at least once
mock_func.assert_called()

# Never called
mock_func.assert_not_called()

# Called specific number of times
assert mock_func.call_count == 3

# Check all calls
expected_calls = [
    mock.call("first", "call"),
    mock.call("second", "call")
]
mock_func.assert_has_calls(expected_calls)
```

### Verify Mock State

```python
# Check call arguments
args, kwargs = mock_func.call_args
assert args[0] == "expected_first_arg"
assert kwargs["key"] == "expected_value"

# Check all call arguments
call_args_list = mock_func.call_args_list
assert len(call_args_list) == 2
```

## Advanced Mocking Techniques

### Side Effects

```python
# Raise exception on call
mock_func.side_effect = ValueError("Test error")

# Different return values for multiple calls
mock_func.side_effect = ["first", "second", "third"]

# Custom function behavior
def custom_behavior(arg):
    if arg == "special":
        return "special_result"
    return "default_result"

mock_func.side_effect = custom_behavior
```

### Property Mocking

```python
# Mock property
mock_obj = mock.Mock()
mock_obj.some_property = "value"

# Mock property with PropertyMock
from unittest.mock import PropertyMock
mock_obj = mock.Mock()
type(mock_obj).some_property = PropertyMock(return_value="value")
```

### Context Manager Mocking

```python
# Mock context manager
mock_context = mock.Mock()
mock_context.__enter__.return_value = mock_context
mock_context.__exit__.return_value = None

with mock.patch("some.module.ContextManager", return_value=mock_context):
    # Test code that uses the context manager
    pass
```

## Best Practices

### 1. Mock at the Right Level

```python
# ❌ Too high level - mocks too much
with mock.patch("tunacode.cli.commands.implementations.model"):

# ✅ Right level - mocks specific dependency
with mock.patch("tunacode.ui.console.error") as mock_error:
```

### 2. Use Realistic Mock Data

```python
# ❌ Unrealistic
mock_registry.get_model.return_value = "fake-model"

# ✅ Realistic
mock_model = MockModel(
    id="anthropic:claude-3.5-sonnet",
    name="Claude 3.5 Sonnet",
    provider="anthropic"
)
mock_registry.get_model.return_value = mock_model
```

### 3. Clear Mock Setup

```python
# ✅ Clear mock setup with comments
def test_model_command_with_registry(self):
    """Test model command with registry interaction."""
    cmd = commands.ModelCommand()

    # Mock registry to simulate model not found
    mock_registry = mock.Mock()
    mock_registry.get_model.return_value = None
    mock_registry.search_models.return_value = []
    cmd.registry = mock_registry
    cmd._registry_loaded = True

    # Mock UI to capture warnings
    with mock.patch("tunacode.ui.console.warning") as mock_warning:
        # Test execution...
```

### 4. Reset Mocks Between Tests

```python
def setUp(self):
    """Reset mocks before each test."""
    self.mock_registry = mock.Mock()
    self.mock_context = mock.Mock()

def tearDown(self):
    """Clean up after each test."""
    self.mock_registry.reset_mock()
    self.mock_context.reset_mock()
```

## Common Pitfalls

### 1. Wrong Mock Target

```python
# ❌ Mocking the wrong import path
with mock.patch("requests.get"):  # If code imports differently

# ✅ Mock where it's used
with mock.patch("tunacode.utils.http_client.requests.get"):
```

### 2. Not Mocking Async Functions

```python
# ❌ Regular mock for async function
mock_async = mock.Mock(return_value="result")

# ✅ AsyncMock for async function
mock_async = AsyncMock(return_value="result")
```

### 3. Forgetting to Set Mock State

```python
# ❌ Mock without proper setup
cmd.registry = mock.Mock()

# ✅ Mock with complete setup
mock_registry = mock.Mock()
mock_registry.get_model.return_value = None
cmd.registry = mock_registry
cmd._registry_loaded = True
```

## Testing the Mocks

Sometimes you need to test that your mocks work correctly:

```python
def test_mock_setup(self):
    """Verify mock setup works as expected."""
    mock_registry = mock.Mock()
    mock_registry.search_models.return_value = ["model1", "model2"]

    # Test the mock
    result = mock_registry.search_models("query")
    assert result == ["model1", "model2"]
    mock_registry.search_models.assert_called_once_with("query")
```

This ensures your test setup is correct before testing the actual functionality.
