# TunaCode Testing Documentation

This directory contains documentation for testing approaches, best practices, and troubleshooting guides for the TunaCode project.

## Overview

TunaCode uses a comprehensive testing strategy that includes:

- **Unit Tests**: Test individual components in isolation
- **Integration Tests**: Test component interactions
- **Characterization Tests**: Document and verify current system behavior
- **End-to-End Tests**: Test complete user workflows

## Test Structure

```
tests/
├── characterization/          # Characterization tests (behavior documentation)
│   ├── commands/             # CLI command behavior tests
│   ├── repl/                 # REPL behavior tests
│   └── agent/                # Agent behavior tests
├── integration/              # Integration tests
├── unit/                     # Unit tests
└── conftest.py              # Test configuration and fixtures
```

## Key Testing Principles

1. **Characterization Tests Document Reality**: These tests capture current behavior, not intended behavior
2. **Mock External Dependencies**: Network calls, file system operations, and complex dependencies are mocked
3. **Predictable Test Data**: Use consistent, realistic test data
4. **Clear Test Names**: Test names should describe the behavior being tested

## Quick Links

- [Characterization Testing Guide](characterization-testing.md)
- [Test Mocking Strategies](mocking-strategies.md)
- [Troubleshooting Test Issues](troubleshooting.md)

## Running Tests

```bash
# Run all tests
uv run pytest

# Run specific test categories
uv run pytest tests/characterization/
uv run pytest tests/unit/

# Run with verbose output
uv run pytest -v

# Run specific test
uv run pytest tests/characterization/test_characterization_commands.py::TestCommandBehaviors::test_model_command_switch_model -v
```
