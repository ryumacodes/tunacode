---
title: Deployment
summary: Runbook for publishing tunacode-cli to PyPI and handling the release flow.
when_to_read:
  - When preparing a PyPI release
  - When reviewing the deployment runbook
last_updated: "2026-04-04"
---

# Deployment

This document is the repository runbook for publishing `tunacode-cli` to PyPI.

The current release flow keeps all validation local, then uses GitHub Actions for the credentialed upload step via the repository `PYPI_API_TOKEN` secret.

## Prerequisites

- Work from `master`.
- Keep the worktree clean before starting the release commit.
- Ensure `gh auth status` succeeds.
- Ensure the repository Actions secrets include `PYPI_API_TOKEN`.
- Ensure `MINIMAX_API_KEY` is available locally if you want to run the tmux E2E gate.

## Release Flow

### 1. Validate the Repository Locally

Run the local release gates first:

```bash
git status --short
git branch --show-current
uv run ruff check .
uv run pytest tests/ -q
source .venv/bin/activate && python -c "from tunacode.ui.main import app; print('IMPORT_OK')"
source .venv/bin/activate && python -m tunacode.ui.main --help
```

Run the tmux-backed E2E gate explicitly:

```bash
export TUNACODE_RUN_TMUX_TESTS=1
export TUNACODE_TEST_API_KEY="$MINIMAX_API_KEY"
uv run pytest tests/system/cli/test_tmux_tools.py -v
```

If any of these fail, stop and fix the issue before releasing.

### 2. Bump the Version

Use the repo-local release helper:

```bash
uv run python skills/pypi-release/scripts/bump_version.py
```

This updates:

- `pyproject.toml`
- `src/tunacode/constants.py`
- `README.md` when a matching version header exists

### 3. Update the Changelog

Review commits since the last tag:

```bash
git log --oneline "$(git describe --tags --abbrev=0)"..HEAD --no-merges
```

Add the new release entry near the top of `CHANGELOG.md`:

```md
## [X.Y.Z] - YYYY-MM-DD

### Added
- ...

### Changed
- ...

### Fixed
- ...
```

### 4. Re-run the Local Gates from the Bumped State

After the version and changelog changes are in place, re-run the same validation commands from step 1.

This matters because the GitHub Actions publish job will build the exact commit you push.

### 5. Commit and Push the Release

Stage the release payload and push it to `master`:

```bash
git add CHANGELOG.md pyproject.toml src/tunacode/constants.py uv.lock
git commit -m "chore(release): bump version to X.Y.Z"
git push origin master
```

If `uv.lock` changes while validating the bumped package, include it so the worktree stays clean and the lockfile matches the release commit.

### 6. Trigger the GitHub Actions Publish Job

Dispatch the manual publish workflow with the version you just pushed:

```bash
gh workflow run publish-release.yml --ref master -f version=X.Y.Z
```

The workflow in `.github/workflows/publish-release.yml` performs these checks before upload:

- Confirms the requested version matches `pyproject.toml`
- Confirms the requested version matches `src/tunacode/constants.py`
- Builds the package
- Runs `twine check dist/*`
- Uploads to PyPI with `PYPI_API_TOKEN`

### 7. Monitor the Publish Job

List the most recent publish run:

```bash
gh run list --workflow=publish-release.yml --limit 1
```

Watch the run to completion:

```bash
gh run watch --exit-status
```

Inspect logs when needed:

```bash
gh run view <run-id> --log-failed
```

## Verified Example

This flow was used successfully on `2026-03-30` to publish `0.1.101`.

Successful workflow run:

- `Release 0.1.101`
- `https://github.com/alchemiststudiosDOTai/tunacode/actions/runs/23755867893`

## Troubleshooting

### Version Mismatch

If the workflow reports a version mismatch:

- Verify `pyproject.toml` and `src/tunacode/constants.py` both match the version you passed to `gh workflow run`.
- Push the corrected commit.
- Re-dispatch the workflow with the corrected version string.

### PyPI Authentication Failure

If the upload step fails with authentication or permission errors:

- Re-check the repository `PYPI_API_TOKEN` secret.
- Confirm the token has publish permission for `tunacode-cli`.

### Node Runtime Warnings

If GitHub Actions reports JavaScript action runtime deprecation warnings, update workflow action versions in `.github/workflows/` so `actions/checkout` and `actions/setup-python` stay on Node 24-compatible majors.
