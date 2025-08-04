<!-- This guide covers initial setup, development environment, project structure, and running TunaCode for the first time -->

# Getting Started with TunaCode Development

## Prerequisites

- Python 3.10 or higher
- Git
- Basic understanding of async Python
- Familiarity with CLI applications

## Development Setup

### 1. Clone the Repository

```bash
git clone https://github.com/RR-LN/tunacode.git
cd tunacode
```

### 2. Set Up Development Environment

The recommended approach is to use the provided setup script:

```bash
./scripts/setup_dev_env.sh
```

This script will:
- Create a fresh virtual environment
- Install all dependencies including dev tools
- Verify the setup

### Manual Setup (Alternative)

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in editable mode with dev dependencies
pip install -e ".[dev]"
pip install pytest-asyncio

# Install pre-commit hooks
pre-commit install
```

### 3. Configure API Keys

Create a `.env` file in the project root:

```bash
ANTHROPIC_API_KEY=sk-...
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=...
# Add other API keys as needed
```

### 4. Run Tests

Verify your setup by running tests:

```bash
# Run all tests
make test

# Run specific test file
pytest tests/test_import.py

# Run with coverage
make coverage

# Skip slow tests during development
pytest -m "not slow"
```

### 5. Code Quality Checks

```bash
# Run linting (black, isort, flake8)
make lint

# Run type checking (if configured)
mypy src/tunacode

# Check for dead code
vulture src/tunacode
```

## Project Structure

```
tunacode/
├── src/tunacode/          # Main source code
│   ├── cli/               # CLI interface and commands
│   ├── core/              # Core business logic
│   ├── tools/             # Tool implementations
│   ├── ui/                # User interface components
│   ├── utils/             # Utility functions
│   ├── configuration/     # Config management
│   ├── services/          # External services (MCP)
│   └── templates/         # Template system
├── tests/                 # Test suite
├── docs/                  # Documentation
├── scripts/               # Development scripts
└── llm-agent-tools/       # Agent tooling (if present)
```

## Development Workflow

### 1. Agent Tooling Workflow

If the `llm-agent-tools` directory exists, follow this workflow:

```bash
# Track tasks with multi-agent support
./llm-agent-tools/scratchpad-multi.sh --agent main

# Use knowledge base
./llm-agent-tools/knowledge.sh --agent main

# Generate code roadmaps
./llm-agent-tools/codemap.sh

# Research online
./llm-agent-tools/researcher.sh
```

### 2. Test-Driven Development

Follow the TDD approach outlined in CLAUDE.md:

1. **Start outside-in**: Write failing acceptance test
2. **Go green fast**: Minimal code to pass
3. **Drive design with micro tests**: Unit test each behavior
4. **Refactor on green**: Clean up while tests pass
5. **Edge-case first**: Test edge cases before implementation

Example:

```python
# 1. Write failing test
async def test_new_feature():
    result = await new_feature("input")
    assert result == "expected"

# 2. Implement minimal code
async def new_feature(input: str) -> str:
    return "expected"  # Just make it pass

# 3. Add more specific tests
async def test_new_feature_edge_case():
    result = await new_feature("")
    assert result == "empty input"

# 4. Refactor implementation
async def new_feature(input: str) -> str:
    if not input:
        return "empty input"
    return "expected"
```

### 3. Making Changes

1. Create a feature branch:
   ```bash
   git checkout -b feature/my-new-feature
   ```

2. Make changes following code style
3. Run tests and linting
4. Commit with descriptive messages:
   ```bash
   git add .
   git commit -m "feat: add new feature X

   - Implemented Y functionality
   - Added tests for Z

   Closes #123"
   ```

## Code Style Guidelines

### 1. Follow the 10 Rules

1. **Guard Clause**: Return early for cleaner code
2. **Delete Dead Code**: Remove unused code
3. **Normalize Symmetries**: Make similar things look similar
4. **New Interface, Old Implementation**: Design ideal interfaces
5. **Reading Order**: Order code for readability
6. **Cohesion Order**: Group related code
7. **Move Declaration & Initialization Together**: Keep variable birth and value adjacent
8. **Explaining Variable**: Extract complex expressions
9. **Explaining Constant**: Replace magic values
10. **Explicit Parameters**: Make all inputs visible

### 2. Python Style

- Use Black for formatting
- Use isort for imports
- Follow PEP 8
- Maximum line length: 120
- Use type hints where beneficial

### 3. Async Best Practices

```python
# Good: Async all the way
async def process_files(paths: List[Path]) -> List[str]:
    tasks = [read_file_async(path) for path in paths]
    return await asyncio.gather(*tasks)

# Bad: Mixing sync and async
def process_files(paths: List[Path]) -> List[str]:
    return asyncio.run(read_all_async(paths))  # Avoid this pattern
```

## Running TunaCode Locally

### Development Mode

```bash
# Run from source
python -m tunacode

# With debug logging
LOG_LEVEL=DEBUG python -m tunacode

# With specific model
python -m tunacode --model openai:gpt-4o
```

### Testing Changes

1. **Unit Test**: Test individual components
2. **Integration Test**: Test component interactions
3. **Manual Test**: Run the application and test interactively
4. **Characterization Test**: Capture existing behavior

Example manual test session:

```bash
# Start TunaCode
python -m tunacode

# Test your feature
/help
/your-new-command
Write a test file
/exit
```

## Debugging

### 1. Enable Debug Logging

```python
# In your code
import logging
logger = logging.getLogger(__name__)
logger.debug("Debug information")

# Set environment variable
export LOG_LEVEL=DEBUG
```

### 2. Use the Debug Commands

```bash
# In TunaCode REPL
/dump              # Show message history
/thoughts on       # Show agent reasoning
/iterations 30     # Increase iteration limit
```

### 3. Python Debugger

```python
# Add breakpoint
import pdb; pdb.set_trace()

# Or use IDE debugger with launch.json
```

### 4. Async Debugging

```python
# Debug async code
import asyncio

async def debug_async():
    # Set breakpoint here
    await some_async_function()

# Run with debugger
asyncio.run(debug_async())
```

## Common Development Tasks

### Adding a New Tool

See [Adding Tools Guide](adding-tools.md)

### Adding a New Command

See [Adding Commands Guide](adding-commands.md)

### Updating Model Registry

Edit `src/tunacode/configuration/models.py`:

```python
MODEL_REGISTRY["provider:new-model"] = ModelInfo(
    provider="provider",
    name="new-model",
    display_name="New Model",
    context_window=100000,
    max_output_tokens=4096,
    supports_tools=True,
    supports_vision=False,
    input_price_per_million=1.00,
    output_price_per_million=2.00
)
```

### Running Benchmarks

```bash
# Performance benchmarks
pytest tests/benchmarks/ -v

# Memory profiling
python -m memory_profiler src/tunacode/cli/main.py
```

## Troubleshooting

### Import Errors

```bash
# Ensure you're in the virtual environment
which python  # Should show venv path

# Reinstall in editable mode
pip install -e ".[dev]"
```

### API Key Issues

```bash
# Check environment variables
echo $ANTHROPIC_API_KEY

# Verify in Python
python -c "import os; print(os.environ.get('ANTHROPIC_API_KEY', 'Not set'))"
```

### Test Failures

```bash
# Run single test with verbose output
pytest tests/test_failing.py::test_specific -vvs

# Check for test pollution
pytest tests/test_failing.py --forked
```

## Next Steps

1. Read the [Architecture Documentation](../modules/core-architecture.md)
2. Explore the [Tools System](../modules/tools-system.md)
3. Learn about [Adding Tools](adding-tools.md)
4. Understand [Command Development](adding-commands.md)
5. Review [Testing Guidelines](testing-guide.md)

## Getting Help

- Check existing issues on GitHub
- Read the codebase documentation
- Ask in discussions
- Review test files for examples

## Contributing

1. Fork the repository
2. Create your feature branch
3. Make changes with tests
4. Ensure all tests pass
5. Submit a pull request

See [CONTRIBUTING.md](../../CONTRIBUTING.md) for detailed guidelines.
