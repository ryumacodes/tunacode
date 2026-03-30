# Common PyPI Release Issues

This document catalogs common problems encountered during PyPI releases and their solutions.

## Python Version Mismatch

**Symptom:**
```
ERROR: Package 'tunacode-cli' requires a different Python: 3.14.0 not in '<3.14,>=3.10'
```

**Cause:** GitHub Actions workflow using `python-version: '3.x'` which selects the latest Python version (3.14+), but the project requires Python <3.14.

**Solution:**
Pin the Python version in `.github/workflows/publish-release.yml`:

```yaml
- name: Set up Python
  uses: actions/setup-python@v5
  with:
    python-version: '3.12'  # Pin to 3.12 instead of '3.x'
```

After fixing:
1. Commit the workflow fix
2. Push the fix to `master`
3. Re-trigger the workflow: `gh workflow run publish-release.yml --ref master -f version=X.Y.Z.W`

## Version Consistency Errors

**Symptom:**
```
Error: pyproject.toml version mismatch
Error: constants.py APP_VERSION mismatch
```

**Cause:** The three version files don't match:
- `pyproject.toml:8` (project version)
- `pyproject.toml:175` (hatch script version)
- `src/tunacode/constants.py:12` (APP_VERSION)

**Solution:**
Use the `bump_version.py` script which updates all three files atomically. If manually fixing:

```bash
NEW_VERSION="0.0.X.Y"

# Update pyproject.toml (both locations)
sed -i "s/version = \"OLD_VERSION\"/version = \"$NEW_VERSION\"/g" pyproject.toml

# Update constants.py
sed -i "s/APP_VERSION = \"OLD_VERSION\"/APP_VERSION = \"$NEW_VERSION\"/" src/tunacode/constants.py

# Verify consistency
grep 'version = ' pyproject.toml
grep 'APP_VERSION' src/tunacode/constants.py
```

## PyPI Authentication Failures

**Symptom:**
```
403 Forbidden
Invalid or non-existent authentication information
```

**Cause:** Missing or expired `PYPI_API_TOKEN` secret in GitHub repository settings.

**Solution:**
1. Generate a new PyPI API token at https://pypi.org/manage/account/token/
2. Add it as `PYPI_API_TOKEN` in GitHub repository secrets
3. Ensure the token has publishing permissions for `tunacode-cli`
4. Re-run the workflow

## Workflow Not Triggering

**Symptom:** The publish workflow does not start.

**Cause:** The workflow is manual. It only starts when dispatched from the GitHub UI or `gh workflow run`.

**Solution:**
1. Verify `.github/workflows/publish-release.yml` has:
   ```yaml
   on:
     workflow_dispatch:
       inputs:
         version:
           required: true
   ```

2. Run it explicitly:
   ```bash
   gh workflow run publish-release.yml --ref master -f version=X.Y.Z.W
   ```

3. Check the newest run:
   ```bash
   gh run list --workflow=publish-release.yml --limit 1
   ```

## Requested Version Does Not Match the Code

**Symptom:**
```text
pyproject.toml version mismatch
constants.py APP_VERSION mismatch
```

**Cause:** The workflow input version does not match the checked-out commit.

**Solution:**
1. Verify the release commit was pushed:
   ```bash
   git push origin master
   ```

2. Re-run the workflow with the version that is actually in the code:
   ```bash
   gh workflow run publish-release.yml --ref master -f version=X.Y.Z.W
   ```

3. If the code version is wrong, fix the version files, push the commit, and then dispatch again.

## Test Failures in Workflow

**Symptom:**
```
Error: Process completed with exit code 1.
pytest failed
```

**Cause:** Tests pass locally but fail in CI (usually environment differences).

**Solution:**
1. Check test configuration in `pytest.ini`
2. Verify all test dependencies are in `pyproject.toml` dev dependencies
3. Run tests in clean environment: `python -m venv test_env && source test_env/bin/activate && pip install -e '.[dev]' && pytest`
4. Fix failing tests before retrying release

## Monitoring Workflow Status

To check workflow status and logs:

```bash
# List recent workflows
gh run list --workflow=publish-release.yml --limit 5

# Watch workflow in real-time
gh run watch

# View failed workflow logs
gh run view <run-id> --log-failed

# View specific job logs
gh run view <run-id> --log --job=<job-id>
```
