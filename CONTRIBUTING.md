# Contributing to TunaCode

Thank you for your interest in contributing to TunaCode! This guide will help you set up a development environment and understand our development workflow.

## Development Setup

### Prerequisites

- Python 3.10 or higher
- git
- make (optional but recommended)

### Setting Up Your Development Environment

1. **Clone the repository**
   ```bash
   git clone https://github.com/larock22/tunacode.git
   cd tunacode
   ```

2. **Run the development setup script**
   ```bash
   ./scripts/setup_dev_env.sh
   ```

   This script will:
   - Create a fresh virtual environment in `venv/`
   - Install TunaCode in editable mode
   - Install all development dependencies
   - Verify the installation

3. **Activate the virtual environment**
   ```bash
   source venv/bin/activate
   ```

### Manual Setup (Alternative)

If you prefer to set up manually:

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Upgrade pip
pip install --upgrade pip

# Install in editable mode with dev dependencies
pip install -e ".[dev]"

# Install additional test dependencies
pip install pytest-asyncio
```

## Development Workflow

### Running Tests

```bash
# Run all tests
make test

# Or directly with pytest
venv/bin/pytest

# Run specific test file
venv/bin/pytest tests/test_agent_initialization.py

# Run with coverage
make coverage
```

### Linting and Code Style

We use black, isort, and flake8 for code formatting and linting:

```bash
# Run all linters
make lint

# This runs:
# - black (code formatter)
# - isort (import sorter)
# - flake8 (style checker)
```

**Important**: Always run `make lint` before committing code. The linters will automatically fix most issues.

### Building the Package

```bash
# Build distribution packages
make build

# Clean build artifacts
make clean
```

## Project Structure

```
tunacode/
├── src/tunacode/       # Main package source
│   ├── cli/            # Command-line interface
│   ├── core/           # Core functionality (agents, state, tools)
│   ├── tools/          # Tool implementations
│   ├── ui/             # User interface components
│   └── utils/          # Utility functions
├── tests/              # Test files
├── scripts/            # Development and installation scripts
├── documentation/      # Additional documentation
└── venv/              # Virtual environment (not committed)
```

## Testing Guidelines

1. **Async Tests**: Use `@pytest.mark.asyncio` for async test functions
2. **Mocking**: Mock external dependencies, especially API calls
3. **Coverage**: Aim for high test coverage for new features
4. **Test Organization**: Place tests in `tests/` with descriptive names

Example test:
```python
import pytest
from unittest.mock import MagicMock

@pytest.mark.asyncio
async def test_my_async_function():
    # Your test code here
    pass
```

## Common Issues

### Virtual Environment Issues

If you encounter issues with the virtual environment:

1. **Wrong Python in venv**: Delete and recreate the venv
   ```bash
   rm -rf venv
   python3 -m venv venv
   source venv/bin/activate
   pip install -e ".[dev]"
   ```

2. **Import errors in tests**: Ensure TunaCode is installed in editable mode
   ```bash
   pip install -e .
   ```

3. **Linting tools not found**: Make sure you're using the venv
   ```bash
   which python  # Should show /path/to/tunacode/venv/bin/python
   ```

### Test Issues

1. **Async test warnings**: Install pytest-asyncio
   ```bash
   pip install pytest-asyncio
   ```

2. **Import errors**: Ensure you're in the project root when running tests

## Submitting Changes

1. Create a new branch for your feature/fix
2. Make your changes
3. Run tests and linting
4. Commit with descriptive messages
5. Push and create a pull request

## Questions?

If you have questions or run into issues, please:
- Check existing issues on GitHub
- Create a new issue with details about your problem
- Include your Python version and OS