---
title: Bump tiny-agent-os baseline to 1.2.7
type: delta
link: tiny-agent-os-1-2-7-baseline
path: pyproject.toml
depth: 1
seams: [M]
ontological_relations:
  - affects: [[dependencies]]
  - affects: [[tinyagent]]
tags:
  - tinyagent
  - deps
  - lockfile
created_at: 2026-03-04T20:31:00+00:00
updated_at: 2026-03-04T20:31:00+00:00
uuid: 19bdb8c9-cca8-4c2d-b926-6674b13a6161
---

# Bump tiny-agent-os baseline to 1.2.7

## Summary

Raised the project dependency floor from `tiny-agent-os>=1.2.5` to `tiny-agent-os>=1.2.7` and refreshed `uv.lock`.

Lockfile resolution now pins `tiny-agent-os==1.2.7` and records its new transitive requirements:

- `pydantic`
- `pydantic-core`
- `annotated-types`
- `typing-inspection`

## Why

Typed contracts required by the typed tinyagent cutover are introduced in the 1.2.7+ release line.

## Validation

- `uv lock --upgrade-package tiny-agent-os` ✅
- `uv run python -c "import importlib.metadata as md; print(md.version('tiny-agent-os'))"` → `1.2.7` ✅
