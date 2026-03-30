# GitHub Actions Workflow Structure

This document describes the structure and requirements for the PyPI publishing workflow used by tunacode-cli.

## Workflow File Location

`.github/workflows/publish-release.yml`

## Trigger Configuration

The workflow is manual and runs only when explicitly dispatched:

```yaml
on:
  workflow_dispatch:
    inputs:
      version:
        description: Version to publish, for example 0.0.78.0
        required: true
        type: string
```

## Workflow Steps

### 1. Checkout Code
```yaml
- uses: actions/checkout@v4
```
Checks out the repository at the release tag.

### 2. Setup Python
```yaml
- name: Set up Python
  uses: actions/setup-python@v5
  with:
    python-version: '3.12'  # IMPORTANT: Pin to 3.12, not '3.x'
```

**Critical:** Must pin to Python 3.12 because:
- Project requires `python >=3.10,<3.14`
- Using `'3.x'` selects the latest Python (3.14+) which breaks the build
- Python 3.13 breaks Hatch's filter parsing

### 3. Install Build Tooling
```yaml
- name: Install build tooling
  run: |
    python -m pip install --upgrade pip
    pip install hatch twine uv ruff pytest pytest-cov pytest-asyncio
```

Installs all required build dependencies.

### 4. Determine Version from Code
```yaml
- name: Determine version from code
  id: ver
  shell: bash
  run: |
    PYPROJ=$(awk '
      /^\[project\]/ { in_proj=1; next }
      /^\[/ { if (in_proj) exit }
      in_proj && /^version =/ { match($0, /"([^"]+)"/, m); print m[1]; exit }
    ' pyproject.toml)
    CONST=$(awk -F '"' '/^APP_VERSION =/ { print $2; exit }' src/tunacode/constants.py)
    echo "pyproject=$PYPROJ" >> "$GITHUB_OUTPUT"
    echo "constants=$CONST" >> "$GITHUB_OUTPUT"
```

Extracts the release version from the checked-out code.

### 5. Check Version Consistency
```yaml
- name: Check version consistency
  shell: bash
  run: |
    EXPECTED="${{ inputs.version }}"
    PYPROJ="${{ steps.ver.outputs.pyproject }}"
    CONST="${{ steps.ver.outputs.constants }}"
    [[ "$EXPECTED" == "$PYPROJ" ]] || { echo 'pyproject.toml version mismatch'; exit 1; }
    [[ "$EXPECTED" == "$CONST" ]] || { echo 'constants.py APP_VERSION mismatch'; exit 1; }
```

Validates that the requested workflow input matches the checked-out code:
- Workflow input version
- `pyproject.toml` [project] version
- `src/tunacode/constants.py` APP_VERSION

### 6. Build Package
```yaml
- name: Build
  run: python -m build
```

Creates distribution packages (`dist/` directory).

### 7. Check Distribution Metadata
```yaml
- name: Check distribution metadata
  run: python -m twine check dist/*
```

Validates the built artifacts before upload.

### 8. Publish to PyPI
```yaml
- name: Publish to PyPI (API token)
  env:
    TWINE_USERNAME: __token__
    TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
  run: python -m twine upload dist/*
```

Uploads the built package to PyPI using the API token authentication method.

## Required Secrets

### PYPI_API_TOKEN

Must be configured in GitHub repository secrets:
1. Go to repository Settings → Secrets and variables → Actions
2. Add `PYPI_API_TOKEN` with value from PyPI

To generate a PyPI token:
1. Visit https://pypi.org/manage/account/token/
2. Create token with scope limited to `tunacode-cli` project
3. Copy token immediately (shown only once)

## Version File Locations

The workflow validates consistency across these files:

1. **`pyproject.toml:8`** - Project version in `[project]` section
   ```toml
   [project]
   name = "tunacode-cli"
   version = "0.0.78.0"
   ```

2. **`pyproject.toml:175`** - Hatch script version
   ```toml
   [tool.hatch.envs.default.scripts]
   version = "0.0.78.0"
   ```

3. **`src/tunacode/constants.py:12`** - Application constant
   ```python
   APP_VERSION = "0.0.78.0"
   ```

## Monitoring and Debugging

### Check Workflow Status
```bash
# List recent workflows
gh run list --workflow=publish-release.yml --limit 5

# Watch a running workflow
gh run watch

# View specific run details
gh run view <run-id>
```

### View Logs
```bash
# View all logs for a run
gh run view <run-id> --log

# View only failed job logs
gh run view <run-id> --log-failed
```

### Manual Trigger
```bash
# Trigger workflow from the release commit on master
gh workflow run publish-release.yml --ref master -f version=0.0.78.0

# Check if workflow started
gh run list --workflow=publish-release.yml --limit 1
```

## Common Modifications

### Update Python Version
If project requirements change:
1. Update `requires-python` in `pyproject.toml`
2. Update `python-version` in workflow (ensure it's within range)
3. Test locally before releasing

### Release From a Different Ref
To publish from a release branch instead of `master`, keep the `version` input the same and change the workflow ref:
```bash
gh workflow run publish-release.yml --ref release/my-branch -f version=0.0.78.0
```

### Change PyPI Upload Target
To publish to TestPyPI first:
```yaml
- name: Publish to TestPyPI
  env:
    TWINE_USERNAME: __token__
    TWINE_PASSWORD: ${{ secrets.TEST_PYPI_API_TOKEN }}
  run: python -m twine upload --repository testpypi dist/*
```
