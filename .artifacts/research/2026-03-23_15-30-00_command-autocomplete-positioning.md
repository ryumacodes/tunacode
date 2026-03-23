---
title: "Command autocomplete dropdown positioning research"
link: "command-autocomplete-positioning-research"
type: research
ontological_relations:
  - relates_to: [[ui-layout, editor-widget, textual-autocomplete]]
tags: [research, ui, autocomplete, positioning]
uuid: "cmd-pos-2026-03-23"
created_at: "2026-03-23T15:30:00Z"
---

## Issue Summary
The "/" command autocomplete dropdown in the TunaCode UI appears positioned too low, causing it to be partially cut off at the bottom of the terminal window. Users can only see the dropdown halfway when typing "/" commands.

## Structure

### UI Layout Hierarchy
```
Screen
├── ResourceBar (top, height: 1)
├── Container#workspace (height: 1fr)
│   ├── Container#viewport (width: 1fr)
│   │   ├── ChatContainer
│   │   ├── LoadingIndicator
│   │   └── Static#streaming-output
│   └── Container#context-rail (optional, width: 34)
│       └── Container#context-panel
└── Editor (bottom, height: 6)
    └── Attached dropdowns:
        ├── FileAutoComplete
        ├── CommandAutoComplete  ← Issue here
        └── SkillsAutoComplete
```

### Key Files

| File | Lines | Purpose |
|------|-------|---------|
| `src/tunacode/ui/app.py:155-174` | `compose()` | UI structure, attaches autocomplete widgets to Editor |
| `src/tunacode/ui/widgets/editor.py:1-311` | Editor class | Custom Input widget with multi-line support |
| `src/tunacode/ui/widgets/command_autocomplete.py:1-94` | CommandAutoComplete | Slash command autocomplete implementation |
| `src/tunacode/ui/styles/layout.tcss:85-95` | Editor styles | Height: 6, border styles |
| `src/tunacode/ui/styles/widgets.tcss:1-45` | Autocomplete styles | AutoComplete widget styling |

## Command Autocomplete Implementation

### Widget Definition
**File:** `src/tunacode/ui/widgets/command_autocomplete.py:L20-L94`

```python
class CommandAutoComplete(AutoComplete):
    """Real-time / command autocomplete dropdown."""
    
    def __init__(self, target: Input) -> None:
        super().__init__(target)
```

The `CommandAutoComplete` extends `textual_autocomplete.AutoComplete` and is attached to the Editor Input widget.

### App Composition
**File:** `src/tunacode/ui/app.py:L172-174`

```python
yield self.editor
yield FileAutoComplete(self.editor)
yield CommandAutoComplete(self.editor)  # ← This is the problematic dropdown
yield SkillsAutoComplete(self.editor)
```

## Positioning Logic

### textual-autocomplete Library (v4.0.6)
**File:** `.venv/lib/python3.11/site-packages/textual_autocomplete/_autocomplete.py:L288-L302`

The `_align_to_target()` method positions the dropdown:

```python
def _align_to_target(self) -> None:
    """Align the dropdown to the position of the cursor within
    the target widget, and constrain it to be within the screen."""
    x, y = self.target.cursor_screen_offset  # Get cursor position in screen space
    dropdown = self.option_list
    width, height = dropdown.outer_size

    # Position at cursor + 1 row below, constrain to screen
    x, y, _width, _height = Region(x - 1, y + 1, width, height).constrain(
        "inside",           # Constraint type
        "none",             # Don't clip
        Spacing.all(0),     # No margin
        self.screen.scrollable_content_region,  # Constraint region
    )
    self.absolute_offset = Offset(x, y)
```

### Key Positioning Parameters
- **Base position:** `(cursor_x - 1, cursor_y + 1)` - One cell left, one row below cursor
- **Constraint:** `constrain("inside", ...)` - Keeps dropdown within screen bounds
- **Target region:** `scrollable_content_region` - The visible screen area

## CSS Styling

### Editor Widget
**File:** `src/tunacode/ui/styles/layout.tcss:L85-95`

```tcss
Editor {
    width: 1fr;
    height: 6;           /* Fixed height of 6 rows */
    background: $background;
    border-top: solid $border;
    border-left: solid $border;
    border-bottom: solid $border;
    border-right: solid $border;
    padding: 0 1;
}
```

### Autocomplete Dropdown
**File:** `src/tunacode/ui/styles/widgets.tcss:L1-L10`

```tcss
AutoComplete {
    background: $surface;
    border-top: solid $bevel-light;
    border-left: solid $bevel-light;
    border-bottom: solid $bevel-dark;
    border-right: solid $bevel-dark;
    padding: 0;
    margin: 0;
}
```

### Default textual-autocomplete CSS
**From:** `textual_autocomplete/_autocomplete.py:L71-L88`

```css
AutoComplete {
    height: auto;
    width: auto;
    max-height: 12;      /* Maximum height of 12 rows */
    display: none;
    background: $surface;
    overlay: screen;
    /* ... */
}
```

## Root Cause Analysis

### The Problem
1. The Editor widget is positioned at the **bottom** of the screen
2. The autocomplete dropdown is positioned **below** the cursor (y + 1)
3. The dropdown has a `max-height: 12` which can extend beyond the screen
4. When the terminal window is small or the cursor is near the bottom edge:
   - The constraint logic attempts to keep it "inside"
   - But the positioning may still render partially off-screen
   - User sees only the top portion of the dropdown

### Constraint Behavior
The `constrain("inside", ...)` method from Textual should keep the region within bounds, but:
- If there isn't enough space below, the dropdown may be clipped
- The constraint doesn't flip the dropdown above the cursor when space is insufficient
- The `scrollable_content_region` may not account for the bottom bar or other UI elements

## Dependencies

### Upstream
- `textual-autocomplete==4.0.6` - Provides AutoComplete base class and positioning logic

### Internal
- `tunacode.ui.widgets.editor.Editor` - Target Input widget
- `tunacode.ui.app.TextualReplApp` - Composes the UI layout

## Possible Solutions

### Option 1: Override Positioning (in CommandAutoComplete)
Override `_align_to_target()` to position the dropdown **above** the editor when near bottom:

```python
def _align_to_target(self) -> None:
    x, y = self.target.cursor_screen_offset
    dropdown = self.option_list
    width, height = dropdown.outer_size
    
    # Check if there's room below
    screen_height = self.screen.scrollable_content_region.height
    if y + 1 + height > screen_height:
        # Position above the cursor instead
        y = y - height - 1
    else:
        y = y + 1
    
    self.absolute_offset = Offset(x - 1, max(0, y))
```

### Option 2: Reduce max-height
Reduce the `max-height` in CSS to ensure the dropdown fits on smaller screens:

```tcss
AutoComplete {
    max-height: 6;  /* Reduced from 12 */
}
```

### Option 3: Position relative to Editor top
Always position relative to the Editor widget's top edge rather than cursor position.

## Evidence

### File Locations
- `src/tunacode/ui/widgets/command_autocomplete.py` - Command autocomplete widget
- `src/tunacode/ui/widgets/editor.py:L147-L150` - `cursor_screen_offset` property used for positioning
- `src/tunacode/ui/app.py:L172-174` - Widget composition order
- `src/tunacode/ui/styles/layout.tcss:L85-95` - Editor dimensions
- `src/tunacode/ui/styles/widgets.tcss` - Autocomplete styling
- `.venv/lib/python3.11/site-packages/textual_autocomplete/_autocomplete.py:L288-302` - Upstream positioning logic

### Reproduction
1. Launch TunaCode in a terminal with limited height (< 20 rows)
2. Type "/" in the Editor
3. Observe that the dropdown extends below the visible area
