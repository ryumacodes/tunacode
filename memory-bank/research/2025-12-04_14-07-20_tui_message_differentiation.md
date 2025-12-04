# Research – TUI Message Visual Differentiation
**Date:** 2025-12-04
**Owner:** Research Agent
**Phase:** Research
**git_commit:** 0efa9ddeabff820265a073db641bc31e48ce604e

## Goal
Analyze the current TUI implementation to understand how user and agent responses are displayed, and identify opportunities to improve visual differentiation between message types.

## Additional Search
- `grep -ri "user.*message\|assistant.*response\|rich_log\|markdown" src/tunacode/ui/ --include="*.py"`

## Findings

### Relevant files & why they matter:
- `src/tunacode/ui/app.py` → Main TUI app containing message display logic (lines 154-179)
- `src/tunacode/constants.py` → UI color scheme and styling definitions (lines 110-124)
- `src/tunacode/ui/renderers/panels.py` → Tool result panel rendering with status-based styling
- `src/tunacode/ui/widgets/editor.py` → User input widget and message submission
- `src/tunacode/ui/app.tcss` → CSS styles for UI components including RichLog

## Key Patterns / Solutions Found

### Current Message Display Implementation

1. **User Messages** (src/tunacode/ui/app.py:176-179):
   - Styled with cyan color (`style="cyan"`)
   - Prefixed with pipe character `│`
   - Include timestamp in dim cyan
   - Format: `│ {message}\n│ tc {timestamp}`

2. **Assistant Responses** (src/tunacode/ui/app.py:154-155):
   - No visual differentiation - rendered as raw Markdown
   - No prefix, border, or special styling
   - Simply written to RichLog as `Markdown(self.current_stream_text)`

3. **Tool Results**:
   - Rendered in bordered panels with status-dependent colors
   - Status colors: running (magenta), completed (green), failed (red)
   - Clear visual separation through panel borders

### Visual Hierarchy Issues

1. **No Clear Separation**:
   - Assistant messages flow directly after user messages without visual break
   - No avatars, icons, or speaker indicators
   - No conversation threading

2. **Inconsistent Styling**:
   - User messages: cyan with pipe prefix
   - Assistant messages: default text styling
   - Tool results: bordered panels
   - No unified visual language

3. **Spacing Gaps**:
   - No explicit separators between message types
   - No vertical spacing to distinguish speakers
   - No background color differences

### Available UI Elements

From `constants.py`, the color palette includes:
- Background: #1a1a1a (near black)
- Surface: #252525 (panels)
- Border: #ff6b9d (magenta)
- Text: #e0e0e0 (light gray)
- Primary: #00d7d7 (cyan)
- Accent: #ff6b9d (magenta)
- Success: #4ec9b0 (green)
- Warning: #c3e88d (yellow/lime)
- Error: #f44747 (red)

## Knowledge Gaps

- User preferences for message differentiation (avatars vs borders vs spacing)
- Accessibility requirements for color contrast
- Performance implications of additional rendering elements
- How streaming affects visual consistency
- Whether message history persistence needs visual cues

## References

### Key Implementation Files
- `src/tunacode/ui/app.py` - Main message display logic
- `src/tunacode/constants.py` - Color definitions (lines 110-124)
- `src/tunacode/ui/renderers/panels.py` - Panel rendering patterns
- `src/tunacode/ui/app.tcss` - CSS styling rules

### Critical Code Sections
- User message formatting: `src/tunacode/ui/app.py:176-179`
- Assistant response rendering: `src/tunacode/ui/app.py:154-155`
- Streaming callback: handles real-time message accumulation
- RichLog widget: main conversation display area

### Potential Solutions to Explore
1. Add visual prefixes for assistant messages (e.g., "│" with different styling)
2. Implement subtle borders or background colors for assistant responses
3. Add message type indicators or avatars
4. Use Rich panels for assistant messages (similar to tool results)
5. Implement visual separators between message turns
6. Add timestamp formatting for assistant responses