# PyPI release 0.1.85

## Summary
- Bumped the packaged TunaCode version from `0.1.84` to `0.1.85`.
- Synced release metadata in `pyproject.toml`, `src/tunacode/constants.py`, and `uv.lock`.
- Added a changelog entry for the `/skills` autocomplete ranking fix and the slash-command argument isolation fix.

## Files
- `pyproject.toml`
- `src/tunacode/constants.py`
- `uv.lock`
- `CHANGELOG.md`

## Reasoning
A new patch release was needed because `master` contains user-facing fixes for `/skills` selection and navigation after `v0.1.84`, while the current PyPI package still published the broken behavior.
