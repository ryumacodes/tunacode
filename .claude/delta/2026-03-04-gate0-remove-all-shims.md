---
title: Remove src/tunacode __all__ shim exports to satisfy Gate 0
type: delta
link: gate0-remove-all-shims
path:
  - src/tunacode/**/__init__.py
  - src/tunacode/core/ui_api/*.py
  - src/tunacode/types/*.py
  - src/tunacode/tools/discover.py
  - src/tunacode/tools/ignore.py
depth: 2
seams: [M]
ontological_relations:
  - affects: [[quality-gates]]
  - affects: [[public-reexports]]
  - affects: [[tooling]]
tags:
  - gates
  - shims
  - lint
  - exports
created_at: 2026-03-04T22:10:00+00:00
updated_at: 2026-03-04T22:10:00+00:00
uuid: c3d2f5ab-a436-4e56-92ba-f40b01fdb9e2
---

# Remove src/tunacode __all__ shim exports to satisfy Gate 0

## Summary

Removed every `__all__` assignment under `src/tunacode` so `scripts/run_gates.py` Gate 0 no longer fails on shim exports.

## Key changes

- Deleted all `__all__` declarations in `src/tunacode/**` modules.
- Kept intentional re-export surfaces in aggregator modules by applying import-level `# noqa: F401` on explicit re-export imports.
- Removed discover-module compatibility re-exports that were only used by tests and switched tests/benchmarks to import helpers from `tools.utils.discover_pipeline` and `tools.utils.discover_types` directly.
- Removed unused ignore-pattern compatibility imports from `tunacode.tools.ignore`.

## Validation

- `uv run ruff check .` ✅
- `uv run pytest` ✅
- `uv run python scripts/run_gates.py` ✅ (`ALL GATES PASSED`)
