# HARNESS.md

## Pre-commits

Source of truth: `.pre-commit-config.yaml`

### Global pre-commit settings
- Python runtime: `python3`
- Global exclude regex:
  - `venv/`, `build/`, `dist/`, `.git/`, `__pycache__/`, `*.egg-info/`
  - `.pytest_cache/`, `.mypy_cache/`, `.ruff_cache/`, `.uv-cache/`, `.uv_cache/`
  - `htmlcov/`, `.coverage`, `reports/`, `llm-agent-tools/`, `.tickets/`, `tinyAgent/`

### Hooks that run on commit (current)

#### `pre-commit-hooks` (repo: `pre-commit/pre-commit-hooks`)
- `trailing-whitespace`
- `end-of-file-fixer` (excludes `models_registry.json`)
- `check-yaml` (`--allow-multiple-documents`)
- `check-added-large-files` (`--maxkb=1000`)
- `check-case-conflict`
- `check-merge-conflict`
- `check-json`
- `check-toml`
- `check-ast`
- `debug-statements`
- `mixed-line-ending` (`--fix=lf`)
- `check-docstring-first`
- `check-executables-have-shebangs`
- `check-shebang-scripts-are-executable`

#### Security / lint / format repos
- `bandit` (repo: `PyCQA/bandit`, args: `-c pyproject.toml`, dep: `bandit[toml]`)
- `ruff` (repo: `astral-sh/ruff-pre-commit`, args: `--fix --show-fixes`)
- `ruff-format` (repo: `astral-sh/ruff-pre-commit`, excludes `models_registry.json`)
- `doc8` (repo: `pycqa/doc8`, args: `--max-line-length=120`)

#### Local project hooks (repo: `local`)
- `mypy` (`uv run mypy --ignore-missing-imports --no-strict-optional`)
  - files: `^src/.*\.py$`
  - exclude: `conftest.py`, `tests/`, `scripts/`
  - stages: `pre-commit`, `pre-push`
- `dead-imports` (`scripts/run-dead-imports.sh`)
  - files: `\.py$`
  - stage: `pre-commit`
- `vulture-changed` (`uv run vulture --min-confidence 80 scripts/utils/vulture_whitelist.py`)
  - files: `^src/.*\.py$`
  - exclude: `tests/`, `test_`
  - stage: `pre-commit`
- `unused-constants` (`uv run python scripts/check-unused-constants.py`)
  - stage: `pre-commit`
- `security-check` (grep for `PRIVATE|SECRET|PASSWORD|TOKEN` in `src/**/*.py`)
- `no-print-statements` (grep for `print(` in `src/**/*.py`, ignores `# noqa` / `# pragma`)
- `check-file-length` (`scripts/check-file-length.sh`)
  - files: `\.py$`
  - exclude: `tests/benchmarks/bench_discover.py`
- `naming-conventions` (`uv run python scripts/check-naming-conventions.py`)
  - files: `^src/.*\.py$`
  - exclude: `tests/`, `scripts/`
- `dependency-layers` (`uv run pytest tests/test_dependency_layers.py -v`)
  - stage: `pre-commit`

### Currently disabled in config
- `isort` (commented out; replaced by Ruff import sorting)
- `markdownlint` (commented out; noted Node.js v23 compatibility issue)

## Pre-push

## Rules

## CI/CD
