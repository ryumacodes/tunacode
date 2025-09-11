# Characterization Testing Guide

## What are Characterization Tests?

Characterization tests (also known as "golden master" or "approval" tests) are a type of test that captures the current behavior of existing code. Unlike traditional unit tests that verify intended behavior, characterization tests document what the system actually does.

## When to Use Characterization Tests

- **Legacy Code**: When working with code that lacks comprehensive tests
- **Refactoring**: To ensure behavior doesn't change during code restructuring
- **Behavior Documentation**: To document how complex systems currently work
- **Regression Prevention**: To catch unintended changes in system behavior

## Best Practices for Characterization Tests

### 1. Document Current Reality, Not Intended Behavior

```python
# ❌ Bad - Tests what we think should happen
async def test_model_command_validates_format(self):
    """Test that ModelCommand validates model format."""
    # This assumes validation exists, but it doesn't

# ✅ Good - Tests what actually happens
async def test_model_command_search_behavior(self):
    """Test ModelCommand treats non-colon input as search query."""
    # This documents the actual search behavior
```

### 2. Use Realistic Test Data

```python
# ❌ Bad - Uses non-existent model
assert context.state_manager.session.current_model == "anthropic:claude-3"

# ✅ Good - Uses realistic model ID or mocks appropriately
assert context.state_manager.session.current_model == "anthropic:claude-3.5-sonnet"
```

### 3. Mock External Dependencies

```python
# ✅ Good - Mock the models registry to avoid network calls
mock_registry = mock.Mock()
mock_registry.get_model.return_value = None
mock_registry.search_models.return_value = []
cmd.registry = mock_registry
cmd._registry_loaded = True
```

## When Characterization Tests Fail

When a characterization test fails, you have three options:

### 1. Fix the Code (if test documents correct behavior)
- The test represents the intended behavior
- The code has a bug or regression
- Fix the implementation to match the test

### 2. Update the Test (if code behavior improved)
- The code behavior has legitimately improved
- The test documents outdated behavior
- Update the test to match the new (better) behavior

### 3. Investigate Further (if unclear)
- Determine which is correct: the test or the code
- Consider the user experience impact
- Make an informed decision based on requirements

## Example: ModelCommand Test Updates

### Original Failing Test
```python
async def test_model_command_switch_model(self):
    """Test ModelCommand switching to new model."""
    # This failed because "anthropic:claude-3" doesn't exist
    result = await cmd.execute(["anthropic:claude-3"], context)
    assert context.state_manager.session.current_model == "anthropic:claude-3"
```

### Updated Test (Option 2: Update Test)
```python
async def test_model_command_switch_model(self):
    """Test ModelCommand switching to new model."""
    # Mock registry to provide predictable behavior
    mock_registry = mock.Mock()
    mock_registry.get_model.return_value = None
    cmd.registry = mock_registry

    result = await cmd.execute(["anthropic:claude-3.5-sonnet"], context)
    # Test documents actual behavior: model is set even if not in registry
    assert context.state_manager.session.current_model == "anthropic:claude-3.5-sonnet"
    mock_warning.assert_called_with("Model not found in registry - setting anyway")
```

## Decision Framework

Ask these questions when a characterization test fails:

1. **Has the code behavior actually changed?**
   - If yes: Is the new behavior better for users?

2. **Was the test making incorrect assumptions?**
   - If yes: Update the test to reflect reality

3. **Is this a regression?**
   - If yes: Fix the code to restore correct behavior

4. **Is the current behavior user-friendly?**
   - If more user-friendly: Update test
   - If less user-friendly: Fix code

## Common Patterns in TunaCode

### Command Testing Pattern
```python
async def test_command_behavior(self):
    """Test specific command behavior."""
    cmd = commands.SomeCommand()
    context = mock.Mock()

    # Mock external dependencies
    with mock.patch("tunacode.ui.console.info") as mock_info:
        result = await cmd.execute(args, context)

    # Assert actual behavior
    mock_info.assert_called_with("expected message")
    assert result == expected_result
```

### Registry Mocking Pattern
```python
# Mock the models registry for predictable results
mock_registry = mock.Mock()
mock_registry.search_models.return_value = []
cmd.registry = mock_registry
cmd._registry_loaded = True
```

## Troubleshooting

See [troubleshooting.md](troubleshooting.md) for common test issues and solutions.
