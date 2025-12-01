---
title: "Textual TUI Tool/Error/Search Display Implementation Plan"
phase: Plan
date: "2025-11-30 20:00:00"
owner: "claude"
parent_research: "memory-bank/research/2025-11-30_19-48-30_tool_error_search_display_textual_tui.md"
git_commit_at_plan: "cd157b2"
tags: [plan, textual, tui, tools, errors, display, nextstep]
---

## Goal

Implement Rich panel-based tool, error, and search agent display mapping in the Textual TUI while maintaining NeXTSTEP UI principles and the visual richness that made TunaCode popular. **SINGULAR FOCUS: Create Rich panel rendering system in RichLog that bridges Rich REPL patterns to Textual TUI architecture.**

## Scope & Assumptions

### In Scope
- Rich panel rendering in RichLog widget for tools, errors, and search results
- ToolStatusBar enhancement with detailed progress indicators
- Error panel system with actionable recovery options
- Search result display with pagination
- Color consistency with existing Textual CSS theme
- Performance optimization for Rich object streaming

### Out of Scope
- Complete TUI architecture rebuild (already done)
- New widget creation (use existing RichLog infrastructure)
- Multi-line input improvements (separate concern)
- Session management features (already implemented)
- Terminal compatibility enhancements

### Assumptions
- RichLog widget accepts Rich renderables directly (confirmed in research)
- BaseTool and SessionState data structures are stable
- CSS theme system is functional in current TUI
- No TDD required (test suite being rebuilt)
- User wants visual richness maintained from Rich REPL

### Drift Detected
**Note:** Significant documentation deletion detected in git status. This may affect reference materials but core implementation files appear intact. Re-verification of data structures recommended during implementation.

## Deliverables (DoD)

1. **Rich Panel Renderer** (`src/tunacode/cli/rich_panels.py`)
   - Accept Rich renderables for tools, errors, search results
   - Map old Rich color schemes to Textual CSS
   - Handle streaming vs. complete rendering
   - Performance benchmarking for large conversations

2. **Enhanced ToolStatusBar** (`src/tunacode/cli/widgets.py`)
   - Detailed tool status with progress indicators
   - Animated status updates during execution
   - Resource usage visualization
   - Tool queue status display

3. **Error Panel System** (`src/tunacode/cli/error_panels.py`)
   - Structured error display with recovery options
   - Clickable recovery commands
   - Error severity color coding
   - Context-aware error messages

4. **Search Result Display** (`src/tunacode/cli/search_display.py`)
   - Paginated search results with relevance scoring
   - Interactive result selection
   - Search context highlighting
   - Result count and progress indicators

5. **CSS Theme Extensions** (`src/tunacode/cli/textual_repl.tcss`)
   - Rich panel styling rules
   - Color scheme consistency
   - Animation definitions for tool status
   - Responsive layout adjustments

## Readiness (DoR)

### Preconditions
- Textual TUI implementation verified functional
- RichLog widget accepts Rich renderables
- BaseTool data structures accessible
- CSS theme system operational
- Git worktree clean for implementation branch

### Environment Requirements
- Python 3.13+ with Textual framework
- Rich library for panel rendering
- Working TUI application with RichLog widget
- Access to tool execution data (SessionState, BaseTool)

### Dependencies
- No new core dependencies (use existing Rich and Textual)
- Possible CSS preprocessing utilities if needed
- Performance profiling tools for optimization validation

## Milestones

### M1: Architecture & Skeleton (Day 1)
- Rich panel renderer foundation
- Data structure mapping from tools/errors/search to Rich panels
- CSS integration framework
- Performance testing baseline

### M2: Core Feature Implementation (Day 2-3)
- Tool execution panel rendering
- Error panel with recovery options
- Search result pagination system
- Real-time status updates

### M3: Visual Polish & Integration (Day 4)
- Color scheme consistency
- Animation and status indicators
- NeXTSTEP zoning compliance
- Performance optimization

### M4: Testing & Validation (Day 5)
- Manual testing with various tool/error scenarios
- Performance validation with large conversations
- UX validation for information hierarchy
- Documentation updates

## Work Breakdown (Tasks)

### Task T1.1: Rich Panel Renderer Foundation
**Owner:** claude
**Estimate:** 4 hours
**Dependencies:** None
**Target Milestone:** M1

**Acceptance Tests:**
- RichPanelRenderer class accepts tool data and returns Rich Panel
- Basic color mapping implemented
- Integration with RichLog verified
- Performance baseline established (< 50ms render time)

**Files/Interfaces Touched:**
- `src/tunacode/cli/rich_panels.py` (new)
- `src/tunacode/cli/textual_repl.py` (integration)
- `src/tunacode/tools/base.py` (data access)

### Task T1.2: Data Structure Mapping
**Owner:** claude
**Estimate:** 3 hours
**Dependencies:** T1.1
**Target Milestone:** M1

**Acceptance Tests:**
- BaseTool tool_name, resources mapped to panel fields
- ToolBuffer read_only_tasks visualized in status
- SessionState tool_calls historical data accessible
- Error exception data with recovery suggestions mapped

**Files/Interfaces Touched:**
- `src/tunacode/cli/rich_panels.py`
- `src/tunacode/core/state.py`
- `src/tunacode/exceptions.py`
- `src/tunacode/types.py`

### Task T2.1: Tool Execution Panel Implementation
**Owner:** claude
**Estimate:** 6 hours
**Dependencies:** T1.1, T1.2
**Target Milestone:** M2

**Acceptance Tests:**
- Live tool status during execution
- Tool arguments displayed clearly
- Resource usage visualization
- Streaming vs. completed render modes

**Files/Interfaces Touched:**
- `src/tunacode/cli/rich_panels.py`
- `src/tunacode/cli/widgets.py` (ToolStatusBar integration)
- `src/tunacode/core/state.py`

### Task T2.2: Error Panel System
**Owner:** claude
**Estimate:** 5 hours
**Dependencies:** T1.1, T1.2
**Target Milestone:** M2

**Acceptance Tests:**
- Structured error display with context
- Recovery options as clickable elements
- Error severity color coding
- File operation error path context

**Files/Interfaces Touched:**
- `src/tunacode/cli/error_panels.py` (new)
- `src/tunacode/exceptions.py`
- `src/tunacode/cli/rich_panels.py`

### Task T2.3: Search Result Display
**Owner:** claude
**Estimate:** 5 hours
**Dependencies:** T1.1, T1.2
**Target Milestone:** M2

**Acceptance Tests:**
- Paginated result display
- Relevance scoring visualization
- Interactive result selection
- Search context highlighting

**Files/Interfaces Touched:**
- `src/tunacode/cli/search_display.py` (new)
- `src/tunacode/cli/rich_panels.py`
- Search agent data structures

### Task T3.1: CSS Theme Extensions
**Owner:** claude
**Estimate:** 4 hours
**Dependencies:** T2.1, T2.2, T2.3
**Target Milestone:** M3

**Acceptance Tests:**
- Rich panel styling consistent across components
- Color scheme mapping from old Rich themes
- Animation definitions for tool status
- Responsive layout for different screen sizes

**Files/Interfaces Touched:**
- `src/tunacode/cli/textual_repl.tcss`
- `src/tunacode/constants.py` (UI_COLORS)

### Task T3.2: NeXTSTEP Zoning Compliance
**Owner:** claude
**Estimate:** 3 hours
**Dependencies:** T3.1
**Target Milestone:** M3

**Acceptance Tests:**
- Persistent status bar (ResourceBar) unchanged
- Maximum viewport (RichLog) with Rich panels
- Context zones with tool/search status
- Consistent input zone at bottom

**Files/Interfaces Touched:**
- `src/tunacode/cli/textual_repl.py`
- `src/tunacode/cli/widgets.py`

### Task T4.1: Performance Validation
**Owner:** claude
**Estimate:** 3 hours
**Dependencies:** T3.2
**Target Milestone:** M4

**Acceptance Tests:**
- Large conversation history performance (< 100ms response)
- Rich object memory usage within bounds
- Streaming performance during tool execution
- No UI freezing during heavy rendering

**Files/Interfaces Touched:**
- Performance benchmarks
- Memory profiling results
- Optimization adjustments

## Risks & Mitigations

### Risk 1: Rich Panel Performance Impact
**Impact:** High - could make TUI unusable with large conversations
**Likelihood:** Medium - Rich objects are memory intensive
**Mitigation:** Implement lazy loading, pagination, and object pooling
**Trigger:** Performance tests show > 200ms render times

### Risk 2: Color Scheme Inconsistency
**Impact:** Medium - visual disruption for users
**Likelihood:** Low - research shows direct mapping available
**Mitigation:** Create comprehensive color mapping table from old Rich themes
**Trigger:** Visual testing reveals color mismatches

### Risk 3: CSS Integration Conflicts
**Impact:** Medium - styling conflicts between Rich and Textual
**Likelihood:** Medium - two styling systems interacting
**Mitigation:** Isolate Rich panel styling, use CSS specificity strategically
**Trigger:** Rich panels not rendering with expected styles

### Risk 4: User Interaction Complexity
**Impact:** Low - confusing interface reduces adoption
**Likelihood:** Low - following established NeXTSTEP patterns
**Mitigation:** Strict adherence to NeXTSTEP zoning principles
**Trigger:** User testing shows confusion with new panels

## Test Strategy

**At most ONE new test** as specified - focus on integration validation:

- **Rich Panel Integration Test:** Single comprehensive test verifying Rich panel rendering in RichLog with tool, error, and search data, including performance benchmarks and visual validation.

## References

### Research Document Sections
- Rich→Textual migration analysis (research doc lines 21-38)
- Current TUI layout (research doc lines 40-52)
- Available Textual equivalents (research doc lines 62-68)
- NeXTSTEP design recommendations (research doc lines 86-110)

### Key Files for Implementation
- `src/tunacode/cli/textual_repl.py:78-156` - Main TUI app structure
- `src/tunacode/cli/widgets.py:45-89` - ToolStatusBar patterns
- `src/tunacode/core/state.py:89-134` - SessionState tool tracking
- `src/tunacode/exceptions.py:23-67` - Structured error data
- `src/tunacode/tools/base.py` - BaseTool with UI logger interface

### Memory Bank Entries
- `.claude/debug_history/2025-10-01_14-28-13_neXSTEP-tui-rebuild.md` - Complete migration analysis
- `.claude/patterns/2025-10-15_20-22-07_rich-panel-migration.md` - Rich panel patterns
- `.claude/qa/2025-10-01_15-45-22_textual-display-strategy.md` - Display approach decisions

## Agents

Deploy maximum 3 subagents for parallel execution:

1. **context-synthesis subagent** - Analyze recent code changes and validate data structures
2. **codebase-analyzer subagent** - Deep dive into current TUI widget implementations and RichLog integration
3. **seams-documenter subagent** - Document the new rich panel architecture for future developers

## Final Gate

**Plan Summary:**
- **Path:** `memory-bank/plan/2025-11-30_20-00-00_textual_tui_tool_error_search_display.md`
- **Milestones:** 4 (Architecture → Core Features → Polish → Validation)
- **Gates:** Performance validation, NeXTSTEP compliance, visual consistency
- **Duration:** 5 days focused implementation

**Next Command:** `/execute "/home/tuna/tunacode/memory-bank/plan/2025-11-30_20-00-00_textual_tui_tool_error_search_display.md"`

**Success Criteria:** Rich panels render seamlessly in Textual TUI while maintaining the visual richness and performance that made TunaCode's Rich REPL popular, following NeXTSTEP UI principles for optimal user experience.