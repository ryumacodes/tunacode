# Dependency Map

> **Baseline frozen: 2026-01-27**
> Generated with [grimp](https://github.com/python-grimp/grimp)

## Layer Hierarchy (high to low)

```
ui          → outer layer (TUI)
core        → business logic
tools       → agent tools
indexing    → code indexing infrastructure
lsp         → language server protocol
─────────────────────────────────
utils       ┐
types       │ utils-level (importable from anywhere)
configuration│
constants   ┘
```

## Current State

![Dependency Graph](layers.png)

### Import Counts (grimp)

| From | To | Count | Status |
|------|----|-------|--------|
| configuration → constants | 3 | ✅ valid |
| configuration → types | 3 | ✅ valid |
| core → configuration | 8 | ✅ valid |
| core → constants | 5 | ✅ valid |
| core → exceptions | 4 | ✅ valid |
| core → indexing | 2 | ✅ valid |
| core → tools | 10 | ✅ valid |
| core → types | 24 | ✅ valid |
| core → utils | 18 | ✅ valid |
| exceptions → types | 1 | ✅ valid |
| indexing → utils | 1 | ✅ valid |
| lsp → utils | 1 | ✅ valid |
| tools → configuration | 2 | ✅ valid |
| tools → constants | 2 | ✅ valid |
| tools → exceptions | 3 | ✅ valid |
| tools → indexing | 1 | ✅ valid |
| tools → lsp | 2 | ✅ valid |
| tools → types | 1 | ✅ valid |
| tools → utils | 4 | ✅ valid |
| ui → core | 51 | ✅ valid |
| utils → configuration | 2 | ✅ valid |
| utils → constants | 5 | ✅ valid |
| utils → exceptions | 2 | ✅ valid |
| utils → types | 3 | ✅ valid |

### Violations

**None.** All dependencies flow in valid directions.

## Rules

1. **Outward flow**: ui → core → tools → infrastructure
2. **Utils-level**: `utils/`, `types/`, `configuration/`, `constants.py` importable anywhere
3. **No backward imports**: tools cannot import from core, core cannot import from ui

## Verification

```bash
uv run python scripts/generate-dependency-map.py
```

## UI Layer Detail

Starting point for clean mapping. The UI layer imports:

- **core (51)**:
