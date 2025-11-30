# Research: TUI Architecture Map

**Date**: 2025-11-30T13:45:00-06:00
**Researcher**: claude-opus
**Branch**: textual_repl
**Status**: complete

---

## Goal

Map the complete TUI/UI architecture during the ongoing Textual migration to establish a clear picture of:
- Current file structure and responsibilities
- Widget/component hierarchy
- Data and message flows
- Migration status and remaining work

---

## TUI Architecture Overview

### Tech Stack Evolution

| Layer | OLD (Deprecated) | NEW (Active) |
|-------|------------------|--------------|
| Framework | prompt_toolkit + Rich | Textual |
| Input | `prompt_toolkit.prompt()` | `TextArea` widget |
| Output | `Rich.Console.print()` | `RichLog` widget |
| Confirmations | Blocking `input()` | Async `ModalScreen` + `Future` |
| Styling | Inline Rich markup | TCSS + Theme system |
| State | Scattered across ui/ | Centralized in `TextualReplApp` |

---

## File Structure Map

### Active Textual TUI Files

```
src/tunacode/cli/
├── textual_repl.py      # Main App (TextualReplApp) - 350 lines
├── widgets.py           # Custom widgets - 195 lines
│   ├── ResourceBar      # Top status bar (model/tokens/cost)
│   ├── ToolStatusBar    # Real-time tool activity display
│   └── Editor           # Multiline input with completions
├── screens.py           # Modal screens - 65 lines
│   └── ToolConfirmationModal
├── textual_repl.tcss    # External stylesheet - 80 lines
└── repl.py              # Legacy shim (raises RuntimeError)
```

### Supporting UI Files (Still Active)

```
src/tunacode/ui/
├── output.py            # Output routing with sink pattern
├── console.py           # Console coordination & lazy loading
├── panels.py            # StreamingAgentPanel (Rich-based)
├── completers.py        # Command/File/Model completers
├── tool_ui.py           # Legacy tool confirmations (being replaced)
├── tool_descriptions.py # Tool display formatting
├── constants.py         # SPINNER_TYPE, DEFAULT_PROMPT
├── input.py             # Legacy Rich input functions
├── keybindings.py       # Legacy prompt_toolkit bindings
├── prompt_manager.py    # Legacy PromptConfig/Manager
├── model_selector.py    # Interactive model selection
├── validators.py        # Input validators
├── lexers.py            # FileReferenceLexer
├── decorators.py        # Async-to-sync wrappers
├── logging_compat.py    # UnifiedUILogger
├── path_heuristics.py   # Path utilities
└── utils.py             # Empty placeholder
```

### Constants & Theme

```
src/tunacode/
├── constants.py         # UI_COLORS palette + build_tunacode_theme()
└── types.py             # ToolConfirmationRequest/Response
```

---

## Widget Hierarchy

```
TextualReplApp (App[None])
├── Header (built-in)
├── ResourceBar (Custom Static)
│   └── Displays: model name, tokens, cost
├── Vertical#body (Container)
│   ├── RichLog (conversation history)
│   │   └── All user inputs + agent responses
│   ├── ToolStatusBar (Custom Static) [NEW]
│   │   └── Real-time tool activity feedback
│   ├── Static#streaming-output
│   │   └── Live response while streaming
│   └── Editor (Custom TextArea)
│       └── Multiline input with Tab completion
└── Footer (built-in: keybindings)
```

---

## Message Architecture

### Custom Messages (widgets.py + screens.py)

| Message | Purpose | Attributes |
|---------|---------|------------|
| `EditorCompletionsAvailable` | Tab completion results | `candidates: list[str]` |
| `EditorSubmitRequested` | User input submission | `text: str` |
| `ToolStatusUpdate` | Update tool status bar | `status: str` |
| `ToolStatusClear` | Clear tool status bar | none |
| `ShowToolConfirmationModal` | Trigger confirmation modal | `request: ToolConfirmationRequest` |
| `ToolConfirmationResult` | Modal response | `response: ToolConfirmationResponse` |

### Message Flows

```
USER INPUT FLOW:
Editor.action_submit()
  → EditorSubmitRequested message
  → on_editor_submit_requested()
  → request_queue.put()
  → _request_worker()
  → _process_request()
  → process_request() [orchestrator]

TOOL CONFIRMATION FLOW:
build_textual_tool_callback()
  → app.request_tool_confirmation()
  → Creates asyncio.Future
  → ShowToolConfirmationModal message
  → push_screen(ToolConfirmationModal)
  → User clicks button
  → ToolConfirmationResult message
  → pending_confirmation.set_result()

STREAMING FLOW:
process_request() yields chunks
  → streaming_callback()
  → Buffers if paused, else appends to current_stream_text
  → _update_streaming_output()
  → streaming_output.update()
  → On completion: RichLog.write() + clear streaming

TOOL STATUS FLOW:
Agent executes tool
  → tool_status_callback("Running grep...")
  → ToolStatusUpdate message
  → on_tool_status_update()
  → tool_status.set_status()
  → On completion: ToolStatusClear message
```

---

## Output Sink Pattern

Routes legacy `ui.print()` calls to Textual RichLog:

```
Legacy Code                    Bridge                      Textual
────────────                   ──────                      ───────
ui.print("...")     →    register_output_sink()    →    RichLog.write()
ui.panel("...")     →    _log_to_rich_log()        →    RichLog.write()
```

**Implementation**: `output.py:198-201` + `textual_repl.py:244-253`

---

## Theme System

### Color Palette (constants.py)

```python
UI_COLORS = {
    "primary": "#00d7ff",        # Bright cyan
    "primary_light": "#4de4ff",  # Light cyan
    "primary_dark": "#0095b3",   # Dark cyan
    "accent": "#0ea5e9",         # Rich cyan
    "background": "#0d1720",     # Ultra dark
    "surface": "#162332",        # Panels
    "border": "#2d4461",         # Strong borders
    "border_light": "#1e2d3f",   # Subtle borders
    "muted": "#6b8aa3",          # Secondary text
    "success": "#059669",        # Emerald green
    "warning": "#d97706",        # Amber
    "error": "#dc2626",          # Red
}
```

### Textual Theme (build_tunacode_theme)

Maps UI_COLORS to Textual Theme properties, generating 120+ CSS variables.

### TCSS Stylesheet (textual_repl.tcss)

| Selector | Theme Variables Used | Notes |
|----------|---------------------|-------|
| ResourceBar | `$surface`, `$primary`, `$border` | Fully themed |
| RichLog | `$surface`, `$border` | Fully themed |
| #streaming-output | `$surface`, `$border` | Fully themed |
| Editor | `$background`, `$accent` | Fully themed |
| ToolConfirmationModal | `$primary`, `$surface` | Fully themed |

---

## Key Bindings

### App-Level (textual_repl.py)

| Key | Action | Description |
|-----|--------|-------------|
| Ctrl+P | `action_toggle_pause` | Pause/Resume Stream |

### Editor Widget (widgets.py)

| Key | Action | Description |
|-----|--------|-------------|
| Tab | `action_complete` | Trigger completion |
| Enter | `action_submit` | Submit input |
| Esc → Enter | Insert newline | Two-key sequence |

---

## Migration Status

### Completed Tasks (T1-T4)

| Task | Description | Status |
|------|-------------|--------|
| T1.1-T1.3 | Add ToolStatusUpdate/Clear messages + widget | DONE |
| T2.1-T2.5 | Integrate ToolStatusBar into TextualReplApp | DONE |
| T3.1-T3.3 | Thread tool_status_callback through orchestration | DONE |
| T4.1-T4.4 | Replace ui.update_spinner_message() | DONE |

### Recent Commits

```
d7affa4 fix: Defer widget creation to compose() (NoActiveAppError fix)
9e5da82 fix: Replace magic literals with constants
92ae00e feat(T4.1-T4.4): Replace ui.update_spinner_message() with callback
44f54de feat(T3.1-T3.3): Thread tool_status_callback through orchestration
587b0d7 feat(T2.1-T2.5): Integrate ToolStatusBar widget
3f7de5e feat(T1.1-T1.3): Add ToolStatusUpdate/Clear messages and widget
```

### Pending Work

| Task | Description | Notes |
|------|-------------|-------|
| T5 | Streaming pause/resume UI controls | Logic exists, UI exposure missing |
| T6 | Complete orchestrator error handling | May need hardening |
| T7 | Golden baseline + E2E tests | No Textual tests exist yet |
| T8 | PR preparation + docs | Branch exists |

---

## Architecture Patterns

### 1. Future-Based Async Tool Confirmation

```python
async def request_tool_confirmation(self, request):
    self.pending_confirmation = asyncio.Future()
    self.post_message(ShowToolConfirmationModal(request=request))
    return await self.pending_confirmation  # Non-blocking
```

### 2. Streaming with Pause/Resume Buffer

```python
async def streaming_callback(self, chunk: str):
    if self._streaming_paused:
        self._stream_buffer.append(chunk)
    else:
        self.current_stream_text += chunk
```

### 3. Widget Composition in compose()

Widgets created in `compose()` to ensure app context is active, avoiding `NoActiveAppError`.

### 4. Message-Driven Decoupling

All UI events use Textual messages for loose coupling between components.

### 5. Background Worker Pattern

Request processing in dedicated worker task keeps UI responsive.

---

## Class Hierarchy

```
Textual Framework Classes:
├── App[None]
│   └── TextualReplApp
├── ModalScreen[None]
│   └── ToolConfirmationModal
├── Static
│   ├── ResourceBar
│   └── ToolStatusBar
└── TextArea
    └── Editor

Message Classes:
├── Message
│   ├── EditorCompletionsAvailable
│   ├── EditorSubmitRequested
│   ├── ToolStatusUpdate
│   ├── ToolStatusClear
│   ├── ShowToolConfirmationModal
│   └── ToolConfirmationResult

Legacy UI Classes:
├── ToolUI (tool_ui.py) - being replaced
└── StreamingAgentPanel (panels.py) - Rich-based
```

---

## File References

### Core Implementation
- `src/tunacode/cli/textual_repl.py` - Main Textual app
- `src/tunacode/cli/widgets.py` - Custom widgets (ResourceBar, Editor, ToolStatusBar)
- `src/tunacode/cli/screens.py` - Modal screens (ToolConfirmationModal)
- `src/tunacode/cli/textual_repl.tcss` - Stylesheet

### Output Integration
- `src/tunacode/ui/output.py` - Output sink routing
- `src/tunacode/ui/console.py` - Console coordination

### Completion System
- `src/tunacode/ui/completers.py` - Command/File/Model completers

### Theme & Constants
- `src/tunacode/constants.py` - UI_COLORS + build_tunacode_theme()
- `src/tunacode/types.py` - ToolConfirmationRequest/Response

### Related Documentation
- `memory-bank/plan/2025-11-29_textual-repl-migration-plan.md`
- `memory-bank/research/2025-11-29_textual-tui-architecture-and-style-guide.md`

---

## Visual Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                       TextualReplApp                             │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                        Header                              │  │
│  └───────────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  ResourceBar: claude-3-opus | 45,230/200,000 | $0.12       │  │
│  └───────────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                    Vertical#body                           │  │
│  │  ┌─────────────────────────────────────────────────────┐  │  │
│  │  │  RichLog (Conversation History)                     │  │  │
│  │  │  > How do I fix this bug?                           │  │  │
│  │  │  I'll analyze the code...                           │  │  │
│  │  │  > Thanks! Can you also...                          │  │  │
│  │  └─────────────────────────────────────────────────────┘  │  │
│  │  ┌─────────────────────────────────────────────────────┐  │  │
│  │  │  ToolStatusBar: Running grep in src/...             │  │  │
│  │  └─────────────────────────────────────────────────────┘  │  │
│  │  ┌─────────────────────────────────────────────────────┐  │  │
│  │  │  #streaming-output                                  │  │  │
│  │  │  Let me search for the relevant files...            │  │  │
│  │  └─────────────────────────────────────────────────────┘  │  │
│  │  ┌─────────────────────────────────────────────────────┐  │  │
│  │  │  Editor                                             │  │  │
│  │  │  Type your message... (Tab: complete, Enter: send)  │  │  │
│  │  └─────────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Footer: ^p Pause/Resume Stream                           │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│                   ToolConfirmationModal                          │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Tool: bash                                                 │ │
│  │  Args: command="rm -rf /tmp/test"                          │ │
│  │  ┌────────────┐  ┌────────────┐                            │ │
│  │  │ [ ] Skip   │  │   [ Yes ]  │  [ No ]                    │ │
│  │  └────────────┘  └────────────┘                            │ │
│  └────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
```

---

## Knowledge Gaps

1. **E2E Tests**: No Textual-specific tests exist yet
2. **Pause/Resume UI**: Logic implemented, user controls not exposed
3. **Legacy File Cleanup**: Unclear which `ui/` files can be removed
4. **Error Surface**: Need to verify error handling displays properly in TUI

---

## Recommended Next Steps

1. **Add Pause/Resume Controls** - Expose Ctrl+P in UI with visual indicator
2. **Create E2E Tests** - Golden baseline for app startup, tool confirmation flow
3. **Audit Legacy Files** - Identify unused `ui/` files for removal
4. **Update Documentation** - README CLI section, keybindings guide
