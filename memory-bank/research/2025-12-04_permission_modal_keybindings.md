# Research – Permission Modal Key Bindings & UX
**Date:** 2025-12-04
**Owner:** Claude Agent
**Phase:** Research
**Status:** GAP IDENTIFIED - Implementation needed

## Goal
Investigate the permission/confirmation modal to verify key bindings work as expected:
- Key 1 = Yes (approve)
- Key 2 = Yes + don't ask again for this session
- Key 3 = No + take feedback

## Findings

### Current Modal Implementation

| File | Line | Component |
|------|------|-----------|
| `src/tunacode/ui/screens/confirmation.py` | 28-47 | `ToolConfirmationModal` class |
| `src/tunacode/ui/screens/confirmation.py` | 49-59 | `on_button_pressed()` handler |
| `src/tunacode/ui/app.py` | 180-197 | `request_tool_confirmation()` |

### Current UI Components

```
┌─────────────────────────────────────────────────┐
│  Confirm tool: {tool_name}                      │
│  Args: {args}                                   │
│                                                 │
│  [ ] Skip future confirmations for this tool   │  ← Checkbox
│                                                 │
│  [  Yes  ]  [  No  ]                            │  ← Buttons (mouse only)
└─────────────────────────────────────────────────┘
```

### GAP: No Key Bindings Defined

**Current state:** The modal has **NO key bindings**. Users must click buttons with mouse.

```python
# confirmation.py:28-47 - NO BINDINGS attribute defined
class ToolConfirmationModal(ModalScreen[None]):
    # No BINDINGS = [...] defined
    def compose(self) -> ComposeResult:
        yield Vertical(
            Label(f"Confirm tool: {self.request.tool_name}", id="tool-title"),
            Label(f"Args: {self.request.args}"),
            self.skip_future,  # Checkbox widget
            Horizontal(
                Button("Yes", id=BUTTON_ID_YES, variant="success"),
                Button("No", id=BUTTON_ID_NO, variant="error"),
                id="actions",
            ),
            id="modal-body",
        )
```

### GAP: No "No with Feedback" Option

The `instructions` field exists in the response type but is **never populated**:

```python
# types.py:89-95
@dataclass
class ToolConfirmationResponse:
    approved: bool
    skip_future: bool = False
    abort: bool = False
    instructions: str = ""  # ← EXISTS but always empty
```

The notifier IS designed to use feedback if provided:

```python
# notifier.py:23-27
guidance = getattr(response, "instructions", "").strip()
if guidance:
    guidance_section = f"User guidance:\n{guidance}"
else:
    guidance_section = "User cancelled without additional instructions."
```

### Current Response Flow

```
┌────────────────────────────────────────────────────────────────┐
│ 1. User clicks Yes/No button                                   │
│    ↓                                                           │
│ 2. on_button_pressed() (confirmation.py:49)                    │
│    approved = (button_id == "yes")                             │
│    skip_future = checkbox.value                                │
│    ↓                                                           │
│ 3. ToolConfirmationResponse created (confirmation.py:53-57)    │
│    instructions = "" (hardcoded empty)                         │
│    ↓                                                           │
│ 4. process_confirmation() (handler.py:48-55)                   │
│    - If skip_future: add to tool_ignore list                   │
│    - If rejected: notify agent with empty guidance             │
└────────────────────────────────────────────────────────────────┘
```

## Required Changes for Expected Behavior

### Option A: Key Bindings on Existing Modal

Add to `ToolConfirmationModal`:

```python
BINDINGS = [
    Binding("1", "approve", "Yes"),
    Binding("2", "approve_skip", "Yes (skip future)"),
    Binding("3", "reject_feedback", "No (with feedback)"),
    Binding("escape", "reject", "No"),
]
```

### Option B: Complete UI Redesign

Replace checkbox + buttons with 3 clear options:

```
┌─────────────────────────────────────────────────┐
│  Confirm tool: {tool_name}                      │
│  Args: {args}                                   │
│                                                 │
│  [1] Yes - Execute this tool                    │
│  [2] Yes - Execute and skip future prompts      │
│  [3] No  - Reject with feedback                 │
│                                                 │
│  Press 1, 2, or 3 to select                     │
└─────────────────────────────────────────────────┘
```

### Components to Modify

| File | Change |
|------|--------|
| `ui/screens/confirmation.py:28` | Add `BINDINGS` class attribute |
| `ui/screens/confirmation.py:36-47` | Update `compose()` for new UI |
| `ui/screens/confirmation.py:49-59` | Add action methods for bindings |
| `ui/screens/confirmation.py` (new) | Add `Input` widget for feedback on option 3 |

## Key Patterns / Solutions Found

### Textual Key Binding Pattern
```python
from textual.binding import Binding

class MyModal(ModalScreen):
    BINDINGS = [
        Binding("1", "action_one", "First option"),
    ]

    def action_action_one(self) -> None:
        # Handle key press
        pass
```

### Feedback Input Pattern
```python
from textual.widgets import Input

class ToolConfirmationModal(ModalScreen):
    def compose(self):
        yield Input(placeholder="Why reject? (optional)", id="feedback")

    def action_reject_feedback(self):
        feedback_input = self.query_one("#feedback", Input)
        instructions = feedback_input.value
        # Include in response
```

## Knowledge Gaps

1. **User preference**: Does user want separate 3 buttons or key-only interaction?
2. **Feedback UX**: Should feedback input appear immediately or only after pressing 3?
3. **Focus management**: How should tab navigation work between options?

## References

- `src/tunacode/ui/screens/confirmation.py:28-59` - Current modal implementation
- `src/tunacode/ui/app.py:180-197` - Confirmation request/response handling
- `src/tunacode/tools/authorization/handler.py:48-55` - Response processing
- `src/tunacode/tools/authorization/notifier.py:15-36` - Rejection feedback to agent
- `src/tunacode/types.py:89-95` - Response dataclass with unused `instructions` field
