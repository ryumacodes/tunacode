# Research – Edit Tool Diff Display Enhancement

**Date:** 2025-12-06
**Owner:** Claude Code Assistant
**Phase:** Research
**Tags:** [diff-display, ui-enhancement, nextstep-ui, file-editing]

## Goal
Research and understand why the edit tool (update_file) doesn't show diffs and appears "blon" (blank/bland), then apply NeXTSTEP UI principles to design a solution that provides clear visual feedback for file edits.

## Initial Context
The user reported that the edit tool doesn't show a diff of edits - they appear too plain and don't provide proper visual feedback about what changed in the files.

## Findings

### Current Implementation
- The edit functionality is implemented as `update_file` tool in `/src/tunacode/tools/update_file.py`
- It performs simple text replacement using fuzzy matching from `/src/tunacode/tools/utils/text_match.py`
- Returns only a success message: `"File '{filepath}' updated successfully."`
- No diff generation or visualization exists

### Relevant Files & Components
- `/src/tunacode/tools/update_file.py` – Main edit tool implementation
- `/src/tunacode/tools/utils/text_match.py` – Fuzzy string replacement with multiple strategies
- `/src/tunacode/ui/renderers/panels.py` – Tool output display (lines 100-154, 424-438)
- `/src/tunacode/ui/components/tool_panel.py` – Native Textual widget for tool display
- `/src/tunacode/ui/widgets/messages.py` – Message classes including `ToolResultDisplay`
- `/src/tunacore/core/agents/agent_components/tool_executor.py` – Tool execution with retry logic

### Data Flow
1. Agent calls `update_file(filepath, target, patch)`
2. Tool reads entire file content
3. Uses `text_match.replace()` with multiple fallback strategies
4. Writes modified content back
5. Returns simple success string
6. UI displays basic panel with success message only

## Key Issues Identified

### 1. No Visual Feedback (Violates NeXTSTEP Principle)
- **Problem**: Users can't see what changed
- **NeXTSTEP Violation**: "Visual feedback - Users must always see result of their action"
- The tool acts invisibly, leaving users uncertain about what was modified

### 2. Information Hierarchy Breakdown
- **Current Layout**: Just a success message at bottom of output
- **NeXTSTEP Ideal**: Should follow information hierarchy with clear zones
- Missing: Primary viewport showing the diff, context about what changed

### 3. Violates Direct Manipulation Principle
- **Problem**: Edit happens without user seeing the transformation
- **NeXTSTEM Guideline**: Objects should respond directly to actions
- Users should see the before/after state transition

## NeXTSTEP UI Analysis

### Information Hierarchy Requirements
```
┌─────────────────────────────────────────────────┐
│  STATUS: File updated ── FilePath: src/file.py  │  ← Persistent Status
├─────────────────────────────────────────────────┤
│                                                 │
│              DIFF VIEWPORT                      │  ← Primary Viewport
│  ┌─ src/file.py ─────────────────────────────┐  │  Maximum real estate
│  │ @@ -10,7 +10,7 @@                         │  │
│  │  old line                                 │  │  User focus here
│  │ +new line                                 │  │
│  └───────────────────────────────────────────┘  │
│                                                 │
├─────────────────────────────────────────────────┤
│  Context: 1 insertion, 2 deletions              │  ← Selection Context
├─────────────────────────────────────────────────┤
│  [Accept] [Revert] [View Full File]             │  ← Available Actions
└─────────────────────────────────────────────────┘
```

### Design Principles to Apply

1. **Consistency**: Diff format should match standard diff visualization
2. **User Control**: Provide options to accept/revert changes
3. **Naturalness**: Diff colors and indicators should behave as expected
4. **Acting for User**: When showing diff, make it identical to what actually changed

## Proposed Solution Architecture

### 1. Enhance update_file Tool
- Generate diff before/after replacement
- Return structured data including:
  - Success status
  - Original content
  - Modified content
  - Generated diff
  - Change statistics

### 2. Create Diff Renderer Component
- New renderer: `/src/tunacode/ui/renderers/diff.py`
- Display diffs with unified format
- Use colors: red for removals, green for additions
- Handle line numbers and context lines

### 3. Update Tool Panel Display
- Modify `panels.py` to detect diff results
- Show diff in primary viewport when available
- Maintain backward compatibility for simple results

### 4. Add Diff-Specific Message Type
- Extend `messages.py` with `DiffResultDisplay`
- Allows specialized handling of diff display
- Can include additional metadata (file path, change counts)

## Implementation Considerations

### 1. Diff Generation Strategy
```python
# Use Python's difflib for unified diff generation
import difflib

def generate_unified_diff(original: str, modified: str, filepath: str) -> str:
    lines_original = original.splitlines(keepends=True)
    lines_modified = modified.splitlines(keepends=True)
    return ''.join(difflib.unified_diff(
        lines_original,
        lines_modified,
        fromfile=f"a/{filepath}",
        tofile=f"b/{filepath}",
        lineterm=""
    ))
```

### 2. UI Integration Points
- `update_file.py`: Add diff generation before writing
- `panels.py`: Check for diff in result and render accordingly
- `tool_panel.py`: Support diff-specific styling
- CSS variables for diff colors to maintain consistency

### 3. Performance Considerations
- Only generate diff for files under configurable size limit
- Lazy rendering for large diffs
- Option to truncate diff with "show more" functionality

## Knowledge Gaps
1. Exact TUI capabilities for colored diff rendering in Textual
2. Performance impact of diff generation on large files
3. Whether to use unified or context diff format
4. How to handle binary files or encoding issues

## References
- `/src/tunacode/tools/update_file.py:11-52` – Current update logic
- `/src/tunacode/ui/renderers/panels.py:100-154` – Current tool display
- `/src/tunacode/tools/utils/text_match.py:274-339` – Text matching strategies
- NeXTSTEP UI Guidelines – Visual feedback and information hierarchy principles
- `difflib.unified_diff` – Python standard library for diff generation

## Additional Search Terms for Implementation
- `grep -ri "diff" .claude/`
- `grep -ri "color.*render" src/tunacode/ui/`
- `grep -ri "unified.*diff" .`

## Next Steps
1. Implement diff generation in update_file tool
2. Create diff renderer with TUI support
3. Update tool panel to display diffs prominently
4. Add user controls for accepting/reverting changes
5. Test with various file types and sizes
