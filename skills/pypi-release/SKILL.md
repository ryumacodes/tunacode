---
name: pypi-release
description: This skill should be used when releasing tunacode-cli to PyPI. It keeps the existing local release checks, then hands the actual PyPI upload to a GitHub Actions workflow that uses the repository's PYPI_API_TOKEN secret.
---

# PyPI Release Automation

## Overview

Keep the existing local release gates for tunacode-cli, then hand the actual PyPI upload to GitHub Actions. This keeps the release checks local while moving the credentialed publish step into the repository workflow.

## When to Use This Skill

Trigger this skill when the user requests:
- "Release to PyPI"
- "Publish a new version"
- "Create a release"
- "Bump version and release"
- "Push a new version to PyPI"

## Core Release Workflow

The skill provides two approaches: **Manual** (REQUIRED) and **Automated** (deprecated - skips critical test step).

### Automated Release (NOT RECOMMENDED - Use Manual)

**WARNING: The automated script is currently discouraged because it skips the mandatory manual test step.**

Use the Manual Release workflow below instead to ensure proper testing before release.

~~Execute the full release workflow with a single script:~~

~~```bash
uv run python skills/pypi-release/scripts/release.py
```~~

~~The script performs these steps automatically:~~
1. ~~Pre-flight checks (git status, branch check, linting, tests)~~
2. ~~Version bump~~
3. ~~Git operations (commit, tag, push)~~
4. ~~GitHub release~~
5. ~~Workflow monitoring~~

**Issue:** The automated script does not include the mandatory manual import test (Step 3) which has caused multiple broken releases. Always use the manual workflow.

### Manual Release (REQUIRED - Step-by-Step)

**This is the ONLY recommended workflow. Follow these steps in order:**

#### Step 1: Pre-flight Checks

Verify the repository is ready for release:

```bash
# Check git status (must be clean)
git status

# Verify on master branch
git branch --show-current

# Run linting
ruff check .

# Run tests
source .venv/bin/activate && pytest tests/ -q

# MANDATORY: Run tmux E2E tool tests (all 6 must pass)
uv run pytest tests/system/cli/test_tmux_tools.py -v -m tmux
```

**HARD GATE: If the tmux tool tests fail, DO NOT proceed with the release.** These tests verify all 6 tools (bash, read_file, write_file, update_file, discover, web_fetch) work end-to-end in the real TUI. No exceptions.

#### Step 2: Bump Version

Use the version bumping script:

```bash
uv run python skills/pypi-release/scripts/bump_version.py
```

The script:
- Reads current version from `pyproject.toml`
- Increments the patch number (rightmost digit)
- Updates four files:
  - `pyproject.toml:8` (project version)
  - `pyproject.toml:175` (hatch script version)
  - `src/tunacode/constants.py:12` (APP_VERSION constant)
  - `README.md` (version header)

#### Step 2.5: Update CHANGELOG

**REQUIRED:** Manually update `CHANGELOG.md` with the new version entry.

1. Check commits since last release:
   ```bash
   git log --oneline $(git describe --tags --abbrev=0)..HEAD --no-merges
   ```

2. Add entry under `## [Unreleased]`:
   ```markdown
   ## [X.Y.Z.W] - YYYY-MM-DD

   ### Added
   - New features

   ### Changed
   - Changes to existing functionality

   ### Fixed
   - Bug fixes
   ```

3. Stage the file:
   ```bash
   git add CHANGELOG.md
   ```

#### Step 3: **MANDATORY** - Test the Build Locally

**CRITICAL: You MUST test that tunacode actually works before releasing!**

Test the import and basic functionality:

```bash
# Activate venv and test import
source .venv/bin/activate && python -c "from tunacode.ui.main import app; print('✓ Import successful')"

# Optionally test the CLI starts without errors
python -m tunacode.ui.main --help
```

**If the import fails, DO NOT PROCEED with the release!** Fix the issue first, then re-test.

This step prevents releasing broken packages to PyPI (which cannot be undone).

#### Step 4: Commit and Push the Release Commit

Commit the version changes and push them to `master`:

```bash
# Stage version files (CHANGELOG.md should already be staged from Step 2.5)
git add pyproject.toml src/tunacode/constants.py README.md CHANGELOG.md

# Commit with conventional commit message
git commit -m "chore: bump version to X.Y.Z.W"

# Push to remote
git push origin master
```

#### Step 5: Trigger the GitHub Actions Publish Workflow

Run the manual publish workflow after the local checks and release commit have passed:

```bash
gh workflow run publish-release.yml --ref master -f version=X.Y.Z.W
```

This workflow:
- Checks that `pyproject.toml` and `src/tunacode/constants.py` match the requested version
- Builds the distribution artifacts
- Runs `twine check` on the built artifacts
- Publishes to PyPI using the repository `PYPI_API_TOKEN` secret

#### Step 6: Monitor Workflow

Check the status of the GitHub Actions workflow:

```bash
# List recent workflow runs
gh run list --workflow=publish-release.yml --limit 1

# Watch workflow in real-time
gh run watch

# View logs if failed
gh run view <run-id> --log-failed
```

## Troubleshooting

### Workflow Failures

If the GitHub Actions workflow fails:

1. **Check workflow status:**
   ```bash
   gh run list --workflow=publish-release.yml --limit 1
   ```

2. **View failure logs:**
   ```bash
   gh run view <run-id> --log-failed
   ```

3. **Common issues:** See `references/common-issues.md` for detailed troubleshooting

### Version Consistency Errors

If the workflow reports version mismatch between the requested version and the code:

1. Verify all four version locations match:
   ```bash
   grep 'version = ' pyproject.toml
   grep 'APP_VERSION' src/tunacode/constants.py
   grep '^## v' README.md | head -1
   ```

2. Re-run `bump_version.py` script to sync versions

3. Push the corrected commit and re-run:
   ```bash
   git push origin master
   gh workflow run publish-release.yml --ref master -f version=X.Y.Z.W
   ```

### Python Version Mismatch

If the workflow fails with Python version errors:

1. Check `.github/workflows/publish-release.yml` line 20
2. Ensure `python-version: '3.12'` (not `'3.x'`)
3. Commit the fix and update the tag to include it

**Common error message:**
```
ERROR: Package 'tunacode-cli' requires a different Python: 3.14.0 not in '<3.14,>=3.10'
```

**Fix:** Pin Python version in workflow to `3.12`

## Key Files and Locations

### Version Files (Must Stay Synchronized)

1. **`pyproject.toml:8`** - Project version in [project] section
2. **`pyproject.toml:175`** - Hatch script version
3. **`src/tunacode/constants.py:12`** - APP_VERSION constant
4. **`README.md`** - Version header (line 40)
5. **`CHANGELOG.md`** - Version history (manual update required)

### Workflow Configuration

- **`.github/workflows/publish-release.yml`** - Manual GitHub Actions workflow
  - Triggers with `workflow_dispatch`
  - Validates the requested version against the checked-out code
  - Builds the distribution and runs `twine check`
  - Publishes to PyPI using `PYPI_API_TOKEN`

### Scripts

- **`scripts/bump_version.py`** - Atomic version bumping across all files
- **`scripts/release.py`** - Full automated release workflow

### References

- **`references/common-issues.md`** - Detailed troubleshooting guide for common problems
- **`references/workflow-structure.md`** - Complete GitHub Actions workflow documentation

## Prerequisites

Ensure these are configured before releasing:

1. **GitHub CLI authenticated:**
   ```bash
   gh auth status
   ```

2. **PyPI API token** configured as `PYPI_API_TOKEN` in repository secrets

3. **Clean git state** - all changes committed

4. **On master branch**

5. **Tests passing** - `pytest tests/`

6. **Linting passing** - `ruff check .`

## Post-Release Verification

After a successful release:

1. **Verify on PyPI:**
   - Visit https://pypi.org/project/tunacode-cli/
   - Confirm new version appears

2. **Test installation:**
   ```bash
   pip install --upgrade tunacode-cli
   tunacode --version
   ```

## Debugging Workflow Issues

When the workflow fails, follow this debug process:

1. **Identify the failure point** from workflow logs
2. **Consult `references/common-issues.md`** for known problems
3. **Fix the issue** (workflow config, version files, etc.)
4. **Push the fix** to `master`:
   ```bash
   git push origin master
   ```
5. **Re-trigger the workflow:**
   ```bash
   gh workflow run publish-release.yml --ref master -f version=X.Y.Z.W
   ```
6. **Monitor until success**

## No Rollback Policy

This skill does not implement automatic rollback. If a release fails:

1. Diagnose the issue using logs and references
2. Fix the underlying problem
3. Push the corrected release commit
4. Re-run the workflow

Rationale: PyPI releases are immutable once published. The version number cannot be reused. Focus on fixing forward rather than rolling back.
