# Research - Input Text Wrapping and Proper UI

**Date:** 2025-12-17
**Owner:** agent
**Phase:** Research

## Goal

Map out the current input implementation, understand paste line functionality, and research proper Textual text input patterns to enable text wrapping for user input.

## Problem Statement

Users currently type in one long horizontal line because the `Editor` widget extends Textual's `Input` class, which is strictly single-line. Multi-line pastes are handled separately via a "paste line" system that stores content invisibly and shows a placeholder.

---

## Findings

### Current Implementation Architecture

| File | Purpose |
|------|---------|
| `src/tunacode/ui/widgets/editor.py` | Main input widget (extends `Input`) |
| `src/tunacode/ui/widgets/messages.py` | `EditorSubmitRequested` message definition |
| `src/tunacode/ui/widgets/status_bar.py` | Mode indicators (paste mode, bash mode) |
| `src/tunacode/ui/app.py:333` | Submission handler with collapse logic |
| `src/tunacode/ui/app.tcss:85-98` | Editor CSS styling |

### Current Editor Widget (`editor.py`)

```python
class Editor(Input):  # Single-line only!
    """Single-line editor with Enter to submit."""

    BINDINGS = [Binding("enter", "submit", "Submit", show=False)]

    def __init__(self) -> None:
        super().__init__(placeholder="we await...")
        self._was_pasted: bool = False
        self._pasted_content: str = ""
```

**Key limitation:** Inherits from `Input` which is architecturally single-line.

### Paste Line System (Must Preserve)

The paste handling intercepts multi-line pastes before the parent `Input` truncates them:

```python
def _on_paste(self, event: events.Paste) -> None:
    lines = event.text.splitlines()
    if len(lines) > 1:
        self._was_pasted = True
        self._pasted_content = event.text  # Store full content
        self.value = f"[[PASTED {len(lines)} LINES]]"  # Show indicator
        status_bar.set_mode(f"pasted {len(lines)} lines")
        event.stop()
```

**This system must be preserved** - it handles large pastes gracefully by:
1. Storing full content in `_pasted_content`
2. Displaying line count indicator `[[PASTED N LINES]]`
3. Updating status bar with paste mode
4. Collapsing display in RichLog for pastes > 10 lines

### Textual Widget Comparison

| Feature | Input | TextArea |
|---------|-------|----------|
| Lines | Single only | Multi-line |
| Soft-wrap | N/A | Yes (default) |
| Line numbers | No | Yes (optional) |
| Syntax highlighting | No | Yes (tree-sitter) |
| Undo/redo | Limited | Full system |
| Tab behavior | Focus next | Configurable |
| Validation | Built-in | Manual |

### Proper Multi-line Input: TextArea Widget

Textual's `TextArea` widget provides proper multi-line editing:

```python
from textual.widgets import TextArea

class Editor(TextArea):  # Multi-line capable
    def __init__(self):
        super().__init__(
            soft_wrap=True,      # Text wraps visually
            show_line_numbers=False,
            tab_behavior="focus",  # Tab moves to next widget
        )
```

**TextArea advantages:**
- Soft-wrap flows text across multiple visual rows
- Cursor navigation works naturally across wrapped lines
- Selection spans multiple lines properly
- Performance optimized (incremental tree-sitter parsing)

---

## Key Patterns / Solutions Found

### Pattern 1: TextArea for Multi-line, Input for Single-line
Official Textual guidance is clear - use `TextArea` when users need to enter/edit multiple lines or when text should wrap visually.

### Pattern 2: Tab Behavior Configuration
```python
tab_behavior="focus"   # Tab moves to next widget (form-like)
tab_behavior="indent"  # Tab inserts tab character (code editor)
```

### Pattern 3: Clipboard Handling
- Multi-character pastes automatically get isolated undo batches in TextArea
- System clipboard access via `pyperclip` with graceful fallback
- OSC 52 terminal-based clipboard for SSH scenarios

### Pattern 4: CSS Sizing for Text Wrapping
```css
TextArea {
    width: 100%;
    height: auto;  /* Or fixed height with scrolling */
}
```

---

## Design Considerations for Migration

### Must Preserve
1. **Paste line indicator** - `[[PASTED N LINES]]` for large pastes
2. **Status bar integration** - paste mode, bash mode indicators
3. **Bash mode** - `!` prefix detection and visual feedback
4. **Autocomplete integration** - `@file` and `/command` systems
5. **Enter to submit** - current binding behavior

### Migration Challenges

| Challenge | Notes |
|-----------|-------|
| Autocomplete | `textual_autocomplete` targets `Input`, may need adapter |
| Enter behavior | TextArea default: new line. Need override for submit |
| Bash mode CSS | Class `bash-mode` styling needs TextArea selector |
| Height management | Dynamic height vs fixed with scroll |
| Paste detection | TextArea may handle pastes differently |

### Possible Architecture

```
Option A: Hybrid Approach
- Keep Input for simple messages
- Switch to TextArea when multi-line detected
- Complex state management

Option B: Full TextArea Migration
- Replace Editor(Input) with Editor(TextArea)
- Override Enter binding to submit
- Adapt autocomplete layer
- Simpler long-term maintenance

Option C: Custom Compound Widget
- Container with TextArea + custom chrome
- Explicit height/scroll management
- Maximum control, most work
```

---

## Knowledge Gaps

- How does `textual_autocomplete` behave with `TextArea` targets?
- What is the performance impact of TextArea for short single-line inputs?
- How to distinguish "Enter to submit" vs "Enter for newline" UX?
  - Shift+Enter for newline is common pattern
  - Or only allow multi-line via paste (current behavior preserved)

---

## References

### Codebase Files
- `src/tunacode/ui/widgets/editor.py` - Current implementation
- `src/tunacode/ui/widgets/messages.py` - Message definitions
- `src/tunacode/ui/app.py:333-356` - Submit handler with collapse
- `src/tunacode/ui/app.tcss:85-98` - Editor styling

### External Documentation
- [Textual TextArea Widget](https://textual.textualize.io/widgets/text_area/)
- [Textual Input Widget](https://textual.textualize.io/widgets/input/)
- [TextArea Development Blog](https://textual.textualize.io/blog/2023/09/18/things-i-learned-while-building-textuals-textarea/)

---

## Summary

The current `Editor` widget uses `Input` which is single-line only, causing the "one long line" problem. Textual provides `TextArea` specifically for multi-line input with proper soft-wrapping.

The existing **paste line system must be preserved** as it gracefully handles large pastes. A migration to `TextArea` would require:
1. Overriding Enter to submit (not newline)
2. Adapting autocomplete integration
3. Preserving bash mode visual feedback
4. Maintaining paste detection/collapse logic

The recommended investigation path is Option B (full TextArea migration) with Enter-to-submit and Shift+Enter-for-newline behavior.
