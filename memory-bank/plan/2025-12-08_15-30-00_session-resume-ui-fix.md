---
title: "Session Resume UI Fix - Plan"
phase: Plan
date: "2025-12-08T15:30:00"
owner: "agent"
parent_research: "memory-bank/research/2025-12-08_session-resume-ui-bug.md"
git_commit_at_plan: "9a4915a"
tags: [plan, session-resume, ui-bug, P0]
---

## Goal

**Fix the session resume display bug:** When a session loads, render the conversation history to the UI so users see their previous messages.

**Non-Goals:**
- Session picker screen (P1, separate PR)
- Command rename `/sessions` -> `/resume` (P1, separate PR)
- Visual distinction for restored messages (P2, later)
- Pagination for large sessions (future)

## Scope & Assumptions

**In Scope:**
- Add `_replay_session_messages()` method to `app.py`
- Call replay method after `load_session()` in commands
- Display user and agent messages from history

**Out of Scope:**
- Tool result panels (require stored args/results - not available)
- Internal thought messages (skip silently)
- Performance optimization for large sessions

**Assumptions:**
- Messages are correctly deserialized (confirmed via analysis)
- `RichLog.write()` handles appending correctly
- Existing display patterns work for restored content

## Deliverables (DoD)

| Deliverable | Acceptance Criteria |
|-------------|---------------------|
| `_replay_session_messages()` method | Renders user + agent messages from `session.messages` |
| Updated `/sessions load` command | Calls replay after `load_session()` succeeds |
| Visual output | Users see conversation history after loading session |

## Readiness (DoR)

- [x] Research complete with file locations and patterns
- [x] Message extraction utility exists (`message_utils.py`)
- [x] Display patterns documented (inline in `app.py`)
- [x] State loading works correctly (`state.py:318-362`)

## Milestones

| # | Milestone | Description |
|---|-----------|-------------|
| M1 | Core Fix | Add `_replay_session_messages()` to `app.py` |
| M2 | Integration | Update `/sessions load` to call replay |
| M3 | Verification | Manual test of session load/display |

## Work Breakdown (Tasks)

### T1: Add Message Replay Method (M1)

**Summary:** Create `_replay_session_messages()` in `TunacodeApp`

**Owner:** agent
**Dependencies:** None
**Target:** M1

**Files/Interfaces:**
- `src/tunacode/ui/app.py` - Add method after line ~325

**Implementation:**
```python
def _replay_session_messages(self) -> None:
    """Render loaded session messages to RichLog."""
    from tunacode.utils.messaging.message_utils import get_message_content
    from pydantic_ai.messages import ModelRequest, ModelResponse

    for msg in self.state_manager.session.messages:
        if isinstance(msg, dict) and "thought" in msg:
            continue  # Skip internal thoughts

        content = get_message_content(msg)
        if not content:
            continue

        if isinstance(msg, ModelRequest):
            # User message format
            user_block = Text()
            user_block.append(f"| {content}\n", style=STYLE_PRIMARY)
            user_block.append("| (restored)", style=f"dim {STYLE_PRIMARY}")
            self.rich_log.write(user_block)
        elif isinstance(msg, ModelResponse):
            # Agent message format
            self.rich_log.write(Text("agent:", style="accent"))
            self.rich_log.write(Markdown(content))
```

**Acceptance Tests:**
- Method exists and is callable
- Iterates `session.messages` without error
- Writes to `rich_log` for each message type

---

### T2: Update Session Load Command (M2)

**Summary:** Call `_replay_session_messages()` after successful load

**Owner:** agent
**Dependencies:** T1
**Target:** M2

**Files/Interfaces:**
- `src/tunacode/ui/commands/__init__.py` lines 244-255

**Implementation:**
After line 245 (`app.rich_log.clear()`), add:
```python
app._replay_session_messages()  # Render loaded messages
```

**Acceptance Tests:**
- `/sessions load <id>` displays previous conversation
- User messages appear with cyan pipe prefix
- Agent messages appear with "agent:" header

---

### T3: Manual Verification (M3)

**Summary:** Test full flow works end-to-end

**Owner:** agent
**Dependencies:** T2
**Target:** M3

**Steps:**
1. Start tunacode, create conversation with 2-3 exchanges
2. Note session ID via `/sessions list`
3. Exit and restart tunacode
4. Run `/sessions load <id>`
5. Verify: conversation history visible in UI

## Risks & Mitigations

| Risk | Impact | Likelihood | Mitigation | Trigger |
|------|--------|------------|------------|---------|
| Large sessions slow UI | Medium | Low | Future: add message limit | >100 messages |
| Tool calls render poorly | Low | High | Skip tool display for now | Accept limitation |
| Message type mismatch | High | Low | Use isinstance checks | Test with varied sessions |

## Test Strategy

**One Test:** Manual verification (T3) - no automated test for this UI behavior.

Rationale: UI message display is visual/integration-level. The underlying `load_session()` already works. Adding unit tests for Rich component rendering has low value vs complexity.

## References

- `memory-bank/research/2025-12-08_session-resume-ui-bug.md` - Root cause analysis
- `src/tunacode/ui/app.py:277-304` - Display patterns
- `src/tunacode/ui/commands/__init__.py:244-257` - Bug location
- `src/tunacode/utils/messaging/message_utils.py:6-29` - Content extraction

---

## Alternative Approach (Not Recommended)

**Option B: Event-driven replay**
- Emit `MessageDisplay` events for each loaded message
- Let existing handlers render them

**Why not:** Adds complexity. Messages would route through async event bus unnecessarily. Direct rendering is simpler and sufficient.

---

## Final Gate

| Item | Value |
|------|-------|
| Plan Path | `memory-bank/plan/2025-12-08_15-30-00_session-resume-ui-fix.md` |
| Milestones | 3 (Core Fix, Integration, Verification) |
| Tasks | 3 |
| Files to Modify | 2 (`app.py`, `commands/__init__.py`) |
| Risk Level | Low |

**Next Command:** `/ce-ex memory-bank/plan/2025-12-08_15-30-00_session-resume-ui-fix.md`
