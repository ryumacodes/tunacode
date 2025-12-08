# Research - Remove Hatch Build System References

**Date:** 2025-12-05
**Owner:** agent
**Phase:** Research

## Goal

Identify ALL hatch-related code, configuration, and documentation in the codebase for removal. The project is migrating from hatch to uv for package management.

## Findings

### Files Requiring Modification

| File | Lines | What to Remove/Change |
|------|-------|----------------------|
| `pyproject.toml` | 1-3 | Build system: `requires = ["hatchling"]`, `build-backend = "hatchling.build"` |
| `pyproject.toml` | 59 | Dev dependency: `"hatch>=1.6.0"` |
| `pyproject.toml` | 159-274 | ALL `[tool.hatch.*]` sections (envs, scripts, build targets) |
| `scripts/setup_dev_env.sh` | 4-5, 12, 74-88, 96, 98, 104-105, 110, 115 | `ensure_hatch()` function, `HATCH_ENV_NAME` var, all hatch commands |
| `.pre-commit-config.yaml` | 46, 62-63, 66-73, 75, 147 | `hatch-lint` hook, hatch-related comments |
| `.github/workflows/publish-release.yml` | 25 | Remove `hatch` from pip install |
| `.github/workflows/publish-release.yml` | 66 | Change `hatch build` to uv-based build |
| `.github/pull_request_template.md` | 16 | Change `hatch run test` to `pytest` or uv equivalent |
| `reports/SMALL_WINS_AUDIT.md` | 98, 180 | Update hatch references in audit report |

### Detailed Breakdown by File

#### 1. `pyproject.toml` (19 references)

**Build System (Lines 1-3):**
```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

**Dev Dependency (Line 59):**
```toml
"hatch>=1.6.0",
```

**Environment Configurations (Lines 159-274):**
- `[tool.hatch.envs.default]` - Lines 159-164
- `[tool.hatch.envs.default.scripts]` - Lines 165-185
- `[tool.hatch.envs.test]` - Lines 236-246
- `[tool.hatch.envs.lint]` - Lines 248-262
- `[tool.hatch.envs.py311]` - Line 264-265
- `[tool.hatch.envs.py312]` - Line 267-268
- `[tool.hatch.envs.py313]` - Line 270-271
- `[tool.hatch.build.targets.wheel]` - Lines 273-274

#### 2. `scripts/setup_dev_env.sh` (16 references)

**Variables:**
- Line 12: `HATCH_ENV_NAME="${HATCH_ENV_NAME:-default}"`

**Comments:**
- Line 4: `# - Creates a Hatch-managed virtual environment rooted at ./.venv`
- Line 5: `# - Installs dev dependencies via Hatch scripts`

**Functions:**
- Lines 74-88: `ensure_hatch()` function

**Commands:**
- Line 96: `ensure_hatch` function call
- Line 105: `hatch -v env create "$HATCH_ENV_NAME"`
- Line 115: `log_info "Or open a Hatch shell: hatch shell"`

#### 3. `.pre-commit-config.yaml` (7 references)

**Hooks:**
- Lines 67-73: `hatch-lint` hook definition
- Line 147: Skip list includes `hatch-lint`

**Comments:**
- Line 46: Reference to hatch-lint handling formatting
- Lines 62-63: Strategy comments about hatch run vs uv run
- Lines 66, 75: Section comments about hatch-managed commands

#### 4. `.github/workflows/publish-release.yml` (2 references)

- Line 25: `pip install hatch twine uv ruff pytest pytest-cov pytest-asyncio`
- Line 66: `run: hatch build`

#### 5. `.github/pull_request_template.md` (1 reference)

- Line 16: `- [ ] All existing tests pass (\`hatch run test\`)`

#### 6. `reports/SMALL_WINS_AUDIT.md` (2 references)

- Line 98: Reference to stale version in hatch scripts
- Line 180: Test command `hatch run test`

### Virtual Environment Binaries

These will be automatically removed when recreating the venv:
- `.venv/bin/hatch`
- `.venv/bin/hatchling`

## Key Patterns / Solutions Found

| Pattern | Replacement |
|---------|-------------|
| `hatch run test` | `pytest` or `uv run pytest` |
| `hatch run lint` | `ruff check .` or `uv run ruff check .` |
| `hatch build` | `uv build` or `python -m build` |
| `hatch publish` | `uv publish` or `twine upload` |
| `hatch env create` | `uv venv && uv pip install -e ".[dev]"` |
| `hatchling` build backend | `setuptools` or keep `hatchling` (it works with uv) |

## Knowledge Gaps

1. **Build backend decision**: Should we switch from `hatchling` to `setuptools`, or keep `hatchling` as build backend? (hatchling works fine with uv, just removes hatch CLI)
2. **Script migration**: Need to define new script runner for pyproject.toml scripts (uv run, or just remove scripts section?)
3. **Pre-commit strategy**: Replace `hatch run lint` with direct `ruff` call or `uv run ruff`?

## Recommended Migration Order

1. Update `pyproject.toml` build system (can keep hatchling or switch to setuptools)
2. Remove `[tool.hatch.*]` sections from `pyproject.toml`
3. Update `scripts/setup_dev_env.sh` to use uv directly
4. Update `.pre-commit-config.yaml` hooks
5. Update `.github/workflows/publish-release.yml`
6. Update documentation files

## References

- `/root/tunacode/pyproject.toml`
- `/root/tunacode/scripts/setup_dev_env.sh`
- `/root/tunacode/.pre-commit-config.yaml`
- `/root/tunacode/.github/workflows/publish-release.yml`
- `/root/tunacode/.github/pull_request_template.md`
- `/root/tunacode/reports/SMALL_WINS_AUDIT.md`
