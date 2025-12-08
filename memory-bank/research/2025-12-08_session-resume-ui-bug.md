# Research - Session Resume UI Bug

**Date:** 2025-12-08
**Owner:** agent
**Phase:** Research

## Goal

Investigate why loading a session doesn't restore chat history in the UI, and document required fixes for proper session resume with NeXTSTEP-inspired UX.

## Findings

### The Critical Bug

When a session is loaded, the message history is restored to backend state but **never displayed in the chat UI**:

1. `state.py:318-362` - `load_session()` correctly populates `session.messages` with full history
2. `commands/__init__.py:245` - `app.rich_log.clear()` clears the display
3. `commands/__init__.py:254` - Only writes "Session loaded" confirmation
4. **GAP: No code renders historical messages from `session.messages` to `rich_log`**

### Relevant Files

| File | Purpose |
|------|---------|
| `src/tunacode/core/state.py:318-362` | Session loading - works correctly, populates `session.messages` |
| `src/tunacode/core/state.py:224-275` | Serialization/deserialization of messages |
| `src/tunacode/ui/commands/__init__.py:184-288` | `/sessions` command - clears UI but doesn't restore |
| `src/tunacode/ui/app.py:289-304` | User message display format |
| `src/tunacode/ui/app.py:277-280` | Agent response display format |
| `src/tunacode/ui/app.py:317-325` | Tool result display format |
| `src/tunacode/utils/messaging/message_utils.py:6-29` | `get_message_content()` - can extract text from any message type |

### Data Flow Analysis

**Session Save (works):**
```
user message → append to session.messages → serialize to JSON → write to disk
```

**Session Load (broken UI):**
```
read JSON → deserialize → populate session.messages → clear UI → write "loaded" → STOP
                                                                              ↑
                                                       MISSING: render messages to rich_log
```

### Message Types in `session.messages`

From pydantic-ai, messages have structure:
- `ModelRequest` (kind="request") - User/system prompts with `parts[]`
- `ModelResponse` (kind="response") - Agent responses with text content
- `dict` with `{"thought": "..."}` - Internal reasoning (custom format)
- Tool calls embedded as `ToolCallPart` and `ToolReturnPart`

## Key Patterns / Solutions Found

### Pattern 1: Message Content Extraction Exists

`utils/messaging/message_utils.py:get_message_content()` already handles all message types:
```python
def get_message_content(message: Any) -> str:
    if isinstance(message, dict):
        if "content" in message: return str(message["content"])
        if "thought" in message: return str(message["thought"])
    if hasattr(message, "parts"): # handles ModelRequest/ModelResponse
        return extract from parts
```

### Pattern 2: Display Formats Are Established

Current live display patterns:
- **User:** `Text()` with cyan pipe prefix, timestamp
- **Agent:** `Text("agent:")` + `Markdown(content)`
- **Tool:** `Panel()` via `tool_panel_smart()`

### Pattern 3: No Bulk Restore Pattern Exists

- `RichLog` only has `write()` for appending, `clear()` for reset
- No pagination or message limiting
- No visual distinction between restored vs new messages

## Proposed Implementation

### Fix 1: Add Message Replay Function

Add to `app.py`:
```python
def _replay_session_messages(self) -> None:
    """Render loaded session messages to RichLog."""
    for msg in self.state_manager.session.messages:
        if is_request(msg):  # User message
            text = extract_user_prompt(msg)
            self._write_user_message(text, restored=True)
        elif is_response(msg):  # Agent response
            text = extract_response_content(msg)
            self._write_agent_message(text, restored=True)
        elif is_thought(msg):
            pass  # Skip internal thoughts
```

### Fix 2: Update Session Load Command

In `commands/__init__.py:244-257`, change:
```python
if app.state_manager.load_session(target_session["session_id"]):
    app.rich_log.clear()
    app._replay_session_messages()  # NEW: render history
    app._update_resource_bar()
```

### Fix 3: UX Improvements

1. **Rename command:** `/sessions` -> `/resume`
2. **Add session picker screen:** `SessionResumeScreen` with Textual best practices
3. **Visual distinction:** Dim styling for restored messages vs bright for new

## Knowledge Gaps

1. **Performance:** Unknown limit for `RichLog` before degradation
2. **Tool Results:** Restoring full tool panels requires storing args/results in session
3. **Thoughts:** Decision needed on whether to display on restore
4. **Large Sessions:** May need pagination or limit (e.g., last 50 messages)

## Implementation Checklist

- [ ] Create `_replay_session_messages()` method in `app.py`
- [ ] Add message type detection helpers (is_request, is_response)
- [ ] Add content extraction helpers for display
- [ ] Update `/sessions load` to call replay function
- [ ] Add visual distinction for restored messages (dim style)
- [ ] Rename `/sessions` to `/resume`
- [ ] Create `SessionResumeScreen` with Textual patterns
- [ ] Add startup check for previous sessions to offer resume

## References

- `src/tunacode/core/state.py` - Session state management
- `src/tunacode/ui/app.py` - Main TUI and message display
- `src/tunacode/ui/commands/__init__.py` - Session commands
- `src/tunacode/utils/messaging/message_utils.py` - Message utilities
- `memory-bank/research/2025-12-08_session-persistence.md` - Prior session research
- `memory-bank/research/2025-12-04_14-07-20_tui_message_differentiation.md` - Message types
