# HARNESS.md

## Pre-commits

Source of truth: `.pre-commit-config.yaml`

### Global pre-commit settings
- Python runtime: `python3`
- Global exclude regex:
  - `venv/`, `build/`, `dist/`, `.git/`, `__pycache__/`, `*.egg-info/`
  - `.pytest_cache/`, `.mypy_cache/`, `.ruff_cache/`, `.uv-cache/`, `.uv_cache/`
  - `htmlcov/`, `.coverage`, `reports/`, `llm-agent-tools/`, `.tickets/`, `tinyAgent/`

### Active pre-commit hooks (organized by purpose)

#### File hygiene and repo safety
- `trailing-whitespace` (repo: `pre-commit/pre-commit-hooks`)
- `end-of-file-fixer` (repo: `pre-commit/pre-commit-hooks`, excludes `models_registry.json`)
- `mixed-line-ending` (repo: `pre-commit/pre-commit-hooks`, args: `--fix=lf`)
- `check-added-large-files` (repo: `pre-commit/pre-commit-hooks`, args: `--maxkb=1000`)
- `check-case-conflict` (repo: `pre-commit/pre-commit-hooks`)
- `check-merge-conflict` (repo: `pre-commit/pre-commit-hooks`)
- `check-executables-have-shebangs` (repo: `pre-commit/pre-commit-hooks`)
- `check-shebang-scripts-are-executable` (repo: `pre-commit/pre-commit-hooks`)

#### Config and syntax validity
- `check-yaml` (repo: `pre-commit/pre-commit-hooks`, args: `--allow-multiple-documents`)
- `check-json` (repo: `pre-commit/pre-commit-hooks`)
- `check-toml` (repo: `pre-commit/pre-commit-hooks`)
- `check-ast` (repo: `pre-commit/pre-commit-hooks`)
- `check-docstring-first` (repo: `pre-commit/pre-commit-hooks`)
- `debug-statements` (repo: `pre-commit/pre-commit-hooks`)

#### Python linting, typing, and formatting
- `ruff` (repo: `astral-sh/ruff-pre-commit`, args: `--fix --show-fixes`)
- `ruff-format` (repo: `astral-sh/ruff-pre-commit`, excludes `models_registry.json`)
- `mypy` (repo: `local`, entry: `uv run mypy --ignore-missing-imports --no-strict-optional`, files: `^src/.*\.py$`, exclude: `conftest.py|tests/|scripts/`, also runs at `pre-push`)
- `dead-imports` (repo: `local`, entry: `scripts/run-dead-imports.sh`, files: `\.py$`)
- `vulture-changed` (repo: `local`, entry: `uv run vulture --min-confidence 80 scripts/utils/vulture_whitelist.py`, files: `^src/.*\.py$`, exclude: `tests/|test_`)
- `naming-conventions` (repo: `local`, entry: `uv run python scripts/check-naming-conventions.py`, files: `^src/.*\.py$`, exclude: `tests/|scripts/`)
- `check-file-length` (repo: `local`, entry: `scripts/check-file-length.sh`, files: `\.py$`, exclude: `tests/benchmarks/bench_discover.py`)

#### Security and safeguards
- `bandit` (repo: `PyCQA/bandit`, args: `-c pyproject.toml`, dep: `bandit[toml]`)
- `security-check` (repo: `local`, grep for `PRIVATE|SECRET|PASSWORD|TOKEN` in `src/**/*.py`)
- `no-print-statements` (repo: `local`, grep for `print(` in `src/**/*.py`, ignores `# noqa` and `# pragma`)
- `unused-constants` (repo: `local`, entry: `uv run python scripts/check-unused-constants.py`)

#### Architecture and docs
- `dependency-layers` (repo: `local`, entry: `uv run pytest tests/test_dependency_layers.py -v`)
- `doc8` (repo: `pycqa/doc8`, args: `--max-line-length=120`)

### Currently disabled in config
- `isort` (commented out; replaced by Ruff import sorting)
- `markdownlint` (commented out; noted Node.js v23 compatibility issue)

## Pre-push

## Rules

## CI/CD
