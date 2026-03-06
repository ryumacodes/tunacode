---
title: "GitHub release publish workflow: skip existing PyPI artifacts"
type: delta
created_at: 2026-03-06T05:18:58Z
updated_at: 2026-03-06T05:18:58Z
uuid: ba502a45-cae9-4026-8c3c-a4167ad8213b
---

# GitHub release publish workflow: skip existing PyPI artifacts

## Summary
- Updated `.github/workflows/publish-release.yml` to use `twine upload --skip-existing`.
- This allows a GitHub Release to be published after a manual PyPI upload without failing on duplicate distributions.

## Reasoning
`v0.1.84` was already uploaded to PyPI manually. Publishing the matching GitHub Release triggers the PyPI workflow, so the workflow must tolerate already-published artifacts.
