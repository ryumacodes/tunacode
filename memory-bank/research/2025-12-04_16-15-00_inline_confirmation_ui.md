# Research – Inline Tool Confirmation UI

**Date:** 2025-12-04
**Owner:** agent
**Phase:** Research

## Goal

Research the current modal-based tool confirmation system and identify how to replace it with inline keybinding-based confirmation directly in the main UI.

## User Request Summary

The user wants to:
- **Remove the modal popup** for tool confirmation
- **Show inline options** in the main component (RichLog)
- Display something like: `[1] Yes  [2] Yes + Skip  [3] No`
- Keep the existing keybindings working without the modal overlay

## Current Implementation

### Key Files

| File | Purpose |
|------|---------|
| `src/tunacode/ui/screens/confirmation.py` | Modal screen for tool confirmation |
| `src/tunacode/ui/app.py` | Main app, modal integration at lines 188-205 |
| `src/tunacode/types.py` | `ToolConfirmationRequest/Response` dataclasses |

### Current Flow (Modal-Based)

1. Agent needs tool confirmation → `build_textual_tool_callback()` (app.py:272-289)
2. Creates `ToolConfirmationRequest` (line 284)
3. Calls `app.request_tool_confirmation()` (line 285)
4. App posts `ShowToolConfirmationModal` message and awaits future (lines 194-196)
5. Handler pushes modal screen via `push_screen()` (line 199)
6. **Modal overlays the entire UI** with buttons and checkbox
7. User presses `1`, `2`, or `3` → action method triggers
8. Modal posts `ToolConfirmationResult` message and pops itself
9. App receives result via `on_tool_confirmation_result()` (line 201)
10. Future is resolved, agent continues

### Current Keybindings (in Modal)

```python
# src/tunacode/ui/screens/confirmation.py:32-37
BINDINGS = [
    Binding("1", "approve", "Yes"),
    Binding("2", "approve_skip", "Yes + Skip"),
    Binding("3", "reject", "No"),
    Binding("escape", "reject", "Cancel", show=False),
]
```

## Proposed Solution

### Inline Confirmation Approach

Instead of pushing a modal screen, show the confirmation prompt **inline in the RichLog** and handle keypresses at the app level.

#### Visual Design

```
┌─────────────────────────────────────────────────────────┐
│ ⚙ Confirm: write_file                                  │
│   filepath: /home/user/project/file.py                  │
│                                                         │
│   [1] Yes   [2] Yes (skip future)   [3] No              │
└─────────────────────────────────────────────────────────┘
```

Or simpler:
```
⚙ write_file → /home/user/project/file.py
  [1] Yes  [2] Yes + Skip  [3] No
```

### Implementation Strategy

#### 1. Modify `request_tool_confirmation()` (app.py:188-196)

**Before:**
```python
async def request_tool_confirmation(self, request: ToolConfirmationRequest) -> ToolConfirmationResponse:
    self.pending_confirmation = asyncio.Future()
    self.post_message(ShowToolConfirmationModal(request=request))
    return await self.pending_confirmation
```

**After:**
```python
async def request_tool_confirmation(self, request: ToolConfirmationRequest) -> ToolConfirmationResponse:
    self.pending_confirmation = asyncio.Future()
    self._pending_confirmation_request = request
    self._show_inline_confirmation(request)  # Write to RichLog instead
    return await self.pending_confirmation
```

#### 2. Add Inline Display Method

```python
def _show_inline_confirmation(self, request: ToolConfirmationRequest) -> None:
    from rich.text import Text

    prompt = Text()
    prompt.append(f"\n⚙ Confirm: ", style="yellow bold")
    prompt.append(f"{request.tool_name}\n", style="cyan")
    prompt.append(f"  {request.args}\n", style="dim")
    prompt.append("  [1] Yes  ", style="green")
    prompt.append("[2] Yes + Skip  ", style="blue")
    prompt.append("[3] No\n", style="red")

    self.rich_log.write(prompt)
```

#### 3. Add App-Level Keybindings for Confirmation

```python
# In TextualReplApp.BINDINGS
BINDINGS = [
    Binding("ctrl+p", "toggle_pause", ...),
    Binding("escape", "cancel_stream", ...),
    Binding("1", "confirm_yes", show=False),
    Binding("2", "confirm_skip", show=False),
    Binding("3", "confirm_no", show=False),
]
```

#### 4. Add Action Methods

```python
def action_confirm_yes(self) -> None:
    if self.pending_confirmation and not self.pending_confirmation.done():
        response = ToolConfirmationResponse(approved=True, skip_future=False, abort=False)
        self.pending_confirmation.set_result(response)
        self.pending_confirmation = None

def action_confirm_skip(self) -> None:
    if self.pending_confirmation and not self.pending_confirmation.done():
        response = ToolConfirmationResponse(approved=True, skip_future=True, abort=False)
        self.pending_confirmation.set_result(response)
        self.pending_confirmation = None

def action_confirm_no(self) -> None:
    if self.pending_confirmation and not self.pending_confirmation.done():
        response = ToolConfirmationResponse(approved=False, skip_future=False, abort=True)
        self.pending_confirmation.set_result(response)
        self.pending_confirmation = None
```

#### 5. Remove Modal Pieces (Cleanup)

- Remove `ShowToolConfirmationModal` message class
- Remove `on_show_tool_confirmation_modal()` handler
- Keep `on_tool_confirmation_result()` for backward compat or remove
- Modal file `confirmation.py` can be deleted or deprecated

## Files to Modify

| File | Action |
|------|--------|
| `src/tunacode/ui/app.py` | Add inline display + app-level keybindings |
| `src/tunacode/ui/screens/confirmation.py` | **DELETE** (no longer needed) |
| `src/tunacode/ui/screens/__init__.py` | Remove exports |

## Edge Cases to Handle

1. **Key conflicts**: `1`, `2`, `3` might conflict with editor input
   - Solution: Only bind when `pending_confirmation` is set
   - Or use `priority=True` and check state in action methods

2. **Escape key**: Currently bound to cancel stream AND reject confirmation
   - Solution: Check if confirmation pending first, then fall back to cancel stream

3. **Visual feedback**: After user responds, clear/update the confirmation prompt
   - Append "[Approved]" or "[Rejected]" after response

## Alternative Designs

### Option A: StatusBar Prompt
Show confirmation in StatusBar instead of RichLog:
```
[StatusBar: ⚙ write_file | [1] Yes [2] Skip [3] No]
```
- Pro: Non-intrusive
- Con: Less visible, limited space

### Option B: Dedicated Confirmation Widget
Create a slim confirmation bar widget between RichLog and Editor:
- Pro: Clear separation
- Con: More complex layout changes

### Option C: Editor Placeholder
Change editor placeholder during confirmation:
```
placeholder = "[1] Yes  [2] Yes+Skip  [3] No  (write_file)"
```
- Pro: Focus stays on editor
- Con: Loses original placeholder, less space for details

## Recommendation

**Go with inline RichLog display** (main proposal above):
- Keeps conversation flow intact
- Shows full context (tool name, args)
- Simple implementation
- Keybindings `1`, `2`, `3` feel natural

## Knowledge Gaps

- Need to verify `1`, `2`, `3` keybindings don't interfere with editor input when focused
- May need conditional binding activation based on `pending_confirmation` state

## References

- `src/tunacode/ui/app.py` - Main app implementation
- `src/tunacode/ui/screens/confirmation.py` - Current modal (to be removed)
- `src/tunacode/types.py:80-95` - Request/Response dataclasses
