# Hatch Commands Quick Reference

## Essential Commands

```bash
# Development
hatch run install     # Install dev dependencies
hatch run run        # Run tunacode
hatch run dev        # Development mode

# Testing
hatch run test       # Run tests
hatch run coverage   # Test coverage

# Code Quality
hatch run lint       # Lint & format
hatch run typecheck  # Type checking
hatch run security   # Security scan

# Building
hatch build          # Build package
hatch run clean      # Clean artifacts
```

## Development Workflow

1. **Setup Environment**
   ```bash
   hatch run install
   ```

2. **Make Changes**
   ```bash
   hatch run dev  # Run with hot reload
   ```

3. **Test Changes**
   ```bash
   hatch run test
   hatch run lint
   ```

4. **Build & Release**
   ```bash
   hatch build
   hatch publish
   ```

## Environment Commands

```bash
# List environments
hatch env show

# Enter environment shell
hatch shell

# Remove all environments
hatch env prune

# Run in specific environment
hatch run test:pytest
hatch run py311:test
```

## Script Definitions

All scripts defined in `pyproject.toml` under:
```toml
[tool.hatch.envs.default.scripts]
```

## Common Tasks

### Run Tests on Multiple Python Versions
```bash
hatch run py310:test
hatch run py311:test
hatch run py312:test
```

### Dead Code Analysis
```bash
hatch run dead-code-check   # Check for dead code
hatch run dead-code-clean   # Remove dead code
hatch run dead-code-report  # Generate reports
```

### Playwright Cache Management
```bash
hatch run remove-playwright
hatch run restore-playwright
```

## CI/CD Integration

```yaml
# GitHub Actions example
- name: Install Hatch
  run: pip install hatch

- name: Run tests
  run: hatch run test

- name: Run linting
  run: hatch run lint-check
```

## Troubleshooting

```bash
# Reset environments
hatch env prune

# Show environment info
hatch env show

# Update hatch
pip install --upgrade hatch
```
