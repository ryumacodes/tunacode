---
date: "2025-11-29T17:30:00-06:00"
researcher: claude-opus
git_commit: 1fcb170bdbe851bb455a596f702d6fe9695bc4c6
branch: textual_repl
repository: alchemiststudiosDOTai/tunacode
topic: "Textual TUI Architecture and Style Guide Mapping"
tags: [research, textual, tui, architecture, style-guide, ui-unification]
status: complete
last_updated: "2025-11-29"
last_updated_by: claude-opus
---

# Research: Textual TUI Architecture and Style Guide Mapping

**Date**: 2025-11-29T17:30:00-06:00
**Researcher**: claude-opus
**Git Commit**: 1fcb170bdbe851bb455a596f702d6fe9695bc4c6
**Branch**: textual_repl
**Repository**: alchemiststudiosDOTai/tunacode

## Research Question

What exists in the current Textual TUI implementation, and how can the architecture and style guide be mapped and unified?

## Summary

The TunaCode Textual TUI (`src/tunacode/cli/textual_repl.py`) is a functional REPL application that replaced the legacy prompt_toolkit/Rich loop. It implements:

- **5 custom widgets**: ResourceBar, Editor, ToolConfirmationModal, and 2 Static displays
- **4 custom messages**: EditorCompletionsAvailable, EditorSubmitRequested, ShowToolConfirmationModal, ToolConfirmationResult
- **1 custom theme**: "tunacode" built from UI_COLORS palette
- **1 external stylesheet**: textual_repl.tcss (80 lines)

The architecture uses message-driven coordination with Future-based async patterns. A complete style system exists in `constants.py` (UI_COLORS) that is partially integrated with the Textual theme.

## Detailed Findings

### 1. Current Widget Architecture

#### Widget Hierarchy

```
TextualReplApp (App)
├── Header (Textual built-in)
├── ResourceBar (Custom Static)
│   └── Displays: model name (tokens/cost planned but commented)
├── Vertical#body (Container)
│   ├── RichLog (history)
│   │   └── Conversation log with user inputs and responses
│   ├── Static#streaming-output
│   │   └── Live streaming response display
│   └── Editor (Custom TextArea)
│       └── Multiline input with /command and @file completion
└── Footer (Textual built-in - shows ctrl+p binding)
```

**File Reference**: `src/tunacode/cli/textual_repl.py:273-277`

#### Custom Widget Definitions

| Widget | Base Class | Lines | Purpose |
|--------|-----------|-------|---------|
| ResourceBar | Static | 69-110 | Top status bar with model/tokens |
| Editor | TextArea | 112-186 | Multiline input with completions |
| ToolConfirmationModal | ModalScreen | 426-455 | Async tool confirmation dialog |

### 2. Message Architecture

#### Message Types

| Message | Lines | Attributes | Purpose |
|---------|-------|------------|---------|
| EditorCompletionsAvailable | 188-194 | `candidates: list[str]` | Tab completion results |
| EditorSubmitRequested | 196-203 | `text, raw_text` | User input submission |
| ShowToolConfirmationModal | 205-211 | `request: ToolConfirmationRequest` | Trigger confirmation modal |
| ToolConfirmationResult | 213-219 | `response: ToolConfirmationResponse` | User's confirmation decision |

#### Message Flow

```
User Input Flow:
Editor.action_submit() → EditorSubmitRequested → on_editor_submit_requested()
  → request_queue.put() → _request_worker() → _process_request()
  → process_request() (orchestrator)

Tool Confirmation Flow:
tool_callback() → request_tool_confirmation() → ShowToolConfirmationModal
  → on_show_tool_confirmation_modal() → push_screen(ToolConfirmationModal)
  → on_button_pressed() → ToolConfirmationResult
  → on_tool_confirmation_result() → pending_confirmation.set_result()

Streaming Flow:
process_request() → streaming_callback() → current_stream_text += chunk
  → _update_streaming_output() → streaming_output.update()
  → (on completion) RichLog.write() + clear streaming display
```

### 3. Current Styling System

#### Source: UI_COLORS (`constants.py:110-130`)

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

    "file_ref": "#00d7ff",       # Same as primary
}
```

#### Current Theme Registration (`textual_repl.py:221-245`)

```python
THEME_NAME = "tunacode"

def _build_tunacode_theme() -> Theme:
    palette = UI_COLORS
    custom_variables = {
        "text-muted": palette["muted"],
        "border": palette["border"],
        "border-light": palette["border_light"],
    }
    return Theme(
        name=THEME_NAME,
        primary=palette["primary"],
        secondary=palette["accent"],
        accent=palette["primary_light"],
        background=palette["background"],
        surface=palette["surface"],
        panel=palette["border_light"],
        success=palette["success"],
        warning=palette["warning"],
        error=palette["error"],
        boost=palette["primary_dark"],
        foreground=palette["primary_light"],
        variables=custom_variables,
    )
```

#### External Stylesheet (`textual_repl.tcss`)

```tcss
/* Current styling - 80 lines */
ResourceBar { height: 3; background: #162332; color: #00d7ff; ... }
#body { height: 1fr; }
RichLog { height: 1fr; background: $surface; border: solid $border; ... }
#streaming-output { max-height: 30%; background: $surface; ... }
Editor { height: 5; background: $background; border: solid $accent; ... }
ToolConfirmationModal { align: center middle; }
#modal-body { width: 60; border: thick $primary; ... }
```

### 4. Existing Rich UI Components (Legacy)

The `src/tunacode/ui/` directory contains 17 Python files from the pre-Textual implementation:

| File | Status | Components |
|------|--------|------------|
| console.py | Active | get_console(), info(), warning(), error() |
| output.py | Active | banner(), spinner(), version(), usage() |
| panels.py | Active | StreamingAgentPanel, panel(), agent(), error() |
| tool_ui.py | Active | ToolUI class |
| input.py | Legacy | Rich-based input functions |
| prompt_manager.py | Legacy | PromptConfig, PromptManager |
| model_selector.py | Legacy | Interactive model selection |
| completers.py | Legacy | CommandCompleter, FileReferenceCompleter |
| lexers.py | Legacy | FileReferenceLexer |
| keybindings.py | Legacy | create_key_bindings() |

**Note**: "Legacy" files are prompt_toolkit based and not used by Textual REPL.

### 5. Textual Theming System (Library Reference)

#### Theme Properties Available

From `textual/theme.py:12-62`:

```python
@dataclass
class Theme:
    name: str
    primary: str                    # Required
    secondary: str | None = None
    warning: str | None = None
    error: str | None = None
    success: str | None = None
    accent: str | None = None
    foreground: str | None = None
    background: str | None = None
    surface: str | None = None
    panel: str | None = None
    boost: str | None = None
    dark: bool = True
    luminosity_spread: float = 0.15
    text_alpha: float = 0.95
    variables: dict[str, str] = field(default_factory=dict)
```

#### Generated CSS Variables (120+)

The Textual ColorSystem generates these variable categories:

| Category | Examples | Count |
|----------|----------|-------|
| Base colors | `$primary`, `$secondary`, `$surface` | 13 |
| Shades | `$primary-darken-2`, `$primary-lighten-1` | 91 (13 x 7) |
| Text | `$text`, `$text-muted`, `$text-disabled` | 6+ |
| Semantic | `$text-primary`, `$text-error`, `$text-success` | 6 |
| Muted | `$primary-muted`, `$secondary-muted` | 6+ |
| Scrollbar | `$scrollbar`, `$scrollbar-hover`, etc. | 7 |
| Links | `$link-color`, `$link-background`, etc. | 4 |
| Footer | `$footer-foreground`, `$footer-key-*` | 6 |
| Input | `$input-cursor-*`, `$input-selection-*` | 3 |
| Button | `$button-foreground`, `$button-focus-*` | 3 |
| Block cursor | `$block-cursor-*`, `$block-hover-*` | 8 |
| Markdown | `$markdown-h1-color`, etc. | 18 |

### 6. Current Architecture Gaps

#### Widget ID Consistency

Current IDs in use:
- `#body` - main vertical container
- `#streaming-output` - streaming display Static
- `#modal-body` - confirmation modal container
- `#tool-title` - modal title label
- `#actions` - modal button container
- `#yes`, `#no` - modal buttons

No formal naming convention documented.

#### CSS Variable Usage

Current usage pattern mixes:
- Theme variables: `$surface`, `$border`, `$accent`, `$primary`
- Hardcoded colors: `#162332`, `#00d7ff`, `#2d4461` in ResourceBar

#### Component Styling Coverage

| Component | Has CSS | Uses Theme Vars | Notes |
|-----------|---------|-----------------|-------|
| ResourceBar | Yes | Partial | Hardcoded colors in TCSS |
| RichLog | Yes | Yes | Uses $surface, $border |
| #streaming-output | Yes | Yes | Uses $surface, $border |
| Editor | Yes | Yes | Uses $background, $accent |
| ToolConfirmationModal | Yes | Partial | Uses $primary, $surface |
| Header | Default | - | Textual built-in |
| Footer | Default | - | Textual built-in |

### 7. Binding Architecture

#### App-Level Bindings (`textual_repl.py:254-256`)

```python
BINDINGS = [
    Binding("ctrl+p", "toggle_pause", "Pause/Resume Stream", priority=True),
]
```

#### Widget-Level Bindings (`textual_repl.py:115-118`)

```python
# Editor
BINDINGS = [
    Binding("tab", "complete", "Complete", show=False),
    Binding("enter", "submit", "Submit", show=False),
]
```

#### Custom Key Handling (`textual_repl.py:168-185`)

- `escape` - Sets flag for Esc+Enter newline sequence
- `escape+enter` - Inserts literal newline
- `enter` (standalone) - Triggers submit

### 8. State Management

#### TextualReplApp State (`textual_repl.py:258-271`)

| Attribute | Type | Purpose |
|-----------|------|---------|
| state_manager | StateManager | Orchestrator state |
| rich_log | RichLog | Conversation history |
| editor | Editor | User input widget |
| resource_bar | ResourceBar | Status display |
| request_queue | asyncio.Queue[str] | Request processing queue |
| pending_confirmation | Future[ToolConfirmationResponse] | Modal result |
| _streaming_paused | bool | Pause flag |
| _stream_buffer | list[str] | Buffered chunks while paused |
| current_stream_text | str | Accumulated response |
| streaming_output | Static | Live display widget |

#### ResourceBar State (`textual_repl.py:72-78`)

| Attribute | Type | Purpose |
|-----------|------|---------|
| _tokens | int | Current token count |
| _max_tokens | int | Token limit (200000) |
| _model | str | Current model name |
| _cost | float | Last call cost |
| _session_cost | float | Session total cost |

## Code References

### Core Implementation
- `src/tunacode/cli/textual_repl.py:1-478` - Main Textual REPL
- `src/tunacode/cli/textual_repl.tcss:1-80` - External stylesheet
- `src/tunacode/constants.py:110-130` - UI_COLORS palette

### Widget Definitions
- `src/tunacode/cli/textual_repl.py:69-110` - ResourceBar
- `src/tunacode/cli/textual_repl.py:112-186` - Editor
- `src/tunacode/cli/textual_repl.py:426-455` - ToolConfirmationModal

### Message Definitions
- `src/tunacode/cli/textual_repl.py:188-219` - All 4 message classes

### Theme Construction
- `src/tunacode/cli/textual_repl.py:221-245` - _build_tunacode_theme()

### Entry Point
- `src/tunacode/cli/textual_repl.py:420-423` - run_textual_repl()

## Architecture Documentation

### Current Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     TextualReplApp                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                     Header                           │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                   ResourceBar                        │   │
│  │  Model: {model_name}                                │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Vertical #body                         │   │
│  │  ┌─────────────────────────────────────────────┐   │   │
│  │  │              RichLog                        │   │   │
│  │  │  > user input                               │   │   │
│  │  │  assistant response...                      │   │   │
│  │  │  > user input                               │   │   │
│  │  └─────────────────────────────────────────────┘   │   │
│  │  ┌─────────────────────────────────────────────┐   │   │
│  │  │        Static #streaming-output             │   │   │
│  │  │  (live response while streaming)            │   │   │
│  │  └─────────────────────────────────────────────┘   │   │
│  │  ┌─────────────────────────────────────────────┐   │   │
│  │  │              Editor                         │   │   │
│  │  │  Enter a request...                         │   │   │
│  │  └─────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                     Footer                           │   │
│  │  ^p Pause/Resume Stream                              │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Message Flow Diagram

```
┌──────────┐    EditorSubmitRequested    ┌─────────────────┐
│  Editor  │ ──────────────────────────► │ TextualReplApp  │
└──────────┘                             └────────┬────────┘
                                                  │
                                     request_queue.put()
                                                  │
                                                  ▼
                                         ┌───────────────┐
                                         │ _request_     │
                                         │ worker()      │
                                         └───────┬───────┘
                                                 │
                                    process_request()
                                                 │
            ┌────────────────────────────────────┼────────────────────────────────────┐
            │                                    │                                     │
            ▼                                    ▼                                     ▼
   tool_callback()                    streaming_callback()                    completion
            │                                    │                                     │
ShowToolConfirmationModal           current_stream_text += chunk            RichLog.write()
            │                                    │                                     │
            ▼                                    ▼                                     │
┌───────────────────┐              ┌────────────────────┐                             │
│ToolConfirmation   │              │ streaming_output   │                             │
│     Modal         │              │     .update()      │                             │
└─────────┬─────────┘              └────────────────────┘                             │
          │                                                                           │
   on_button_pressed                                                                  │
          │                                                                           │
ToolConfirmationResult                                                                │
          │                                                                           │
          ▼                                                                           │
pending_confirmation                                                                  │
    .set_result()                                                                     │
          │                                                                           │
          └───────────────────────────────────────────────────────────────────────────┘
```

### Theme/CSS Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    constants.py                             │
│                     UI_COLORS                               │
│  primary, background, surface, border, success, etc.       │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│               _build_tunacode_theme()                       │
│                                                             │
│  Theme(                                                     │
│    name="tunacode",                                         │
│    primary=UI_COLORS["primary"],                            │
│    ...                                                      │
│    variables={                                              │
│      "text-muted": UI_COLORS["muted"],                     │
│      "border": UI_COLORS["border"],                        │
│      ...                                                    │
│    }                                                        │
│  )                                                          │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                Textual ColorSystem                          │
│                                                             │
│  Generates 120+ CSS variables:                             │
│  $primary, $primary-darken-1, $surface, $text-muted, ...  │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│               textual_repl.tcss                             │
│                                                             │
│  ResourceBar { background: #162332; }  ← Hardcoded        │
│  RichLog { background: $surface; }     ← Theme var        │
│  Editor { border: solid $accent; }     ← Theme var        │
└─────────────────────────────────────────────────────────────┘
```

## Historical Context

### Migration Journey

1. **Pre-migration**: 17 files in `src/tunacode/ui/` using Rich/prompt_toolkit
2. **Research**: `memory-bank/research/2025-11-29_14-53-40_rich-to-textual-migration.md`
3. **Plan**: `memory-bank/plan/2025-11-29_textual-repl-migration-plan.md`
4. **Current**: Tasks 1-4 complete (with issues), Tasks 5-8 pending

### Key Decisions Made

- Future-based async tool confirmation pattern
- Buffer-based streaming pause/resume
- Single-file Textual app (no module extraction yet)
- External TCSS stylesheet over inline DEFAULT_CSS

## Related Research

- `memory-bank/research/2025-11-29_14-53-40_rich-to-textual-migration.md` - Original migration analysis
- `memory-bank/research/2025-11-29_textual-repl-tui-modernization.md` - TUI modernization research
- `memory-bank/plan/2025-11-29_textual-repl-migration-plan.md` - Task breakdown and status
- `memory-bank/communication/2025-11-29_gemini_textual-migration-discussion.md` - Implementation notes

## Appendix: Complete UI_COLORS to Theme Variable Mapping

| UI_COLORS Key | Theme Property | CSS Variable |
|---------------|----------------|--------------|
| primary | primary | $primary |
| primary_light | accent | $accent |
| primary_dark | boost | $boost |
| accent | secondary | $secondary |
| background | background | $background |
| surface | surface | $surface |
| border | variables["border"] | $border |
| border_light | panel | $panel |
| muted | variables["text-muted"] | $text-muted |
| secondary | (unused) | - |
| success | success | $success |
| warning | warning | $warning |
| error | error | $error |
| file_ref | (unused) | - |

## Appendix: TCSS Variable Coverage

| Selector | Hardcoded Colors | Theme Variables Used |
|----------|-----------------|---------------------|
| ResourceBar | #162332, #00d7ff, #2d4461 | none |
| RichLog | none | $surface, $border |
| #streaming-output | none | $surface, $border |
| Editor | none | $background, $accent |
| ToolConfirmationModal | none | none |
| #modal-body | none | $primary, $surface |
| #tool-title | none | $primary |
