# Research - Panel Width Inconsistency

**Date:** 2025-12-23
**Owner:** agent
**Phase:** Research

## Goal

Identify all sources of inconsistent panel widths in the TUI tool output display.

## Findings

### Constants Definition
- `src/tunacode/constants.py:39` - `TOOL_PANEL_WIDTH = 100`

### Files Using TOOL_PANEL_WIDTH Correctly (16 Panel sites)
- `src/tunacode/ui/renderers/panels.py` - 7 uses (lines 156, 208, 255, 330, 346, 359, 372)
- `src/tunacode/ui/renderers/tools/bash.py:246`
- `src/tunacode/ui/renderers/tools/glob.py:225`
- `src/tunacode/ui/renderers/tools/grep.py:227`
- `src/tunacode/ui/renderers/tools/list_dir.py:199`
- `src/tunacode/ui/renderers/tools/read_file.py:225`
- `src/tunacode/ui/renderers/tools/research.py:293`
- `src/tunacode/ui/renderers/tools/update_file.py:236`
- `src/tunacode/ui/renderers/tools/web_fetch.py:181`

### Files MISSING TOOL_PANEL_WIDTH (Root Cause)
1. **`src/tunacode/ui/renderers/search.py:169`** - `render_empty_results()` creates Panel without width
2. **`src/tunacode/ui/app.py:505`** - Tool confirmation panel created without width

## Key Patterns / Solutions Found

- All panels should use `width=TOOL_PANEL_WIDTH` with `expand=False`
- Pattern: `Panel(..., expand=False, width=TOOL_PANEL_WIDTH)`

## Knowledge Gaps

- None - root cause identified

## References

- `src/tunacode/constants.py` - TOOL_PANEL_WIDTH definition
- `src/tunacode/ui/renderers/panels.py` - Main panel renderer (fixed)
- `src/tunacode/ui/renderers/search.py` - Missing width on line 169
- `src/tunacode/ui/app.py` - Missing width on line 505
