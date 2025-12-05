# Research - Hatch to UV Migration

**Date:** 2025-12-05
**Owner:** claude-agent
**Phase:** Research
**Git Commit:** a16f103a3a9068083ff00b735bfc2b8f974d676d

## Goal

Map all hatch references in the codebase and document what needs to change to complete migration from hatch to uv/pip as the primary development tooling.

## Findings

### Critical Files Requiring Changes

| File | Lines | Change Required |
|------|-------|-----------------|
| `pyproject.toml` | 1-3, 59, 159-275 | Remove hatch envs, keep hatchling build backend |
| `.github/workflows/publish-release.yml` | 25, 66 | Remove hatch install, replace `hatch build` |
| `.pre-commit-config.yaml` | 67-73 | Replace `hatch run lint` with direct ruff |
| `scripts/setup_dev_env.sh` | 74-115 | Remove hatch dependency, use uv venv |

### pyproject.toml Changes Required

**Build System (KEEP):**
```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```
- `hatchling` is a lightweight build backend - does NOT require hatch installed
- This is the correct modern approach for PEP 517/518 compliance

**Dev Dependencies (REMOVE line 59):**
```toml
"hatch>=1.6.0",  # REMOVE THIS
```

**Environment Configs (REMOVE lines 159-270):**
```toml
[tool.hatch.envs.default]          # DELETE
[tool.hatch.envs.default.scripts]  # DELETE
[tool.hatch.envs.test]             # DELETE
[tool.hatch.envs.test.scripts]     # DELETE
[tool.hatch.envs.lint]             # DELETE
[tool.hatch.envs.lint.scripts]     # DELETE
[tool.hatch.envs.py311]            # DELETE
[tool.hatch.envs.py312]            # DELETE
[tool.hatch.envs.py313]            # DELETE
```

**Build Target (KEEP line 273-274):**
```toml
[tool.hatch.build.targets.wheel]
packages = ["src/tunacode"]
```
- Required by hatchling to find the source package

### GitHub Actions Changes

**File:** `.github/workflows/publish-release.yml`

**Line 25 - Remove hatch from install:**
```yaml
# Before:
pip install hatch twine uv ruff pytest pytest-cov pytest-asyncio
# After:
pip install build twine uv ruff pytest pytest-cov pytest-asyncio
```

**Line 66 - Replace hatch build:**
```yaml
# Before:
run: hatch build
# After:
run: python -m build
```

### Pre-commit Hook Changes

**File:** `.pre-commit-config.yaml` lines 66-73

```yaml
# Before:
- id: hatch-lint
  name: Run hatch lint check
  entry: hatch run lint
  language: system
  pass_filenames: false
  always_run: true
  stages: [pre-commit]

# After:
- id: ruff-lint
  name: Run ruff lint check
  entry: bash -c "ruff check . && ruff format --check ."
  language: system
  pass_filenames: false
  always_run: true
  stages: [pre-commit]
```

### Development Script Changes

**File:** `scripts/setup_dev_env.sh`

**Remove ensure_hatch() function (lines 74-89)**
**Remove ensure_hatch call (line 96)**
**Replace hatch env create (line 105):**
```bash
# Before:
hatch -v env create "$HATCH_ENV_NAME"
# After:
if [ ! -d "$VENV_DIR" ]; then
    uv venv "$VENV_DIR"
fi
```

**Remove hatch shell reference (line 115)**

### Documentation Files to Update/Remove

| File | Action |
|------|--------|
| `.claude/development/hatch-commands.md` | DELETE - no longer relevant |
| `.claude/development/uv-hatch-setup.md` | UPDATE - reflect pure uv approach |
| `README.md` line 84 | REMOVE hatch build guide reference |
| `.github/pull_request_template.md` line 16 | UPDATE `hatch run test` to `pytest` |

### Memory Bank Files (Historical Reference Only)

These files contain hatch references but are execution logs - no changes needed:
- `memory-bank/execute/2025-11-19_error_handling_hardening.md`
- `memory-bank/execute/2025-10-02_14-45-00_release_process_automation.md`
- `memory-bank/execute/2025-11-29_17-55-00_textual-tui-architecture-refactor.md`
- Multiple other execution/research logs

## Key Patterns / Solutions Found

**Pattern: hatchling vs hatch distinction**
- `hatchling` = build backend (lightweight, no CLI needed)
- `hatch` = full project manager (CLI tool, environments)
- Keep hatchling, remove hatch dependency

**Pattern: Script command equivalents**
| Hatch Command | UV/Direct Equivalent |
|---------------|---------------------|
| `hatch run test` | `pytest` |
| `hatch run lint` | `ruff check . && ruff format .` |
| `hatch build` | `python -m build` |
| `hatch env create` | `uv venv .venv` |
| `hatch shell` | `source .venv/bin/activate` |

## Knowledge Gaps

1. The `[tool.hatch.envs.default.scripts]` section has useful script aliases - consider creating a `Makefile` or `justfile` to preserve these conveniences
2. Multi-Python version testing (`py311`, `py312`, `py313` envs) - need alternative approach if this feature is used

## Migration Order (Recommended)

1. **GitHub Actions first** - easiest to test, highest impact
2. **Pre-commit hooks** - ensures local dev works
3. **Development setup script** - onboarding flow
4. **pyproject.toml cleanup** - final configuration
5. **Documentation cleanup** - last step

## References

- [pyproject.toml](https://github.com/alchemiststudiosDOTai/tunacode/blob/a16f103a3a9068083ff00b735bfc2b8f974d676d/pyproject.toml)
- [publish-release.yml](https://github.com/alchemiststudiosDOTai/tunacode/blob/a16f103a3a9068083ff00b735bfc2b8f974d676d/.github/workflows/publish-release.yml)
- [pre-commit-config.yaml](https://github.com/alchemiststudiosDOTai/tunacode/blob/a16f103a3a9068083ff00b735bfc2b8f974d676d/.pre-commit-config.yaml)
- [setup_dev_env.sh](https://github.com/alchemiststudiosDOTai/tunacode/blob/a16f103a3a9068083ff00b735bfc2b8f974d676d/scripts/setup_dev_env.sh)
- [.claude/development/hatch-commands.md](https://github.com/alchemiststudiosDOTai/tunacode/blob/a16f103a3a9068083ff00b735bfc2b8f974d676d/.claude/development/hatch-commands.md)
