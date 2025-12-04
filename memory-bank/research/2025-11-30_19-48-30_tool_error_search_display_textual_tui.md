# Research – Tool/Error/Search Agent Display Mapping from Rich REPL to Textual TUI

**Date:** 2025-11-30
**Owner:** claude
**Phase:** Research
**Last Updated:** 2025-11-30
**Tags:** [tui, textual, rich, tools, errors, display, mapping, nextstep]

## Goal

Research and analyze how to map the popular Rich-based tool/error/search agent display from the old TunaCode REPL to the new Textual TUI main container, following NeXTSTEP UI principles for optimal information hierarchy and user experience.

## Additional Search
- `grep -ri "ToolStatusBar\|RichLog\|ToolStatusUpdate" .claude/` → Found existing TUI status mechanisms
- `grep -ri "panels\|console\|markdown" .claude/` → Found Rich display patterns in memory bank

## Findings

### Relevant Files & Why They Matter

#### Current TUI Architecture Files
- `src/tunacode/cli/textual_repl.py` → Main TUI application with RichLog viewport and ResourceBar
- `src/tunacode/cli/widgets.py` → Custom widgets including ToolStatusBar (3 states: active, idle, error)
- `src/tunacode/cli/screens.py` → Modal screens for tool confirmation
- `src/tunacode/cli/textual_repl.tcss` → CSS styling and color definitions
- `src/tunacode/constants.py` → UI_COLORS palette and THEME_NAME

#### Data Structure Files
- `src/tunacode/tools/base.py` → BaseTool class with UI logger interface and tool state
- `src/tunacode/core/state.py` → SessionState with tool history, ReAct data, file context
- `src/tunacode/exceptions.py` → Structured error hierarchy with recovery guidance
- `src/tunacode/types.py` → UILogger protocol for async status updates

#### Memory Bank Documentation
- `.claude/debug_history/2025-10-01_14-28-13_neXSTEP-tui-rebuild.md` → Detailed Rich→Textual migration analysis
- `.claude/patterns/2025-10-15_20-22-07_rich-panel-migration.md` → Rich panel patterns in TUI

## Key Patterns / Solutions Found

### 1. Current TUI Layout (NeXTSTEP-Compliant)
```
┌─────────────────────────────────────────────┐
│ Model │ Tokens │ Cost │ Session             │  ← PERSISTENT STATUS (ResourceBar)
├─────────────────────────────────────────────┤
│                                             │
│           Main conversation/code            │  ← MAXIMUM VIEWPORT (RichLog)
│                                             │
├────────────────┬────────────────────────────┤
│ Context files  │   Input area (Editor)      │  ← COMMAND ZONE
└────────────────┴────────────────────────────┘
```

### 2. Lost Rich Display Patterns
**Old Rich REPL Features (What Made It Popular):**
- **Bordered Panels**: Rich panels with colored borders (blue for responses, red for errors, yellow for tools)
- **Markdown Rendering**: Rich Markdown inside panels for formatted responses
- **Animated Spinners**: Real-time status updates during tool execution
- **Tool Confirmation Panels**: Structured tool execution display with arguments
- **Live Streaming**: Rich Live components for real-time content updates

### 3. Available Textual Equivalents
**Direct Mappings:**
- **Rich Panels → RichLog**: RichLog widget accepts Rich renderables directly
- **Tool Status → ToolStatusBar**: Already implemented with 3 states (active/idle/error)
- **Modal Confirmations → ToolConfirmationModal**: Already implemented
- **Markdown → Rich**: RichLog can render Rich Markdown objects
- **Streaming → RichLog**: Native streaming support with pause/resume

### 4. Data Available for Display
**Tool Execution Data:**
- `BaseTool.tool_name` → Display identification
- `BaseTool._resources` → Resource tracking visualization
- `ToolBuffer.read_only_tasks` → Queue status and task counting
- `SessionState.tool_calls` → Historical tool usage

**Error Information:**
- `ToolExecutionError` with recovery suggestions → Structured error display
- `FileOperationError` with path context → Context-aware error messages
- `suggested_fix` and `recovery_commands` → Actionable error guidance

**Search Agent Data:**
- `SearchResult` with relevance scoring → Ranked result display
- `ResearchAgent.max_files` → Progress tracking
- `SearchConfig` parameters → Search context display

### 5. NeXTSTEP-Based Design Recommendations

**Zone-Based Information Hierarchy:**
```
┌─Model:gpt-4─┬─Tokens:1.2k─┬─Cost:$0.02─┬─Session:active─┐  ← PERSISTENT STATUS
├─────────────────────────────────────────────────────────┤
│                                                         │
│               MAIN CONVERSATION VIEWPORT                │  ← RichLog (maximum space)
│        (Rich panels, markdown, tools, errors)          │
│                                                         │
├─────────────┬───────────────────┬───────────────────────┤
│ Context: 3f │ Tool: bash ● idle │ Search: 42 results    │  ← SPATIAL/SELECTION/ACTIONS
│ files.py    │                   │ grep: "pattern"       │
├─────────────┴───────────────────┴───────────────────────┤
│ > Enter command...                                       │  ← INPUT ZONE
└─────────────────────────────────────────────────────────┘
```

**Key Design Principles:**
1. **Persistent Status Bar** → Already implemented (ResourceBar)
2. **Maximum Viewport** → RichLog with Rich renderables for panels
3. **Context Zones** → Extend current context panel with tool/search status
4. **Consistent Input** → Keep Editor at bottom (CLI convention)
5. **Visual Feedback** → Use ToolStatusBar states and Rich styling

## Knowledge Gaps

### Missing Context for Next Phase
1. **Rich Panel Implementation**: Need to experiment with Rich panel rendering in RichLog widget
2. **Performance Impact**: Rich panel streaming vs. plain text performance unknown
3. **Color Consistency**: Need to map old Rich color schemes to Textual CSS themes
4. **Modal Timing**: When to show tool confirmations vs. inline status
5. **Error Recovery Flow**: How to present actionable recovery options in TUI
6. **Search Result Pagination**: Large result sets need pagination/scrolling strategy
7. **Tool Animation**: Equivalent of Rich spinners for long-running operations

### Implementation Details Needed
1. **Rich Object Creation**: How to convert tool/error data into Rich panels
2. **CSS Integration**: Rich panel styling vs. Textual CSS coordination
3. **Async Updates**: Tool status updates during execution in RichLog
4. **User Interaction**: Clickable elements in Rich panels for actions
5. **Memory Management**: Large conversation history with rich objects

## References

### Files for Full Review
- `src/tunacode/cli/textual_repl.py:78-156` → Main TUI app structure and RichLog usage
- `src/tunacode/cli/widgets.py:45-89` → ToolStatusBar implementation patterns
- `.claude/debug_history/2025-10-01_14-28-13_neXSTEP-tui-rebuild.md` → Complete migration analysis
- `src/tunacode/core/state.py:89-134` → SessionState tool tracking data
- `src/tunacode/exceptions.py:23-67` → Structured error data with recovery

### GitHub Permalents
- Current TUI implementation: https://github.com/tunacode/tunacode/blob/textual_repl/src/tunacode/cli/textual_repl.py
- Widget definitions: https://github.com/tunacode/tunacode/blob/textual_repl/src/tunacode/cli/widgets.py
- Tool status handling: https://github.com/tunacode/tunacode/blob/textual_repl/src/tunacode/core/state.py

### Related Memory Bank Entries
- `.claude/patterns/2025-10-15_20-22-07_rich-panel-migration.md` → Rich panel patterns
- `.claude/qa/2025-10-01_15-45-22_textual-display-strategy.md` → Display approach Q&A
- `.claude/delta_summaries/2025-10-01_14-28-13_tui-rebuild-summary.md` → Migration decisions

---

## Next Steps Recommendations

1. **Prototype Rich Panel Rendering**: Create test panels in RichLog to verify Rich→Textual compatibility
2. **Extend ToolStatusBar**: Add detailed tool status with progress indicators
3. **Implement Error Panels**: Structured error display with recovery options
4. **Add Search Result Zone**: Dedicated area for search results with pagination
5. **Create Tool Animation**: Spinners or progress bars for long operations
6. **User Testing**: Validate information hierarchy and visual feedback effectiveness

The research indicates that the Rich→Textual migration is architecturally sound, with RichLog providing the key bridge for maintaining the visual richness that made TunaCode popular while gaining Textual's reactive benefits.
