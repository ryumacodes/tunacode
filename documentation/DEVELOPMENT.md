# Development

This guide covers development setup, testing, and contribution guidelines for TunaCode.

## Requirements

- Python 3.10+
- Git (for version control)

## Development Installation

### Clone and Setup

```bash
# Clone the repository
git clone https://github.com/larock22/tunacode.git
cd tunacode

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"
```

### Development Dependencies

The `[dev]` extras include:
- `pytest` - Testing framework
- `pytest-asyncio` - Async test support
- `black` - Code formatter
- `isort` - Import sorter
- `flake8` - Linting
- `mypy` - Type checking

## Development Commands

### Using Make

```bash
# Install development environment
make install

# Run linting (black, isort, flake8)
make lint

# Run tests
make test

# Run tests with coverage
make coverage

# Build distribution packages
make build

# Clean build artifacts
make clean
```

### Manual Commands

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_import.py

# Run tests matching pattern
pytest -k "test_name"

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=tunacode tests/
```

## Version Management

When updating versions, modify both:
1. `pyproject.toml`: version field
2. `src/tunacode/constants.py`: VERSION constant

Example:
```python
# pyproject.toml
[project]
version = "0.1.0"

# src/tunacode/constants.py
VERSION = "0.1.0"
```

## Code Style

### Formatting

TunaCode uses:
- **Black** for code formatting
- **isort** for import sorting
- **flake8** for linting

Run formatting:
```bash
black src/ tests/
isort src/ tests/
flake8 src/ tests/
```

### Type Hints

Use type hints throughout the codebase:
```python
def process_file(file_path: str, encoding: str = "utf-8") -> str:
    """Process a file and return its contents."""
    ...
```

## Testing

### Test Structure

```
tests/
├── test_agent_initialization.py
├── test_architect_integration.py
├── test_background_manager.py
├── test_config_setup_async.py
├── test_fast_glob_search.py
├── test_file_reference_expansion.py
├── test_json_tool_parsing.py
├── test_orchestrator_file_references.py
├── test_orchestrator_import.py
├── test_orchestrator_planning_visibility.py
├── test_react_thoughts.py
└── test_update_command.py
```

### Writing Tests

Example test:
```python
import pytest
from tunacode.tools.read_file import ReadFileTool

@pytest.mark.asyncio
async def test_read_file_tool():
    tool = ReadFileTool()
    result = await tool.execute(file_path="/path/to/file.txt")
    assert result.success
    assert "content" in result.data
```

### Running Specific Tests

```bash
# Run tests for a specific module
pytest tests/test_tools.py

# Run with pattern matching
pytest -k "test_read_file"

# Run with markers
pytest -m "slow"
```

## Project Structure

See [ARCHITECTURE.md](./ARCHITECTURE.md) for detailed project structure.

## Contributing

### Development Workflow

1. Create a feature branch
2. Make changes with tests
3. Run linting and tests
4. Submit pull request

### Pull Request Guidelines

- Include tests for new features
- Update documentation as needed
- Follow existing code style
- Add meaningful commit messages

### Debugging

Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Use the debug commands:
- `/dump` - Show message history
- `/thoughts` - Toggle ReAct reasoning display
- `/parsetools` - Debug JSON parsing

## Publishing

### PyPI Release Process

1. Update version in `pyproject.toml` and `constants.py`
2. Run tests: `make test`
3. Build packages: `make build`
4. Upload to PyPI: `make publish`

### Manual Publishing

```bash
# Build distribution
python -m build

# Upload to PyPI
python -m twine upload dist/*
```

## Acknowledgments

TunaCode is a fork of [sidekick-cli](https://github.com/geekforbrains/sidekick-cli). Special thanks to the sidekick-cli team for creating the foundation that made TunaCode possible.

### Key Differences from sidekick-cli

While TunaCode builds on the foundation of sidekick-cli, we've made several architectural changes for our workflow:

- **JSON Tool Parsing Fallback**: Added fallback parsing for when API providers fail with structured tool calling
- **Parallel Search Tools**: New `bash` and `grep` tools with parallel execution for codebase navigation
- **Agent Orchestration**: Advanced orchestrator for complex multi-step tasks with planning transparency
- **Background Processing**: Asynchronous task manager for long-running operations
- **Read-Only Agent**: Safe exploration mode that prevents accidental modifications
- **ReAct Reasoning**: Implemented ReAct (Reasoning + Acting) patterns with configurable iteration limits
- **Dynamic Configuration**: Added `/refresh` command and modified configuration management
- **Safety Changes**: Removed automatic git commits and `/undo` command - requires explicit git usage
- **Error Recovery**: Multiple fallback mechanisms and orphaned tool call recovery
- **Tool System Rewrite**: Complete overhaul of internal tools with atomic operations and different confirmation UIs
- **Debug Commands**: Added `/parsetools`, `/thoughts`, `/iterations` for debugging

## License

MIT License - see [LICENSE](../LICENSE) file for details.
