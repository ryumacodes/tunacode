# Technical Context

## Technologies Used

### Core Technologies
- **Python 3.10+**: Primary programming language
- **Setuptools**: Package management and distribution
- **Pytest**: Testing framework
- **Pytest-cov**: Test coverage reporting
- **Pre-commit**: Git pre-commit hooks for code quality
- **Make**: Build automation

### Development Tools
- **Ruff**: Code formatting and Linting
- **Mypy**: Static type checking
- **Isort**: Import sorting
- **Vulture**: Dead code detection
- **Pip-tools**: Dependency management

### Testing Technologies
- **Pytest**: Core testing framework
- **Pytest-mock**: Mocking library for tests
- **Coverage.py**: Code coverage measurement

### Documentation
- @documentation
- documentation/README.md

## Development Setup

### Environment Requirements
- Python 3.10 or higher
- Virtual environment (ALWAYS)
- Git for version control



### Development Workflow
1. Create feature branch from main
2. Implement changes in small, focused commits
3. Run tests locally: `pytest tests/`
4. Ensure linting passes: `make lint`
5. Update documentation as needed
6. Create pull request for review

### Testing Process
1. Run all tests: `pytest tests/`
2. Run specific test file: `pytest tests/path/to/test_file.py`
3. Run with coverage: `pytest --cov=tunacode tests/`
4. Generate coverage report: `pytest --cov=tunacode --cov-report=html tests/`

## Technical Constraints

### Python Version
- Must maintain compatibility with supported Python versions

### File Size Limits
- All Python files should be under 500 lines
- Exceptionally large files require refactoring

### Code Quality Requirements
- All code must pass linting checks
- Type hints required for all public interfaces
- Test coverage must not decrease

### Dependency Management
- Dependencies must be pinned in requirements files
- No direct installation of packages outside of requirements
- Security scanning for dependencies

## Dependencies

### Runtime Dependencies
- Standard Python library (no external dependencies in core)

### Development Dependencies
- ruff
- isort==5.10.1
- mypy==0.931
- pre-commit==2.17.0
- pytest==6.2.5
- pytest-cov==3.0.0
- pytest-mock==3.6.1
- vulture==2.3

### Tool Dependencies
- make (for running make commands)
- git (for version control)
- bash or compatible shell (for scripts)

## Important Technical Notes

### Pydantic-AI Agent Usage (Critical)
**Updated: After recent refactoring issues**

When using pydantic-ai Agent objects, be aware of these critical API differences:

1. **Use `agent.iter()` not `agent.run()` for async context managers**:
   ```python
   # CORRECT - returns async context manager
   async with agent.iter(message) as agent_run:
       async for node in agent_run:
           # process nodes

   # INCORRECT - agent.run() returns a coroutine, not a context manager
   async with agent.run(message) as agent_run:  # This will fail!
   ```

2. **AgentRun is directly iterable - no .stream attribute**:
   ```python
   # CORRECT - iterate directly over agent_run
   async for node in agent_run:
       # process nodes

   # INCORRECT - AgentRun has no .stream attribute
   for node in agent_run.stream:  # This will fail!
   ```

3. **Always use async iteration**:
   ```python
   # CORRECT
   async for node in agent_run:
       # process nodes

   # INCORRECT - must use async for
   for node in agent_run:  # This will fail!
   ```

4. **Function parameter order in process_request**:
   After refactoring, the parameter order changed from `(model, message, ...)` to `(message, model, ...)`. Always check the function signature when calling `process_request`.

These issues were discovered and fixed during the refactoring of main.py. Future agents should be aware of these API requirements to avoid similar errors.

## Tool Usage Patterns

### Code Formatting
- Run `make format` to format all code with Ruff and isort
- Configure IDE to format on save with Ruff

### Linting
- Run `make lint` to check code with flake8 and mypy
- Configure IDE to show linting errors in real-time

### Testing
- Run `make test` to run all tests
- Run `make test-cov` to run tests with coverage
- Run individual tests with `pytest path/to/test.py`

### Pre-commit Hooks
- Automatically run on commit
- Include formatting, linting, and import sorting
- Can be run manually with `pre-commit run --all-files`

### Refactoring Tools
- Use vulture to identify dead code
- Use characterization tests to ensure behavior preservation
- Use incremental approach with small commits

### Documentation Updates
- Update README.md for user-facing changes
- Update docstrings for API changes
- Update comments for implementation changes

## Development Environment
- Virtual environment recommended
- IDE with Python support (VS Code, PyCharm, etc.)
- Terminal access for running commands
- Git for version control
