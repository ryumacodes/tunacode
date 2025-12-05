# Research – UI and Theme Unification

**Date:** 2025-12-04
**Owner:** Claude Agent
**Phase:** Research

## Goal

Map out the current UI and theme system to identify opportunities for unification and consistency improvements.

## Findings

### Architecture Overview

TunaCode uses **Textual** (Python TUI framework) with **Rich** for content rendering. The UI follows a NeXTSTEP-inspired zone-based layout.

### File Inventory

| File | Purpose |
|------|---------|
| `src/tunacode/ui/app.py` | Main TextualReplApp class, compose method, event handlers |
| `src/tunacode/ui/app.tcss` | Primary TCSS stylesheet (NeXTSTEP zones) |
| `src/tunacode/constants.py` | UI_COLORS dict (lines 109-124), build_tunacode_theme() (lines 195-220) |
| `src/tunacode/ui/widgets/resource_bar.py` | Top bar: model, tokens, cost |
| `src/tunacode/ui/widgets/status_bar.py` | Bottom 3-column status bar |
| `src/tunacode/ui/widgets/editor.py` | Command input widget |
| `src/tunacode/ui/widgets/file_autocomplete.py` | @ mention file completion |
| `src/tunacode/ui/components/tool_panel.py` | Tool execution display |
| `src/tunacode/ui/components/error_display.py` | Error display component |
| `src/tunacode/ui/components/search_results.py` | Search results table |
| `src/tunacode/ui/renderers/panels.py` | Rich panel rendering (PANEL_STYLES pattern) |
| `src/tunacode/ui/renderers/search.py` | Search result rendering |
| `src/tunacode/ui/renderers/errors.py` | Error rendering functions |
| `src/tunacode/ui/screens/setup.py` | Setup wizard screen |
| `src/tunacode/ui/commands/__init__.py` | Command system (/help, /clear, etc.) |

### Color Palette (UI_COLORS)

Defined in `src/tunacode/constants.py:109-124`:

```python
UI_COLORS = {
    "background": "#1a1a1a",  # Near black
    "surface": "#252525",     # Panel background
    "border": "#ff6b9d",      # Magenta borders
    "text": "#e0e0e0",        # Primary text (high contrast)
    "muted": "#808080",       # Secondary text
    "primary": "#00d7d7",     # Cyan - model, tokens
    "accent": "#ff6b9d",      # Magenta - brand
    "success": "#4ec9b0",     # Green - costs
    "warning": "#c3e88d",     # Yellow/lime
    "error": "#f44747",       # Red
}
```

### Layout Structure (NeXTSTEP Zones)

```
◇ tokens: 1.2k ◇ model ◇ $0.00 ◇ tunacode     [ResourceBar - height: 1]
┌────────────────────────────────────────────────┐
│                                                │
│  Main viewport (RichLog - height: 1fr)         │
│                                                │
├────────────────────────────────────────────────┤
│ Editor (height: 6, Enter to submit)            │
└────────────────────────────────────────────────┘
[branch] [edited files] [last action]             [StatusBar - height: 1]
```

## Key Patterns / Solutions Found

### Pattern 1: Three Parallel Styling Systems

| System | Location | Usage |
|--------|----------|-------|
| **TCSS Variables** | `app.tcss`, widget `DEFAULT_CSS` | `$primary`, `$accent`, `$error` |
| **UI_COLORS Dict** | `renderers/panels.py`, `renderers/search.py` | `UI_COLORS["primary"]` |
| **Hardcoded Strings** | `app.py`, `resource_bar.py` | `"cyan"`, `"magenta bold"` |

### Pattern 2: PANEL_STYLES (Best Practice)

Found in `src/tunacode/ui/renderers/panels.py:28-59`:

```python
PANEL_STYLES: dict[PanelType, dict[str, str]] = {
    PanelType.TOOL: {
        "border": UI_COLORS["primary"],
        "title": UI_COLORS["primary"],
        "subtitle": UI_COLORS["muted"],
    },
    PanelType.ERROR: {
        "border": UI_COLORS["error"],
        ...
    },
}
```

This is the **gold standard** pattern for style management.

### Pattern 3: State-Based CSS Classes

```css
/* app.tcss */
RichLog.streaming { border: solid $accent; }
RichLog.paused { border: solid $warning; }
.tool-panel.running { border: solid $accent; }
.tool-panel.completed { border: solid $success; }
.tool-panel.failed { border: solid $error; }
```

Dynamic class toggling in Python:
```python
self.rich_log.add_class("streaming")
self.rich_log.remove_class("streaming")
```

## Inconsistencies Found

### Hardcoded Color Strings (Need Replacement)

| File | Line(s) | Current | Should Be |
|------|---------|---------|-----------|
| `app.py` | 120-122 | `"magenta bold"`, `"cyan"`, `"dim"` | `UI_COLORS["accent"]`, `UI_COLORS["primary"]`, `UI_COLORS["muted"]` |
| `app.py` | 290-330 | `"bold cyan"`, `"bold green"`, `"bold red"` | `UI_COLORS` references |
| `resource_bar.py` | 54-57 | `"green"`, `"yellow"`, `"red"` | `UI_COLORS["success"]`, `UI_COLORS["warning"]`, `UI_COLORS["error"]` |
| `resource_bar.py` | 79, 84 | `"cyan"`, `"green"` | `UI_COLORS["primary"]`, `UI_COLORS["success"]` |
| `commands/__init__.py` | 33 | `style="cyan"` | `UI_COLORS["primary"]` |

### Style Definition Locations (Scattered)

- `app.tcss` - Main TCSS styles
- `screens/setup.py:27-91` - Inline DEFAULT_CSS
- `components/tool_panel.py:23-61` - Inline DEFAULT_CSS
- `components/error_display.py:21-64` - Inline DEFAULT_CSS
- `components/search_results.py` - Inline DEFAULT_CSS

## Knowledge Gaps

1. **No unified style constants module** - Hardcoded color strings must be hunted down
2. **Rich vs Textual style separation** - No clear guidance on when to use which
3. **Missing style documentation** - No design system docs

## Recommendations for Unification

### 1. Create Style Constants Module

Create `src/tunacode/ui/styles.py`:

```python
from tunacode.constants import UI_COLORS

# Rich Text style strings
STYLE_PRIMARY = UI_COLORS["primary"]
STYLE_ACCENT = UI_COLORS["accent"]
STYLE_SUCCESS = UI_COLORS["success"]
STYLE_WARNING = UI_COLORS["warning"]
STYLE_ERROR = UI_COLORS["error"]
STYLE_MUTED = UI_COLORS["muted"]

# Composite styles
STYLE_HEADING = f"bold {STYLE_ACCENT}"
STYLE_SUBHEADING = f"bold {STYLE_PRIMARY}"
STYLE_DIM = "dim"
```

### 2. Replace Hardcoded Strings

Target files:
- `src/tunacode/ui/app.py` (~10 occurrences)
- `src/tunacode/ui/widgets/resource_bar.py` (~5 occurrences)
- `src/tunacode/ui/commands/__init__.py` (~1 occurrence)

### 3. Consolidate DEFAULT_CSS

Options:
- Move inline CSS to `app.tcss` (preferred)
- Create component-specific `.tcss` files
- Keep inline but use shared style mixins

### 4. Document the Design System

Create `docs/design-system.md` covering:
- Color palette usage
- Component styling patterns
- When to use TCSS vs Rich styles
- State class naming conventions

## References

- `src/tunacode/constants.py` - Color definitions, theme builder
- `src/tunacode/ui/app.tcss` - Primary stylesheet
- `src/tunacode/ui/renderers/panels.py` - PANEL_STYLES pattern (best practice example)
- `src/tunacode/ui/app.py` - Main application with inline Rich styles
- `src/tunacode/ui/widgets/resource_bar.py` - Widget with hardcoded colors

## Summary

The UI uses Textual + Rich with a NeXTSTEP zone layout. Colors are centralized in `UI_COLORS` but applied inconsistently through three parallel systems:

1. **TCSS variables** (good - used in stylesheets)
2. **UI_COLORS dictionary** (good - used in renderers)
3. **Hardcoded strings** (bad - needs elimination)

**Priority fixes:**
1. Create `src/tunacode/ui/styles.py` with Rich-compatible constants
2. Replace ~16 hardcoded color strings with symbolic references
3. Consider consolidating inline DEFAULT_CSS into `app.tcss`
