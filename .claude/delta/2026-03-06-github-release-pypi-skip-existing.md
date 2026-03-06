# GitHub release publish workflow: skip existing PyPI artifacts

## Summary
- Updated `.github/workflows/publish-release.yml` to use `twine upload --skip-existing`.
- This allows a GitHub Release to be published after a manual PyPI upload without failing on duplicate distributions.

## Reasoning
`v0.1.84` was already uploaded to PyPI manually. Publishing the matching GitHub Release triggers the PyPI workflow, so the workflow must tolerate already-published artifacts.
