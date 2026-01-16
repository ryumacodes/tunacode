# Research – Tool Panel Scrolling Readability

**Date:** 2026-01-15
**Owner:** agent
**Phase:** Research

## Goal

Understand why tool panels are hard to track visually as they scroll, and identify improvement opportunities while maintaining the delicate balance of information density.

## Problem Statement

As tools execute and their output panels scroll through the RichLog viewport, it becomes difficult to:
1. Distinguish one tool's output from another
2. Track which tool is currently visible
3. Quickly scan back through tool history
4. Maintain context when many tools execute in sequence

## Findings

### Current Architecture

**All tool output flows through a single RichLog widget:**
- `src/tunacode/ui/app.py:119` - Creates RichLog with `auto_scroll=True`
- `src/tunacode/ui/app.py:355` - Writes panels: `self.rich_log.write(panel, expand=True)`
- Tools stack vertically in chronological order

**4-Zone Layout Pattern** (each tool panel has):
1. **Header**: Tool name + status indicator
2. **Parameters**: Key arguments passed to tool
3. **Viewport**: Truncated content (8 lines max)
4. **Status**: Timing, truncation info

### Visual Differentiation Mechanisms (Current)

| Mechanism | Location | Description |
|-----------|----------|-------------|
| Border color | `panels.py:34-65` | Cyan=tool, Green=success, Red=error, Yellow=warning |
| Tool name in title | `base.py:436` | `[{border_color}]{tool_name}[/] [{status}]` |
| Timestamp subtitle | `base.py:437` | Right-aligned `HH:MM:SS` |
| Internal separators | `base.py:359` | `──────────` between zones |

### What's Missing (Root Cause)

**No visual separation BETWEEN panels:**
- Natural `RichLog.write()` spacing only
- No margins/gaps defined in CSS
- Adjacent panels blend together visually

**All borders are solid lines:**
- Same border weight/style across all tools
- Subtle color differences lost at scroll speed

**No visual anchors:**
- No sticky headers
- No tool grouping/categorization
- No alternating backgrounds
- No icons or visual identifiers

### Relevant Files

| File | Purpose |
|------|---------|
| `src/tunacode/ui/app.py:347-355` | Tool result message handler |
| `src/tunacode/ui/renderers/panels.py:476-523` | `tool_panel_smart()` routing |
| `src/tunacode/ui/renderers/tools/base.py:375-441` | Base renderer 4-zone template |
| `src/tunacode/ui/styles/panels.tcss` | Panel CSS (currently minimal) |
| `src/tunacode/ui/styles/theme-nextstep.tcss:184-209` | NeXTSTEP 3D bevel effects |
| `src/tunacode/constants.py:37-45` | Viewport size constraints |

### Configuration Constants

```python
# constants.py
TOOL_VIEWPORT_LINES = 8      # Max lines per tool viewport
MIN_VIEWPORT_LINES = 3       # Minimum padding for consistency
MAX_PANEL_LINE_WIDTH = 50    # Line truncation width
STREAM_THROTTLE_MS = 100.0   # Streaming update interval
```

### CSS Structure

**Current RichLog styling** (`layout.tcss:44-49`):
```tcss
RichLog {
    height: 1fr;
    background: $background;
    padding: 1;
    scrollbar-gutter: stable;
}
```

**Panel classes exist but underutilized** (`panels.tcss`):
```tcss
.tool-panel {
    border: solid $primary;
    background: $surface;
    padding: 0 1;
    margin: 0 0 1 0;  /* 1 cell bottom margin */
}
```

## Key Patterns / Solutions Found

### Pattern 1: Increase Inter-Panel Spacing

Add explicit margin between panel writes, either:
- CSS: Increase `.tool-panel { margin: 0 0 2 0; }` (2 cell gap)
- Python: Add blank line write between panels

### Pattern 2: Alternating Visual Treatment

Alternate between two subtle background shades:
- Even panels: `$surface` (#252525)
- Odd panels: slightly lighter (`#2a2a2a`)

Would require tracking panel index in app.py.

### Pattern 3: Tool-Type Visual Signatures

Add visual identifiers per tool type:
- `bash` → `$` prefix glyph
- `read_file` → `📄` or file icon
- `grep` → `🔍` or search icon
- etc.

Currently partial - bash shows `$ command`, others don't have icons.

### Pattern 4: Section Headers

Group rapid tool executions under timestamped dividers:
```
═══════════════ 14:23:45 ═══════════════
[tool panels here]
═══════════════ 14:23:52 ═══════════════
[more tool panels]
```

Would help batch-scanning.

### Pattern 5: Thicker/Double Borders

NeXTSTEP theme already has 3D bevels - could make them more pronounced:
- Thicker bevel edges
- More contrast between light/dark sides

### Pattern 6: Sticky Tool Summary (Advanced)

Show a floating summary of currently visible tool:
- Would require custom Textual widget
- Higher implementation complexity
- May conflict with NeXTSTEP aesthetic

## Knowledge Gaps

1. **User preference data** - Which tools scroll fastest? What's the typical tool density?
2. **Accessibility requirements** - Color-blind considerations for border colors
3. **Performance impact** - Would alternating backgrounds or icons slow rendering?
4. **NeXTSTEP authenticity** - Which patterns align with original NeXTSTEP UI guidelines?

## Recommendations (Prioritized)

1. **Quick win**: Increase bottom margin in `panels.tcss` from 1 to 2-3 cells
2. **Medium effort**: Add tool-type glyphs to panel headers (consistent visual anchor)
3. **Design review**: Invoke NeXTSTEP-ui skill before implementing to ensure authenticity
4. **Future**: Consider section dividers for time-based grouping

## References

- `src/tunacode/ui/renderers/panels.py` - Core panel rendering
- `src/tunacode/ui/renderers/tools/base.py` - BaseToolRenderer with 4-zone pattern
- `src/tunacode/ui/styles/panels.tcss` - Panel CSS
- `src/tunacode/ui/styles/theme-nextstep.tcss` - NeXTSTEP theme overrides
- `.claude/skills/neXTSTEP-ui/SKILL.md` - Design philosophy reference
- `.claude/kb/patterns/panel-expansion.md` - RichLog expand=True lesson
