---
title: Layer Dependency Tests
link: layer-dependency-tests
type: doc
path: docs/architecture/dependencies/layer_dependency_tests.md
depth: 3
seams: [A]
ontological_relations:
  - relates_to: [[architecture]]
  - affects: [[tests]]
tags:
  - architecture
  - dependencies
  - tests
created_at: 2026-01-28T12:29:20-06:00
updated_at: 2026-01-28T12:30:26-06:00
uuid: 93a21c4c-99e1-4268-8e1c-cf4bc5c8b87f
---

# Layer Dependency Tests

## Summary
These tests enforce the project’s dependency direction rules (ui → core → tools → lsp with utils-level helpers accessible to all layers). They prevent cross-layer imports that would violate the architecture.

## When to Read
Read this when you add cross-layer imports, adjust module boundaries, or see architecture test failures in CI.

## Tests and Enforcement

### `tests/test_dependency_layers.py`
- Uses `grimp` to build a full import graph for `tunacode`.
- Allows imports into `utils`, `types`, `configuration`, `constants`, and `exceptions` from any layer.
- Ensures only these direct layer transitions are allowed:
  - `ui → core`
  - `core → tools`
  - `tools → lsp`
- Fails if new violations appear beyond the frozen baseline.

Run:
```
uv run pytest tests/test_dependency_layers.py -v
```

### `tests/architecture/test_layer_dependencies.py`
- Scans Python files with `ast` to detect forbidden import prefixes.
- Enforces:
  - `core` cannot import `ui`
  - `tools` cannot import `ui` or `core`
  - `utils` and `types` cannot import `ui`, `core`, or `tools`
- Has no allowlisted exceptions.

Run:
```
uv run pytest tests/architecture/test_layer_dependencies.py -v
```

## Common Failure Causes
- New cross-layer imports added in a tool module.
- UI code importing tool implementations directly.
- Core or tools importing from UI modules instead of passing callbacks.
