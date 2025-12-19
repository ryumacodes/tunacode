# Research - NeXTSTEP Tool Panel Audit (Issue #185)

**Date:** 2025-12-18
**Owner:** Claude Agent
**Phase:** Research
**GitHub Issue:** https://github.com/alchemiststudiosDOTai/tunacode/issues/185

## Goal

Map out and audit all tool panel renderers for NeXTSTEP 4-zone layout compliance as requested in issue #185: "refactor: Tool panels don't follow NeXTSTEP UI guidelines".

## Issue Summary

**Problem Statement:** Tool result panels don't fully adhere to the NeXTSTEP UI design philosophy. Specifically:
1. Missing/incorrect metadata - Tools show "unknown" for filepath, args when available
2. Inconsistent zone layout - Panels don't consistently follow 4-zone layout
3. Missing status metrics - Duration, line counts, truncation not consistent
4. No visual hierarchy - All information has same visual weight

**4-Zone NeXTSTEP Layout Standard:**
```
┌─────────────────────────────────────────┐
│ HEADER: tool_name [status]              │  <- identifier + state
├─────────────────────────────────────────┤
│ CONTEXT: key parameters                 │  <- what was acted on
├─────────────────────────────────────────┤
│                                         │
│ PRIMARY VIEWPORT                        │  <- main content
│ (output, diff, results)                 │
│                                         │
├─────────────────────────────────────────┤
│ STATUS: metrics, truncation, duration   │  <- footer with stats
└─────────────────────────────────────────┘
```

## Findings

### Relevant Files & Why They Matter

#### Core Panel Infrastructure
| File | Purpose |
|------|---------|
| `src/tunacode/ui/renderers/panels.py` | Base panel rendering, `RichPanelRenderer` class, `tool_panel_smart()` router |
| `src/tunacode/constants.py` | `UI_COLORS`, `MAX_PANEL_LINES`, `MAX_PANEL_LINE_WIDTH` constants |
| `src/tunacode/ui/styles.py` | Extended UI color definitions |

#### Tool-Specific Renderers (9 files)
| File | Tool | 4-Zone Compliant |
|------|------|------------------|
| `src/tunacode/ui/renderers/tools/read_file.py` | read_file | **YES** |
| `src/tunacode/ui/renderers/tools/list_dir.py` | list_dir | **YES** |
| `src/tunacode/ui/renderers/tools/grep.py` | grep | **YES** |
| `src/tunacode/ui/renderers/tools/glob.py` | glob | **YES** (minor issue) |
| `src/tunacode/ui/renderers/tools/bash.py` | bash | **YES** |
| `src/tunacode/ui/renderers/tools/web_fetch.py` | web_fetch | **YES** |
| `src/tunacode/ui/renderers/tools/research.py` | research_codebase | **YES** |
| `src/tunacode/ui/renderers/tools/update_file.py` | update_file | **YES** (5-zone with diagnostics) |
| `src/tunacode/ui/renderers/tools/diagnostics.py` | Inline diagnostics | **YES** (2-zone inline) |

#### Design Documentation
| File | Purpose |
|------|---------|
| `docs/ui/design_philosophy.md` | Core NeXTSTEP design principles |
| `docs/ui/nextstep_panels.md` | Panel architecture specification |

### Audit Results by Tool

#### 1. read_file.py - **COMPLIANT**
- **Header**: Filename + line range (`lines 1-50`)
- **Context**: `path: {filepath}`
- **Viewport**: Line-numbered content (`{line_num:>5}| {content}`)
- **Status**: Display count, total lines, "more available" indicator, duration
- **Issues**: Falls back to "unknown" filepath if args missing (line 103) - **this is the bug reported in #185**

#### 2. list_dir.py - **COMPLIANT**
- **Header**: Directory + file/dir counts
- **Context**: `hidden: on/off`, `max: {N}`, `ignore: {N}`
- **Viewport**: Tree structure with box-drawing characters
- **Status**: Truncation indicator, line count, duration
- **Issues**: `DEFAULT_IGNORE_COUNT = 38` magic constant undocumented

#### 3. grep.py - **COMPLIANT**
- **Header**: Pattern + match count
- **Context**: `strategy:`, `case:`, `regex:`, `context:`
- **Viewport**: Grouped matches by file with line numbers
- **Status**: Truncation, files searched, duration
- **Issues**: Strategy defaults to "smart" silently if parsing fails

#### 4. glob.py - **COMPLIANT (minor bug)**
- **Header**: Pattern + file count
- **Context**: `recursive:`, `hidden:`, `sort:`
- **Viewport**: File path list
- **Status**: Source (indexed/scanned), truncation, duration
- **Issues**: **Dead code at line 207** - border_color logic both branches identical:
  ```python
  border_color = UI_COLORS["success"] if data.source == "index" else UI_COLORS["success"]
  ```

#### 5. bash.py - **COMPLIANT**
- **Header**: Command + exit code (green "ok" or red "exit N")
- **Context**: `cwd:`, `timeout:`
- **Viewport**: Separate stdout/stderr sections
- **Status**: Truncation, line counts, duration
- **Issues**: Working dir defaults to "." - acceptable fallback

#### 6. web_fetch.py - **COMPLIANT**
- **Header**: Domain + line count
- **Context**: `url:`, `timeout:`
- **Viewport**: Fetched content
- **Status**: Truncation, line count, duration
- **Issues**: Magic numbers `30` (domain length) and `70` (URL truncation)

#### 7. research.py - **EXEMPLARY**
- **Header**: Query string (truncated if needed)
- **Context**: `dirs:`, `max_files:`
- **Viewport**: Files, findings, recommendations sections
- **Status**: File count, finding count, duration
- **Issues**: None - excellent use of symbolic constants

#### 8. update_file.py - **COMPLIANT (5-zone)**
- **Header**: Filename + +/- stats
- **Context**: `path:` filepath
- **Viewport**: Syntax-highlighted diff
- **Status**: Hunk count, truncation, duration
- **Zone 5**: LSP diagnostics (conditional)
- **Issues**: None - proper extension to 5-zone for diagnostics

#### 9. diagnostics.py - **COMPLIANT (inline)**
- **Header**: Color-coded error/warning/info counts
- **Viewport**: Diagnostic list with line numbers
- **Issues**: None - purpose-built for embedding

### Tools WITHOUT Specialized Renderers

The following tools fall back to generic `tool_panel()` rendering:
- `write_file` - **NEEDS RENDERER** (similar to update_file)
- `ask_human` - Low priority (simple text)
- `TodoWrite` / `TodoRead` - Low priority (internal)
- MCP tools - Dynamic, may need generic handling

### Related PRs Already Merged

| PR | Description | Status |
|----|-------------|--------|
| #165 | Add NeXTSTEP-style tool panel renderers | Merged (v0.1.7) |
| #122 | Enhance research agent UI with distinctive purple panel | Merged |
| #180 | Add subagent UI loading states with progress feedback | Merged (v0.1.10) |
| #186 | LSP diagnostics display | Merged (v0.1.11) |

### Related Issues

| Issue | Relation |
|-------|----------|
| #163 | Possible duplicate - panel rendering concerns |
| #184 | Related - UI consistency |
| #52 | Unknown context |
| #97 | Unknown context |

## Key Patterns / Solutions Found

### Common Renderer Architecture
All tool renderers share:
1. **Dataclass** for parsed data (e.g., `ReadFileData`, `GrepData`)
2. **parse_result()** function extracting structured data from tool output
3. **render_{tool}()** main function creating Rich Panel
4. **_truncate_line()** helper using `MAX_PANEL_LINE_WIDTH`
5. **Consistent Panel config**: `padding=(0, 1)`, `expand=False`

### Zone Separation Pattern
```python
separator = Text(BOX_HORIZONTAL * SEPARATOR_WIDTH, style="dim")
content_parts.append(separator)
```

### Fallback Handling
Most renderers have fallback values:
- `read_file`: filepath → "unknown"
- `bash`: working_dir → "."
- `grep`: strategy → "smart"
- `web_fetch`: domain → first 30 chars

## Knowledge Gaps

1. **NeXTSTEP-ui Skill Missing**: The `.claude/skills/neXTSTEP-ui/` referenced in CLAUDE.md does not exist yet
2. **write_file Renderer Missing**: No specialized renderer for write_file tool
3. **"Unknown" Bug Root Cause**: Need to trace why filepath shows "unknown" - is it args not being passed to renderer?

## Acceptance Criteria Mapping

From issue #185:

| Criteria | Current State |
|----------|---------------|
| All tool panels follow consistent 4-zone layout | **DONE** - All 9 renderers compliant |
| No "unknown" values when info available | **PARTIAL** - Fallbacks exist, need to trace args passing |
| Header shows: tool name + status indicator | **DONE** |
| Context zone shows: key parameters | **DONE** |
| Viewport shows: primary content with formatting | **DONE** |
| Status zone shows: relevant metrics | **DONE** |
| Consistent styling across all tool panels | **DONE** |
| Call neXTSTEP-ui skill before implementing | **BLOCKED** - Skill doesn't exist |

## Recommendations for Implementation

### Priority 1 - Fix "Unknown" Values Bug
Trace why `read_file` and other tools show "unknown":
1. Check `tool_panel_smart()` in panels.py - is `args` being passed correctly?
2. Check tool execution flow - where are args captured and forwarded to renderer?
3. Verify the renderer's `parse_result()` is receiving args dict

### Priority 2 - Fix Dead Code
- `glob.py:207` - Make indexed vs scanned sources visually distinct

### Priority 3 - Extract Magic Numbers
- `web_fetch.py:52` - `30` chars for domain truncation
- `web_fetch.py:115` - `70` chars for URL truncation
- `list_dir.py:17` - Document why `DEFAULT_IGNORE_COUNT = 38`

### Priority 4 - Add write_file Renderer
Create `src/tunacode/ui/renderers/tools/write_file.py` following the update_file.py pattern.

### Priority 5 - Create NeXTSTEP-ui Skill
Create `.claude/skills/neXTSTEP-ui/SKILL.md` with design guidelines for future UI changes.

## References

### Design Documentation
- `docs/ui/design_philosophy.md` - Core NeXTSTEP principles
- `docs/ui/nextstep_panels.md` - Panel architecture specification
- `CLAUDE.md` - Project instructions with UI rules

### Implementation Files
- `src/tunacode/ui/renderers/panels.py` - Base panel rendering
- `src/tunacode/ui/renderers/tools/__init__.py` - Tool renderer registry
- `src/tunacode/constants.py` - UI constants

### GitHub
- Issue: https://github.com/alchemiststudiosDOTai/tunacode/issues/185
- Related: #163, #184, #52, #97
