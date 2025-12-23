# Research - Issue #184: Standardize Tool Panel Viewport Sizing

**Date:** 2025-12-18
**Owner:** Research Agent
**Phase:** Research
**GitHub Issue:** https://github.com/alchemiststudiosDOTai/tunacode/issues/184
**Last Updated:** 2025-12-18 18:30
**Last Updated By:** Research Agent
**Last Updated Note:** Resolved knowledge gaps - confirmed bash.py (6-line) and list_dir.py (0-line) reserves are bugs

## Goal

Analyze and document the current state of tool panel viewport sizing across all renderers to prepare for standardization per the NeXTSTEP "uniformity" principle.

## Search Methodology

- Grep: `MAX_PANEL_LINES` usage across codebase
- Grep: `_truncate_line` implementations
- Grep: viewport-related calculations
- File analysis: All 9 tool renderers in `src/tunacode/ui/renderers/tools/`

## Findings

### Constants Definition

**Location:** [`src/tunacode/constants.py:31-32`](https://github.com/alchemiststudiosDOTai/tunacode/blob/a21af540583be01d8ada3e4a7742faea53f8ccbd/src/tunacode/constants.py#L31-L32)

```python
MAX_PANEL_LINES = 30      # Focus zone limit for tool results
MAX_PANEL_LINE_WIDTH = 200  # Individual line truncation
```

### Current Viewport Calculations by Renderer

| Renderer | File:Line | Reserved Lines | Usable Viewport | Implementation |
|----------|-----------|----------------|-----------------|----------------|
| bash.py | [L103](https://github.com/alchemiststudiosDOTai/tunacode/blob/a21af540583be01d8ada3e4a7742faea53f8ccbd/src/tunacode/ui/renderers/tools/bash.py#L103) | 6 | 24 | `MAX_PANEL_LINES - 6` |
| grep.py | [L165](https://github.com/alchemiststudiosDOTai/tunacode/blob/a21af540583be01d8ada3e4a7742faea53f8ccbd/src/tunacode/ui/renderers/tools/grep.py#L165) | 2 | 28 | `MAX_PANEL_LINES - 2` |
| read_file.py | [L163](https://github.com/alchemiststudiosDOTai/tunacode/blob/a21af540583be01d8ada3e4a7742faea53f8ccbd/src/tunacode/ui/renderers/tools/read_file.py#L163) | 2 | 28 | `MAX_PANEL_LINES - 2` |
| glob.py | [L162](https://github.com/alchemiststudiosDOTai/tunacode/blob/a21af540583be01d8ada3e4a7742faea53f8ccbd/src/tunacode/ui/renderers/tools/glob.py#L162) | 2 | 28 | `MAX_PANEL_LINES - 2` |
| list_dir.py | [L100](https://github.com/alchemiststudiosDOTai/tunacode/blob/a21af540583be01d8ada3e4a7742faea53f8ccbd/src/tunacode/ui/renderers/tools/list_dir.py#L100) | 0 | 30 | `MAX_PANEL_LINES` (no reserve) |
| web_fetch.py | [L81](https://github.com/alchemiststudiosDOTai/tunacode/blob/a21af540583be01d8ada3e4a7742faea53f8ccbd/src/tunacode/ui/renderers/tools/web_fetch.py#L81) | 4 | 26 | `MAX_PANEL_LINES - 4` |
| update_file.py | [L108](https://github.com/alchemiststudiosDOTai/tunacode/blob/a21af540583be01d8ada3e4a7742faea53f8ccbd/src/tunacode/ui/renderers/tools/update_file.py#L108) | 4 | 26 | `MAX_PANEL_LINES - 4` |
| research.py | [L167](https://github.com/alchemiststudiosDOTai/tunacode/blob/a21af540583be01d8ada3e4a7742faea53f8ccbd/src/tunacode/ui/renderers/tools/research.py#L167) | 4 | 26 | `LINES_RESERVED_FOR_HEADER_FOOTER` constant |
| diagnostics.py | [L14](https://github.com/alchemiststudiosDOTai/tunacode/blob/a21af540583be01d8ada3e4a7742faea53f8ccbd/src/tunacode/ui/renderers/tools/diagnostics.py#L14) | N/A | 10 | `MAX_DIAGNOSTICS_DISPLAY = 10` (independent) |

### Root Cause Analysis

1. **No shared constant:** Each renderer manually calculates viewport with different magic numbers
2. **Only research.py is correct:** Uses symbolic constant `LINES_RESERVED_FOR_HEADER_FOOTER = 4` at line 27
3. **Inconsistent reasoning:** The -2, -4, -6 variations suggest ad-hoc decisions without unified design

### Line Truncation Inconsistencies

**Standard Pattern (7 renderers):**
```python
if len(line) > MAX_PANEL_LINE_WIDTH:
    return line[: MAX_PANEL_LINE_WIDTH - 3] + "..."
```

**BUG in list_dir.py:88-92:**
```python
if len(line) > MAX_PANEL_LINE_WIDTH:
    return line[:MAX_PANEL_LINE_WIDTH] + "..."  # Missing -3 subtraction!
```
This produces lines of 203 characters instead of 200.

**glob.py Special Case:** Uses `_truncate_path()` instead of `_truncate_line()` to preserve filenames.

### Dead Code Identified

**Location:** [`glob.py:207`](https://github.com/alchemiststudiosDOTai/tunacode/blob/a21af540583be01d8ada3e4a7742faea53f8ccbd/src/tunacode/ui/renderers/tools/glob.py#L207)

```python
border_color = UI_COLORS["success"] if data.source == "index" else UI_COLORS["success"]
```

Both branches return identical values, making the conditional meaningless.

### Duplicated Constants

**BOX_HORIZONTAL and SEPARATOR_WIDTH** are defined locally in 9 files:

| File | Lines |
|------|-------|
| bash.py | 17-18 |
| diagnostics.py | 16-17 |
| glob.py | 18-19 |
| grep.py | 17-18 |
| list_dir.py | 18-19 |
| read_file.py | 18-19 |
| research.py | 18-19 |
| update_file.py | 19-20 |
| web_fetch.py | 17-18 |

All define `SEPARATOR_WIDTH = 52` and `BOX_HORIZONTAL = "\u2500"` (or `"─"`).

### Other Magic Numbers

**web_fetch.py:**
- Line 52: `30` chars for domain truncation fallback
- Line 115-116: `70`/`67` chars for URL display truncation

**research.py (good example):**
- Line 25: `MAX_QUERY_DISPLAY_LENGTH = 60`
- Line 24: `ELLIPSIS_LENGTH = 3`
- Line 27: `LINES_RESERVED_FOR_HEADER_FOOTER = 4`

## Key Patterns / Solutions Found

### Existing Best Practice: research.py

[`research.py:21-29`](https://github.com/alchemiststudiosDOTai/tunacode/blob/a21af540583be01d8ada3e4a7742faea53f8ccbd/src/tunacode/ui/renderers/tools/research.py#L21-L29) demonstrates the correct approach:

```python
# Symbolic constants for magic values
DEFAULT_DIRECTORY = "."
DEFAULT_MAX_FILES = 3
ELLIPSIS_LENGTH = 3
MAX_QUERY_DISPLAY_LENGTH = 60
MAX_DIRECTORIES_DISPLAY = 3
LINES_RESERVED_FOR_HEADER_FOOTER = 4
MIN_LINES_FOR_RECOMMENDATIONS = 2
MAX_FALLBACK_RESULT_LENGTH = 500
```

### 4-Zone NeXTSTEP Layout (All Renderers Compliant)

All tool renderers follow this structure:
1. **Zone 1 (Header):** Primary identifier + summary stats
2. **Zone 2 (Context):** Parameters/configuration
3. **Zone 3 (Viewport):** Primary content display
4. **Zone 4 (Status):** Metrics, truncation, timing

## Proposed Fix (from Issue #184)

1. **Add to constants.py:**
```python
LINES_RESERVED_FOR_HEADER_FOOTER = 4
TOOL_VIEWPORT_LINES = MAX_PANEL_LINES - LINES_RESERVED_FOR_HEADER_FOOTER  # = 26
```

2. **Update all 8 tool renderers** to use `TOOL_VIEWPORT_LINES`

3. **Standardize line truncation:** Ensure all use `line[:MAX_PANEL_LINE_WIDTH - 3] + "..."`

4. **Fix dead code in glob.py:207**

5. **Optional cleanup:** Extract `BOX_HORIZONTAL` and `SEPARATOR_WIDTH` to constants.py

## Knowledge Gaps

1. ~~**Why bash.py reserves 6 lines:** Needs stdout/stderr labels? Should be documented~~ RESOLVED - See Follow-up Research
2. ~~**Why list_dir uses no reserve:** Intentional design or bug?~~ RESOLVED - See Follow-up Research
3. **Test coverage:** No tests exist for viewport calculations

---

## Follow-up Research [2025-12-18 18:30]

### bash.py 6-Line Reserve Analysis

**Finding: BUG - Excessive reservation**

The bash.py renderer reserves 6 lines (`MAX_PANEL_LINES - 6` at line 103) but analysis of the actual panel structure shows:

**Panel Composition (lines 201-212):**
1. header (1 line) - Command + exit status
2. params (1 line) - Working directory + timeout
3. separator (1 line) - Horizontal rule
4. viewport (N lines) - stdout/stderr content
5. separator (1 line) - Horizontal rule
6. status (1 line) - Truncation info, duration

**Actual overhead: 5 lines** (not counting newlines which are spacing, not rendered lines)

**Critical Bug:** The `_truncate_output()` function is called **twice** when both stdout and stderr exist:
- Line 161: `stdout_content, stdout_shown, stdout_total = _truncate_output(result.stdout)`
- Line 170: `stderr_content, stderr_shown, stderr_total = _truncate_output(result.stderr)`

Each call thinks it needs to reserve 6 lines independently, meaning with both streams present, **12 lines are unnecessarily reserved** from the combined viewport.

**Recommendation:** Change `MAX_PANEL_LINES - 6` to use `TOOL_VIEWPORT_LINES` constant (26 lines) or calculate based on whether both streams are present.

---

### list_dir.py No-Reserve Analysis

**Finding: BUG - Missing reservation causes overflow**

The list_dir.py renderer uses `MAX_PANEL_LINES` directly at lines 100-103 without subtracting reserved lines:

```python
if total <= MAX_PANEL_LINES:  # Line 100: uses 30 directly
    return "\n".join(_truncate_line(ln) for ln in lines), total, total

truncated = [_truncate_line(ln) for ln in lines[:MAX_PANEL_LINES]]  # Line 103
```

**Panel Composition (lines 159-171):**
1. header (1 line)
2. blank line
3. params (1 line)
4. blank line
5. separator (1 line)
6. blank line
7. viewport (N lines) - tree content
8. blank line
9. separator (1 line)
10. blank line
11. status (1 line)

**Total non-viewport overhead: 10 lines**

When tree content fills 30 lines, the total panel becomes **40 lines**, exceeding the `MAX_PANEL_LINES = 30` focus zone limit.

**Recommendation:** Reserve at least 4 lines to match other renderers, resulting in `MAX_PANEL_LINES - 4 = 26` usable viewport lines.

---

### Truncation Bug Confirmed: list_dir.py:90-91

```python
def _truncate_line(line: str) -> str:
    if len(line) > MAX_PANEL_LINE_WIDTH:
        return line[:MAX_PANEL_LINE_WIDTH] + "..."  # BUG: produces 203 chars
```

**Correct pattern** (used by 7 other renderers):
```python
return line[: MAX_PANEL_LINE_WIDTH - 3] + "..."  # Produces exactly 200 chars
```

---

### Updated Summary Table

| Renderer | Reserved | Usable | Bug Status | Required Fix |
|----------|----------|--------|------------|--------------|
| bash.py | 6 | 24 | BUG (excessive) | Change to 4 |
| grep.py | 2 | 28 | OK but inconsistent | Change to 4 |
| read_file.py | 2 | 28 | OK but inconsistent | Change to 4 |
| glob.py | 2 | 28 | OK but inconsistent | Change to 4 |
| list_dir.py | 0 | 30 | BUG (overflow) | Change to 4 |
| web_fetch.py | 4 | 26 | Correct | Use constant |
| update_file.py | 4 | 26 | Correct | Use constant |
| research.py | 4 | 26 | Correct (best practice) | Keep as reference |

**Target standard:** All renderers should use `TOOL_VIEWPORT_LINES = 26` (MAX_PANEL_LINES - 4)

## Files Requiring Updates

| File | Change Required |
|------|-----------------|
| `src/tunacode/constants.py` | Add new constants |
| `src/tunacode/ui/renderers/tools/bash.py:103` | Use shared constant |
| `src/tunacode/ui/renderers/tools/grep.py:165` | Use shared constant |
| `src/tunacode/ui/renderers/tools/read_file.py:163` | Use shared constant |
| `src/tunacode/ui/renderers/tools/glob.py:162,207` | Use shared constant + fix dead code |
| `src/tunacode/ui/renderers/tools/list_dir.py:91,100` | Fix truncation bug + use shared constant |
| `src/tunacode/ui/renderers/tools/web_fetch.py:81` | Use shared constant |
| `src/tunacode/ui/renderers/tools/update_file.py:108` | Use shared constant |
| `src/tunacode/ui/renderers/tools/research.py` | Import from constants instead of local |

## References

### GitHub Links
- **Issue:** https://github.com/alchemiststudiosDOTai/tunacode/issues/184
- **Related Issues:** #163, #52, #126
- **Related PR:** #165 (feat: add NeXTSTEP-style tool panel renderers)

### Documentation
- `docs/ui/design_philosophy.md` - NeXTSTEP design principles
- `docs/ui/nextstep_panels.md` - 4-zone panel architecture spec
- `memory-bank/research/2025-12-18_15-30-00_nextstep-tool-panel-audit.md` - Prior audit
- `memory-bank/cleanup-sweep/duplication.md` - Documents BOX_HORIZONTAL/SEPARATOR_WIDTH duplication

### Code Style Rules (CLAUDE.md)
> "Always replace magic numbers with symbolic constants that broadcast meaning."
> "Never use magic literals; symbolic constants are preferred."
> "Normalize symmetries: you must make identical things look identical and different things look different for faster pattern-spotting."
