# Task 09: Architecture Enforcement Tests

## Summary
Automated enforcement of architectural boundaries is implemented via `tests/architecture/`. Two test files enforce the layered dependency direction: import ordering within files and forbidden cross-layer imports.

## Context
| Test | Purpose | Status |
|------|---------|--------|
| `test_import_order.py` | Imports sorted by layer rank (types/utils → tools → core → ui) | ✅ 130 parametrized tests |
| `test_layer_dependencies.py` | No backward imports (core → ui, tools → core/ui, utils → core/tools/ui) | ✅ 4 parametrized tests |

## Dependency Rules Enforced

```
Layer Order (lowest to highest rank):
┌─────────────────────────────────────────────────────┐
│ Shared: types, utils, configuration, constants, etc │  rank 0-8
├─────────────────────────────────────────────────────┤
│ tools                                              │  rank 9
├─────────────────────────────────────────────────────┤
│ core                                               │  rank 10
├─────────────────────────────────────────────────────┤
│ ui                                                 │  rank 11
└─────────────────────────────────────────────────────┘

Forbidden Imports:
- core → ui (UI_PREFIX)
- tools → ui, core (UI_PREFIX, CORE_PREFIX)
- utils → ui, core, tools (UI_PREFIX, CORE_PREFIX, TOOLS_PREFIX)
- types → ui, core, tools (UI_PREFIX, CORE_PREFIX, TOOLS_PREFIX)
```

## Run Tests

```bash
uv run pytest tests/architecture/ -v
```

## Related Docs
- [PLAN.md](../../PLAN.md)
- [Architecture Refactor Status Research](../../memory-bank/research/2026-01-25_architecture-refactor-status.md)
- [Architecture Documentation](../../docs/codebase-map/architecture/architecture.md)
