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

TunaCode uses a comprehensive test suite with multiple categories:

```
tests/
├── characterization/          # Characterization tests capturing existing behavior
│   ├── agent/                # Agent system tests
│   ├── background/           # Background task manager tests
│   ├── code_index/           # Code indexing system tests
│   ├── commands/             # Command system tests
│   ├── repl/                 # REPL interaction tests
│   ├── services/             # MCP and service tests
│   ├── state/                # State management tests
│   ├── ui/                   # User interface tests
│   └── utils/                # Utility function tests
├── integration/              # Integration tests
├── unit/                     # Unit tests
└── utility/                  # Test utilities
```

Key test categories:
- **Characterization Tests**: Capture existing behavior patterns for safety during refactoring
- **Integration Tests**: Test system interactions and workflows
- **Unit Tests**: Test individual components in isolation
- **Async Tests**: Use `@pytest.mark.asyncio` for testing async functionality

### Writing Tests

Example async tool test:
```python
import pytest
from tunacode.tools.read_file import read_file

@pytest.mark.asyncio
async def test_read_file_tool():
    """Test read_file tool functionality."""
    content = await read_file("/path/to/test/file.txt")
    assert content is not None
    assert isinstance(content, str)
```

Example parallel execution test:
```python
import pytest
from tunacode.core.agents.agent_components import execute_tools_parallel

@pytest.mark.asyncio
async def test_parallel_tool_execution():
    """Test parallel execution of read-only tools."""
    async def mock_callback(part, node):
        return f"result-{part}"

    tool_calls = [("tool1", "node1"), ("tool2", "node2")]
    results = await execute_tools_parallel(tool_calls, mock_callback)

    assert len(results) == 2
    assert results[0] == "result-tool1"
    assert results[1] == "result-tool2"
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

## Architecture Components

### Memory Anchors

When adding significant code sections, use memory anchors for LLM optimization:

```python
"""Module for handling background tasks.

CLAUDE_ANCHOR[background-manager]: Async task manager with lifecycle management
"""

class BackgroundTaskManager:
    """CLAUDE_ANCHOR[task-manager-class]: Core background task coordination"""

    def spawn(self, coro, *, name=None):
        """CLAUDE_ANCHOR[task-spawn]: Task creation and tracking entry point"""
        # Implementation here
```

Guidelines for memory anchors:
- Place in docstrings or comments
- Use descriptive, unique keys
- Keep descriptions concise but meaningful
- Update `.claude/anchors.json` when adding new anchors

### Code Indexing System

The code index provides fast file discovery:

```python
from tunacode.core.code_index import CodeIndex

# Create and build index
index = CodeIndex("/path/to/project")
index.build_index()

# Fast file lookups
python_files = index.lookup("*.py", file_type="py")
class_locations = index.lookup("MyClass")
```

Key features:
- Symbol indexing (classes, functions, imports)
- Directory caching for efficient traversal
- Automatic exclusion of build/cache directories
- Incremental refresh capabilities

### Parallel Tool Execution

Read-only tools execute in parallel automatically:

```python
# These tools will execute concurrently:
await read_file("file1.py")
await read_file("file2.py")
await grep("pattern", "src/")
await list_dir("tests/")

# Write tools remain sequential for safety:
await write_file("new.py", content)
await update_file("existing.py", target, patch)
```

Configuration:
- Set `TUNACODE_MAX_PARALLEL` environment variable
- Default: CPU count
- Tools are automatically batched by type

### Background Task Management

For long-running operations:

```python
from tunacode.core.background.manager import BG_MANAGER

# Spawn background task
task_id = BG_MANAGER.spawn(my_async_coroutine())

# Tasks are automatically cleaned up
await BG_MANAGER.shutdown()
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

**Performance & Execution**:
- **Parallel Tool Execution**: Read-only tools execute concurrently for 3x performance improvement
- **Code Indexing System**: Fast in-memory file discovery without timeout-prone grep searches
- **Background Task Management**: Asynchronous task manager for long-running operations
- **3-Second Search Deadline**: Prevents system hangs on overly broad search patterns

**LLM Optimization**:
- **Memory Anchor System**: In-file anchors for persistent code navigation across sessions
- **JSON Tool Parsing Fallback**: Robust fallback when API providers fail with structured tool calling
- **Enhanced Tool Suite**: Added `grep`, `glob`, `list_dir` tools with advanced features

**Architecture & Safety**:
- **MCP Integration**: Model Context Protocol support for external tools
- **Enhanced Error Recovery**: Multiple fallback mechanisms and orphaned tool call recovery
- **Safety Changes**: Removed automatic git commits and `/undo` command - requires explicit git usage
- **Tool System Rewrite**: Complete overhaul with atomic operations and improved confirmation UIs

**Developer Experience**:
- **ReAct Reasoning**: Transparent AI decision-making with configurable iteration limits
- **Debug Commands**: Added `/parsetools`, `/thoughts`, `/iterations` for debugging
- **Dynamic Configuration**: Added `/refresh` command and modified configuration management
- **Comprehensive Testing**: Characterization tests for behavior capture during refactoring

## License

MIT License - see [LICENSE](../LICENSE) file for details.
