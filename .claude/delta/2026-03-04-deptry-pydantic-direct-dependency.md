---
title: Declare pydantic as a direct runtime dependency for session validation handling
type: delta
link: deptry-pydantic-direct-dependency
path: pyproject.toml
depth: 1
seams: [M]
ontological_relations:
  - affects: [[dependency-management]]
  - affects: [[session-state]]
tags:
  - dependencies
  - deptry
  - pydantic
created_at: 2026-03-05T03:58:00+00:00
updated_at: 2026-03-05T03:58:00+00:00
uuid: 8bb54104-b704-4463-b58e-89e996f3119c
---

# Declare pydantic as a direct runtime dependency for session validation handling

## Summary

`deptry` reported `DEP003` because `src/tunacode/core/session/state.py` imports `pydantic.ValidationError` directly while `pydantic` was only present transitively through `tiny-agent-os`.

## Changes

- Added `pydantic>=2,<3` to `[project].dependencies` in `pyproject.toml`.
- Updated `uv.lock` to reflect the direct dependency declaration.

## Validation

- `uv run deptry src/` ✅
- `uv run ruff check .` ✅
