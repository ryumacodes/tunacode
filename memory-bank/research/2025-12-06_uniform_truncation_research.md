# Research – Uniform Tool Result Truncation

**Date:** 2025-12-06
**Owner:** claude-agent
**Phase:** Research

## Goal

Map out how to implement uniform truncation for tool results display in the TUI, following NeXTSTEP design principles for information hierarchy and user control.

## Findings

### Data Flow: Tool Execution to Panel Display

```
1. Tool Execution (tools/*.py)
   ↓ Returns: str (full result, may be pre-truncated)

2. Pydantic-AI wraps result in tool-return part
   ↓ Part.content = full tool result string

3. Node Processor extracts tool-return parts
   ↓ src/tunacode/core/agents/agent_components/node_processor.py:82-94
   ↓ result_str = str(content) — NO TRUNCATION

4. Tool Result Callback
   ↓ src/tunacode/ui/app.py:455-480
   ↓ ToolResultDisplay(result=result) — NO TRUNCATION

5. Message Handler
   ↓ src/tunacode/ui/app.py:291-299
   ↓ tool_panel_smart(result=message.result) — NO TRUNCATION

6. Panel Renderer Selection
   ↓ src/tunacode/ui/renderers/panels.py:351-365
   ├─→ Search tools (glob/grep): parse_glob_output() / parse_grep_output()
   │   ↓ Creates SearchResultData with list of result dicts
   │   ↓ render_search_results() — snippets truncated to 80 chars
   │
   └─→ Other tools (bash/read_file/list_dir): tool_panel()
       ↓ render_tool() — results truncated to 200 chars
```

### Relevant Files & Why They Matter

| File | Purpose |
|------|---------|
| `src/tunacode/ui/renderers/panels.py` | Primary truncation logic via `_truncate_value()` at 60/80/200 chars |
| `src/tunacode/ui/renderers/search.py` | Parses glob/grep output into structured `SearchResultData` |
| `src/tunacode/ui/app.py:455-480` | Tool result callback — potential emergency truncation point |
| `src/tunacode/ui/app.py:291-299` | Message handler writes panels to RichLog |
| `src/tunacode/core/agents/agent_components/node_processor.py:82-94` | Extracts tool-return parts from pydantic-ai nodes |
| `src/tunacode/tools/bash.py:206-230` | Bash truncates at 5000 chars with middle cut |
| `src/tunacode/tools/glob.py:329-353` | Glob limits to 5000 files |
| `src/tunacode/tools/grep.py:163-193` | Grep limits to 50 results but NO output size limit |
| `src/tunacode/constants.py` | Defines `MAX_COMMAND_OUTPUT`, `MAX_LINE_LENGTH`, etc. |

### Current Truncation Matrix

| Layer | Component | Limit | Type |
|-------|-----------|-------|------|
| **Tool Output** | bash | 5000 chars | Middle cut with marker |
| **Tool Output** | read_file | 2000 lines | Line count limit |
| **Tool Output** | glob | 5000 files | File count limit |
| **Tool Output** | list_dir | 100 files | File count limit |
| **Tool Output** | grep | 50 results | Result count only (GAP!) |
| **Display** | Arguments | 60 chars | Simple truncate + ellipsis |
| **Display** | Tool results | 200 chars | Simple truncate + ellipsis |
| **Display** | Search snippets | 80 chars | Simple truncate + ellipsis |
| **Display** | Search result count | UNLIMITED | ALL results displayed (GAP!) |

### Architecture Constraints

1. **Immutable Panels**: Once written to RichLog, panels cannot be modified
2. **Rich vs Textual**: System uses Rich renderables, not interactive Textual widgets
3. **Single Write Point**: All panels go through `rich_log.write(panel)` at app.py:300
4. **No Collapsible State**: Panels are static — no expand/collapse functionality
5. **Fixed Truncation**: Original data is lost after truncation at render time

### Existing Truncation Function

```python
# src/tunacode/ui/renderers/panels.py:292-296
def _truncate_value(value: Any, max_length: int = 50) -> str:
    str_value = str(value)
    if len(str_value) <= max_length:
        return str_value
    return str_value[: max_length - 3] + "..."
```

**Limitations:**
- Character-based only (no line awareness)
- No truncation metadata preserved
- No visual indicator of what was cut

## Key Patterns / Solutions Found

### NeXTSTEP Information Hierarchy Applied

Following NeXTSTEP principles, tool result panels should:

```
┌─────────────────────────────────────────────┐
│  PANEL TITLE        │ STATUS │ SOURCE      │  ← Glanceable identity
├─────────────────────────────────────────────┤
│  Primary info (summary/key results)         │  ← User focus
│  - Truncated content with count             │
├─────────────────────────────────────────────┤
│  [Showing 20 of 150 results • 12.3ms]       │  ← Context for "more"
└─────────────────────────────────────────────┘
```

### Three-Tier Truncation Strategy

**Tier 1: Tool Output (Domain-Aware)**
- Tools truncate with domain knowledge (lines vs files vs results)
- Preserve meaningful structure (show first/last, not arbitrary cut)
- Add inline markers: `[truncated at N]`

**Tier 2: Display Layer (Visual Consistency)**
- Uniform character/line limits for panel display
- Truncation with metadata: `"Showing X of Y"`
- Consistent styling across all tool types

**Tier 3: Emergency Layer (Safety Valve)**
- Catch-all at callback layer for uncapped tools
- Prevents message system from handling gigantic strings
- Hard limit: ~50k chars with middle cut

### Recommended Constants

```python
# Add to src/tunacode/constants.py

# Panel Display Limits
MAX_PANEL_LINES = 30           # Lines of content in panel
MAX_PANEL_RESULT_CHARS = 200   # Keep existing
MAX_PANEL_ARG_CHARS = 60       # Keep existing
MAX_PANEL_SNIPPET_CHARS = 80   # Keep existing
MAX_SEARCH_RESULTS_DISPLAY = 20  # Results shown in panel

# Emergency Truncation
MAX_CALLBACK_RESULT_SIZE = 50_000  # 50k char emergency limit
```

### Implementation Approach: Enhanced `_truncate_value()`

```python
def _truncate_content(
    value: str,
    max_chars: int = 200,
    max_lines: int = 30,
) -> tuple[str, int, int]:
    """
    Truncate content with metadata for user awareness.

    Returns: (truncated_text, total_lines, total_chars)
    """
    lines = value.split("\n")
    total_lines = len(lines)
    total_chars = len(value)

    # Line-based truncation takes priority
    if total_lines > max_lines:
        truncated = "\n".join(lines[:max_lines])
        return truncated + f"\n... ({total_lines - max_lines} more lines)", total_lines, total_chars

    # Character-based fallback for long single lines
    if total_chars > max_chars:
        return value[:max_chars - 3] + "...", total_lines, total_chars

    return value, total_lines, total_chars
```

## Knowledge Gaps

1. **User Preference**: Should truncation be configurable via settings?
2. **Full View Access**: How should users access full output? (command? separate panel? file?)
3. **Grep Output Size**: Need to measure actual grep output sizes in production
4. **Performance Impact**: Does storing full results in app state affect memory?

## Implementation Plan

### Phase 1: Emergency Truncation (Safety)

**File:** `src/tunacode/ui/app.py:455-480`

Add emergency truncation in callback before posting message:
```python
def build_tool_result_callback(app: TextualReplApp):
    MAX_RESULT_SIZE = 50_000

    def _callback(..., result: str | None = None, ...):
        if result and len(result) > MAX_RESULT_SIZE:
            half = MAX_RESULT_SIZE // 2
            quarter = MAX_RESULT_SIZE // 4
            result = (
                result[:half]
                + "\n\n... [Result truncated for display] ...\n\n"
                + result[-quarter:]
            )
        # ... rest of callback
```

### Phase 2: Uniform Display Truncation

**File:** `src/tunacode/ui/renderers/panels.py`

1. Replace `_truncate_value()` with `_truncate_content()` that handles multi-line
2. Add truncation metadata to subtitle: `"Showing 30/150 lines"`
3. Update `render_tool()` to use line-based truncation for results
4. Update `render_search_results()` to limit displayed results to 20

### Phase 3: Search Result Limiting

**File:** `src/tunacode/ui/renderers/panels.py:188-250`

Modify `render_search_results()`:
```python
MAX_DISPLAY_RESULTS = 20
displayed = data.results[:MAX_DISPLAY_RESULTS]
hidden = len(data.results) - len(displayed)

# Add to subtitle
if hidden > 0:
    subtitle += f" • +{hidden} more"
```

### Phase 4: Grep Tool Truncation (Optional)

**File:** `src/tunacode/tools/grep.py` or `grep_components/result_formatter.py`

Add output size limit to grep formatted output:
- Max 10,000 chars
- Preserve complete matches (don't cut mid-result)
- Add `[truncated at N matches]` marker

## References

- `src/tunacode/ui/renderers/panels.py` — Panel dataclasses and rendering
- `src/tunacode/ui/renderers/search.py` — Search result parsing
- `src/tunacode/ui/app.py` — Tool result callback and message handler
- `src/tunacode/constants.py` — Existing truncation constants
- `src/tunacode/tools/bash.py:206-230` — Reference for middle-cut truncation
- NeXTSTEP UI Guidelines — Information hierarchy principles
