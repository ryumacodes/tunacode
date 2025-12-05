# Research – Bash Mode UI Visual Indicator

**Date:** 2025-12-04
**Owner:** Claude (context-engineer:research)
**Phase:** Research
**Git Commit:** 1abdc05d00e914c79ed9e1e3c374c9520899c134

## Goal

Research how to add visual feedback when a user types `!` as the first character in the Editor input, indicating they are entering "bash mode" for shell command execution.

## Findings

### Current Implementation

The `!` bash mode is implemented but lacks real-time visual feedback:

**Detection Logic:**
- `src/tunacode/ui/commands/__init__.py:200-202` - Checks for `!` prefix
  ```python
  if text.startswith("!"):
      await run_shell_command(app, text[1:])
      return True
  ```
- Detection happens AFTER submission, not during typing

**Input Flow:**
- `src/tunacode/ui/widgets/editor.py:12` - `Editor(Input)` widget captures user input
- `src/tunacode/ui/widgets/editor.py:36-42` - `action_submit()` posts message on Enter
- `src/tunacode/ui/app.py:211-217` - `on_editor_submit_requested()` routes to command handler
- No real-time prefix detection exists currently

**Shell Execution:**
- `src/tunacode/ui/commands/__init__.py:223-249` - `run_shell_command()` function
- Uses `subprocess.run()` with `shell=True`
- 30-second timeout
- Output displayed in `app.rich_log`

### Relevant Files & Why They Matter

| File | Purpose |
|------|---------|
| `src/tunacode/ui/widgets/editor.py` | Editor widget where text change watching should be added |
| `src/tunacode/ui/app.tcss` | CSS styles where bash-mode class should be defined |
| `src/tunacode/ui/commands/__init__.py` | Current ! detection logic (for reference) |
| `src/tunacode/constants.py:108-122` | UI_COLORS palette for consistent theming |

### Existing Visual Feedback Patterns

The codebase already implements mode-based visual feedback via CSS classes:

1. **RichLog States** (`app.tcss:28-44`):
   - `.streaming` → Border: `$accent` (magenta)
   - `.paused` → Border: `$warning` (yellow/lime)

2. **Tool Panel States** (`app.tcss:221-239`):
   - `.running` → Border: `$accent`
   - `.completed` → Border: `$success` (green)
   - `.failed` → Border: `$error` (red)

3. **Color Semantic Meanings** (`constants.py`):
   - `$warning` (#c3e88d) = caution/special mode (yellow/lime)
   - `$primary` (#00d7d7) = identity/command (cyan)
   - `$accent` (#ff6b9d) = active/attention (magenta)

### Editor Widget Current Structure

```python
# src/tunacode/ui/widgets/editor.py
class Editor(Input):
    BINDINGS = [Binding("enter", "submit", show=False)]

    def __init__(self):
        super().__init__(placeholder="we await...")

    def on_key(self, event: events.Key) -> None:
        # Currently only handles confirmation key interception
        ...

    def action_submit(self) -> None:
        text = self.value.strip()
        if not text:
            return
        self.post_message(EditorSubmitRequested(text=text, raw_text=self.value))
        self.value = ""
```

## Key Patterns / Solutions Found

### Pattern 1: CSS Class Toggle (Recommended)

Add CSS class to Editor based on input prefix:

**CSS Addition** (`app.tcss`):
```css
Editor.bash-mode {
    border: solid $warning;  /* Yellow/lime for shell mode */
}

Editor.command-mode {
    border: solid $primary;  /* Cyan for / commands */
}
```

**Editor Modification** (`editor.py`):
```python
def watch_value(self, value: str) -> None:
    """React to text changes in real-time."""
    self.remove_class("bash-mode", "command-mode")
    if value.startswith("!"):
        self.add_class("bash-mode")
    elif value.startswith("/"):
        self.add_class("command-mode")
```

### Pattern 2: Dynamic Placeholder

Change placeholder text based on mode:
```python
def watch_value(self, value: str) -> None:
    if value.startswith("!"):
        self.placeholder = "shell command..."
    elif value.startswith("/"):
        self.placeholder = "command..."
    else:
        self.placeholder = "we await..."
```

### Pattern 3: Prefix Label Widget

Add a visual label showing current mode:
- Normal: `>`
- Bash: `!` (yellow)
- Command: `/` (cyan)

## Implementation Recommendation

**Approach: CSS Class Toggle with Border Change**

This approach:
1. Follows existing patterns in the codebase (RichLog states use same technique)
2. Provides immediate visual feedback (border color change)
3. Is non-intrusive (doesn't require layout changes)
4. Works with both default and NeXTSTEP themes

**Files to Modify:**
1. `src/tunacode/ui/widgets/editor.py` - Add `watch_value()` method
2. `src/tunacode/ui/app.tcss` - Add `.bash-mode` and optionally `.command-mode` styles

**Estimated Changes:**
- ~5 lines in `editor.py`
- ~8 lines in `app.tcss`

## Knowledge Gaps

- Should `/` command mode also get visual feedback? (Consistency argument)
- Should there be a text indicator in addition to border color? (Accessibility)
- NeXTSTEP theme override needed? (Currently uses different border colors)

## References

- `src/tunacode/ui/widgets/editor.py` - Editor widget implementation
- `src/tunacode/ui/app.tcss:94-103` - Current Editor styling
- `src/tunacode/ui/app.tcss:36-44` - RichLog state classes (pattern reference)
- `src/tunacode/ui/commands/__init__.py:195-220` - Current command handling
- `src/tunacode/constants.py:108-122` - UI_COLORS palette
