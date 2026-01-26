# Dependency Map

> **Baseline frozen: 2026-01-26**
> Generated with [grimp](https://github.com/python-grimp/grimp)

## Layer Hierarchy (high to low)

```
ui          → outer layer (TUI)
core        → business logic
tools       → agent tools
indexing    → code indexing infrastructure
lsp         → language server protocol
templates   → prompt templates
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
| core → configuration | 4 | ✅ valid |
| core → constants | 4 | ✅ valid |
| core → exceptions | 3 | ✅ valid |
| core → indexing | 2 | ✅ valid |
| core → tools | 18 | ✅ valid |
| core → types | 22 | ✅ valid |
| core → utils | 13 | ✅ valid |
| exceptions → types | 1 | ✅ valid |
| indexing → utils | 1 | ✅ valid |
| lsp → utils | 1 | ✅ valid |
| tools → configuration | 2 | ✅ valid |
| tools → constants | 5 | ✅ valid |
| tools → exceptions | 3 | ✅ valid |
| tools → indexing | 1 | ✅ valid |
| tools → lsp | 1 | ✅ valid |
| tools → templates | 1 | ✅ valid |
| tools → types | 8 | ✅ valid |
| tools → utils | 4 | ✅ valid |
| ui → configuration | 8 | ✅ valid |
| ui → constants | 24 | ✅ valid |
| ui → core | 9 | ✅ valid |
| ui → exceptions | 2 | ✅ valid |
| ui → types | 6 | ✅ valid |
| ui → utils | 11 | ✅ valid |
| utils → configuration | 2 | ✅ valid |
| utils → constants | 6 | ✅ valid |
| utils → exceptions | 2 | ✅ valid |
| utils → types | 4 | ✅ valid |
| ui → lsp | 1 | ❌ violation |

### Violations

**1 violations found.** UI must not import directly from tools/lsp.

| From Layer | To Layer | Importer | Imported |
|------------|----------|----------|----------|
| ui | lsp | `ui.widgets.resource_bar` | `lsp.servers` |

## Rules

1. **Outward flow**: ui → core → tools → infrastructure
2. **Utils-level**: `utils/`, `types/`, `configuration/`, `constants.py` can be imported from any layer
3. **No backward imports**: tools cannot import from core, core cannot import from ui

## Verification

```bash
uv run python scripts/generate-dependency-map.py
```

## UI Layer Detail

Starting point for clean mapping. The UI layer imports:

- **core (9)**:
- **configuration (8)**:
- **constants (24)**:
- **utils (11)**:
- **types (6)**:
- **lsp (1)**: ⚠️
- **exceptions (2)**:

⚠️ = violation (UI should delegate to core, not import directly)
