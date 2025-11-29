---
date: "2025-11-29T16:33:26-06:00"
researcher: claude-opus
git_commit: 6ea592643288dcfc7b3f6aa87b9acf54423a636a
branch: textual_repl
repository: alchemiststudiosDOTai/tunacode
topic: "Textual REPL TUI Modernization"
tags: [research, textual, tui, css, styling, ui-modernization]
status: complete
last_updated: "2025-11-29"
last_updated_by: claude-opus
---

# Research: Textual REPL TUI Modernization

**Date**: 2025-11-29T16:33:26-06:00
**Researcher**: claude-opus
**Git Commit**: 6ea592643288dcfc7b3f6aa87b9acf54423a636a
**Branch**: textual_repl
**Repository**: alchemiststudiosDOTai/tunacode

## Research Question

How is the current TextualReplApp structured and what patterns exist for modernizing its TUI appearance?

## Summary

The TextualReplApp (`src/tunacode/cli/textual_repl.py`) is a recently created Textual application that replaced the legacy Rich/prompt_toolkit REPL. It currently has **minimal styling** - only the `ResourceBar` widget has inline CSS. The app uses `CSS_PATH = None`, meaning no external stylesheet is loaded. A screenshot shows the current UI has text rendering issues (word-by-word line breaks) and lacks visual polish.

The codebase has an existing cyan-themed color palette in `constants.py` that could inform a Textual theme. Modern Textual best practices favor external `.tcss` files, docked layouts, custom themes, and proper widget borders/padding.

## Detailed Findings

### Current TextualReplApp Structure

**File**: `src/tunacode/cli/textual_repl.py` (454 lines)

**Widget Hierarchy**:
```
TextualReplApp(App)
├── Header (Textual built-in)
├── ResourceBar(Static) - custom top bar
├── Vertical(id="body")
│   ├── RichLog - conversation history
│   ├── Static(id="streaming-output") - live streaming display
│   └── Editor(TextArea) - custom multiline input
└── Footer (Textual built-in)
```

**Custom Widgets**:

1. **ResourceBar** (`textual_repl.py:67-127`)
   - Displays model name (tokens/cost display commented out as TODO)
   - Only widget with inline CSS:
   ```css
   ResourceBar {
       dock: top;
       height: 1;
       background: $surface;
       color: $text-muted;
       padding: 0 1;
   }
   ```

2. **Editor** (`textual_repl.py:130-203`)
   - Extends TextArea
   - Custom keybindings: Tab (complete), Enter (submit), Esc+Enter (newline)
   - Completions for `/commands` and `@files`
   - No CSS styling defined

3. **ToolConfirmationModal** (`textual_repl.py:402-431`)
   - Extends ModalScreen
   - Basic Yes/No buttons with Checkbox
   - No CSS styling - noted as "looks terrible" in migration plan

**App Configuration**:
- Line 242: `CSS_PATH = None` - no external stylesheet
- Line 244-246: Single binding `ctrl+p` for pause/resume
- Uses Textual's default theme

### Observed UI Issues (from screenshot)

The screenshot `Screenshot 2025-11-29 161357.png` shows:

1. **Word-by-word line breaking** - Text like "O help you with your code base or workflow today?" displays as one word per line, indicating width/wrapping issues

2. **Raw text display** - Status shows as separate lines: "T", "UN", "AC", "ODE", "DONE" instead of "TUNACODE DONE"

3. **Basic styling** - No borders, minimal visual hierarchy, default colors

4. **Large empty input area** - The Editor takes significant vertical space

5. **Footer binding display** - Shows "^p Pause/Resume Stream" twice

### Existing Color Palette

**File**: `src/tunacode/constants.py:110-129`

```python
UI_COLORS = {
    # Core brand colors
    "primary": "#00d7ff",        # Bright cyan
    "primary_light": "#4de4ff",  # Light cyan
    "primary_dark": "#0095b3",   # Dark cyan
    "accent": "#0ea5e9",         # Rich cyan

    # Background & structure
    "background": "#0d1720",     # Ultra dark with cyan undertone
    "surface": "#162332",        # Panels, cards
    "border": "#2d4461",         # Stronger cyan-gray borders
    "border_light": "#1e2d3f",   # Subtle borders

    # Text
    "muted": "#6b8aa3",          # Secondary text
    "secondary": "#4a6582",      # Tertiary text

    # Semantic
    "success": "#059669",        # Emerald green
    "warning": "#d97706",        # Muted amber
    "error": "#dc2626",          # Clean red

    "file_ref": "#00d7ff",
}
```

This palette is used by Rich-based UI modules but not yet integrated with Textual.

### Modern Textual Design Patterns

**External CSS Files** (Recommended)

```python
# In app class
CSS_PATH = "app.tcss"
```

**Docked Layout Pattern** (for REPL interfaces)

```tcss
Header {
    dock: top;
}

#chat-container {
    height: 1fr;
    overflow-y: auto;
}

Input {
    dock: bottom;
    height: 3;
    border-top: solid $secondary;
}
```

**Custom Theme Registration**

```python
from textual.theme import Theme

def on_mount(self) -> None:
    theme = Theme(
        name="tunacode",
        primary="#00d7ff",
        secondary="#0ea5e9",
        accent="#4de4ff",
        background="#0d1720",
        surface="#162332",
        panel="#1e2d3f",
        # ...
    )
    self.register_theme(theme)
    self.theme = "tunacode"
```

**Message Styling** (for chat interfaces)

```tcss
.message-user {
    background: $panel;
    border-left: heavy $primary;
    padding: 1 2;
    margin: 0 0 1 0;
}

.message-assistant {
    background: $surface;
    border-left: heavy $accent;
    padding: 1 2;
    margin: 0 0 1 0;
}
```

**Responsive Sizing**

```tcss
.main-content {
    height: 1fr;  /* Fractional unit - takes remaining space */
}

.sidebar {
    width: 25%;   /* Percentage of parent */
}
```

## Code References

- `src/tunacode/cli/textual_repl.py:67-78` - ResourceBar DEFAULT_CSS (only inline CSS)
- `src/tunacode/cli/textual_repl.py:130-203` - Editor widget (no CSS)
- `src/tunacode/cli/textual_repl.py:239-394` - TextualReplApp (CSS_PATH = None)
- `src/tunacode/cli/textual_repl.py:402-431` - ToolConfirmationModal (no CSS)
- `src/tunacode/constants.py:110-129` - UI_COLORS palette (Rich-based, reusable)

## Architecture Documentation

### Current Styling Architecture

```
+---------------------+
| No External CSS     |
| (CSS_PATH = None)   |
+---------------------+
         |
         v
+---------------------+
| ResourceBar         |
| (inline DEFAULT_CSS)|
+---------------------+
         |
         v
+---------------------+
| All Other Widgets   |
| (Textual defaults)  |
+---------------------+
```

### Widget Messaging Flow

```
Editor -> EditorSubmitRequested -> TextualReplApp
  -> request_queue.put()
  -> _request_worker()
  -> process_request() (orchestrator)
  -> streaming_callback() -> streaming_output.update()
  -> RichLog.write() (final)
```

### Tool Confirmation Flow

```
process_request() -> tool_callback()
  -> request_tool_confirmation()
  -> ShowToolConfirmationModal message
  -> ToolConfirmationModal screen pushed
  -> Button press -> ToolConfirmationResult message
  -> pending_confirmation Future resolved
```

## Historical Context (from migration docs)

**From migration plan** (`memory-bank/plan/2025-11-29_textual-repl-migration-plan.md`):
- Task 4 notes modal is "functional but unstyled (looks terrible per project lead)"
- Tasks 5-8 remain incomplete (streaming integration, orchestrator wiring, testing, PR)

**From communication log** (`memory-bank/communication/2025-11-29_gemini_textual-migration-discussion.md`):
- Migration replaced 17 files in `ui/` directory
- Future-based async tool confirmation pattern agreed upon
- Buffer-based streaming pause/resume pattern agreed upon

## Related Research

- `memory-bank/research/2025-11-29_14-53-40_rich-to-textual-migration.md` - Original migration research
- `memory-bank/plan/2025-11-29_textual-repl-migration-plan.md` - Detailed task breakdown

## Open Questions

1. **Streaming display wrapping** - Why does text appear word-by-word? Is it the `Static` widget's width calculation or the update mechanism?

2. **Theme integration** - Should UI_COLORS from constants.py be converted to a Textual Theme, or should a fresh design be created?

3. **Modal styling priority** - Is ToolConfirmationModal styling blocking anything, or can it be addressed as part of general polish?

4. **Input area height** - Should the Editor widget have a fixed height or grow with content?
