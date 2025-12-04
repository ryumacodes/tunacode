---
title: "Permission Modal Key Bindings – Plan"
phase: Plan
date: "2025-12-04T13:30:00Z"
owner: "Claude Agent"
parent_research: "memory-bank/research/2025-12-04_permission_modal_keybindings.md"
git_commit_at_plan: "c0cc378"
tags: [plan, ui, keybindings, modal, textual]
---

## Goal

Add keyboard-driven interaction to the tool confirmation modal so users can approve/reject tools without using a mouse.

**Singular focus:** Implement key bindings `1`, `2`, `3`, `Escape` for the permission modal.

**Non-goals:**
- No new widgets (keep existing layout)
- No feedback input field (future scope)
- No refactoring of authorization logic

## Scope & Assumptions

**In scope:**
- Add `BINDINGS` attribute to `ToolConfirmationModal`
- Add action methods for each binding
- Ensure keyboard navigation works immediately when modal appears

**Out of scope:**
- Adding Input widget for user feedback on rejection
- Changing the visual layout of the modal
- Modifying authorization handler logic

**Assumptions:**
- Textual's `ModalScreen` supports key bindings out of the box
- Current button/checkbox UI remains for mouse users
- Key `2` triggers both "Yes" and "skip future" in one action

## Deliverables (DoD)

| Artifact | Acceptance Criteria |
|----------|---------------------|
| `ui/screens/confirmation.py` | Has `BINDINGS` with 4 entries: `1`, `2`, `3`, `escape` |
| Key `1` | Approves tool, `skip_future=False` |
| Key `2` | Approves tool, `skip_future=True` |
| Key `3` | Rejects tool, `abort=True` |
| Key `Escape` | Rejects tool, `abort=True` (same as `3`) |
| Manual test | Pressing `1`, `2`, `3` works without mouse |

## Readiness (DoR)

- [x] Research doc exists and is current
- [x] Code location identified: `src/tunacode/ui/screens/confirmation.py`
- [x] Textual binding pattern documented in research
- [x] No pending changes to confirmation.py in git

## Milestones

| ID | Milestone | Description |
|----|-----------|-------------|
| M1 | Add Bindings | Add `BINDINGS` class attribute with 4 keys |
| M2 | Add Actions | Implement 4 action methods |
| M3 | Test | Manual test of all key bindings |
| M4 | Commit | Single atomic commit |

## Work Breakdown (Tasks)

| ID | Task | Owner | Est | Deps | Milestone |
|----|------|-------|-----|------|-----------|
| T1 | Add `Binding` import from textual.binding | Agent | 1m | - | M1 |
| T2 | Define `BINDINGS` list with 4 entries | Agent | 2m | T1 | M1 |
| T3 | Implement `action_approve()` for key 1 | Agent | 2m | T2 | M2 |
| T4 | Implement `action_approve_skip()` for key 2 | Agent | 2m | T2 | M2 |
| T5 | Implement `action_reject()` for keys 3 and escape | Agent | 2m | T2 | M2 |
| T6 | Manual test: run app, trigger write tool, test keys | Agent | 3m | T3-T5 | M3 |
| T7 | Commit with message | Agent | 1m | T6 | M4 |

### Task Acceptance Tests

**T1-T2 (Add Bindings):**
- `Binding` is imported from `textual.binding`
- `BINDINGS` contains entries for `"1"`, `"2"`, `"3"`, `"escape"`

**T3 (action_approve):**
- Creates `ToolConfirmationResponse(approved=True, skip_future=False, abort=False)`
- Posts `ToolConfirmationResult` message
- Pops screen

**T4 (action_approve_skip):**
- Creates `ToolConfirmationResponse(approved=True, skip_future=True, abort=False)`
- Posts `ToolConfirmationResult` message
- Pops screen

**T5 (action_reject):**
- Creates `ToolConfirmationResponse(approved=False, skip_future=False, abort=True)`
- Posts `ToolConfirmationResult` message
- Pops screen

**T6 (Manual test):**
- Modal appears when write tool is requested
- Pressing `1` approves and modal closes
- Pressing `2` approves + adds to ignore list, modal closes
- Pressing `3` or `Escape` rejects and modal closes

### Files/Interfaces Touched

| File | Change |
|------|--------|
| `src/tunacode/ui/screens/confirmation.py` | Add import, BINDINGS, 3 action methods |

## Risks & Mitigations

| Risk | Impact | Likelihood | Mitigation | Trigger |
|------|--------|------------|------------|---------|
| Key binding conflicts with Textual globals | Medium | Low | Use specific keys (1,2,3) unlikely to conflict | Modal doesn't respond |
| Modal loses focus on open | High | Low | Ensure modal is focused on push | Keys don't work |

## Test Strategy

**ONE manual test only:**
1. Run `tunacode`
2. Request a write operation (e.g., ask to create a file)
3. Modal appears
4. Test each key: `1`, `2`, `3`, `Escape`
5. Verify correct behavior for each

No automated test required for this UI change.

## Alternative Approach (NOT selected)

**Option B: Full UI redesign with Input widget**
- Would add text input for rejection feedback
- More complex, requires async input handling
- Deferred to future iteration

## References

- Research: `memory-bank/research/2025-12-04_permission_modal_keybindings.md`
- File: `src/tunacode/ui/screens/confirmation.py:28-60`
- Textual docs: Binding pattern

---

## Final Gate

- **Plan path:** `memory-bank/plan/2025-12-04_13-30-00_permission_modal_keybindings.md`
- **Milestones:** 4
- **Gates:** Manual test before commit
- **Next command:** `/context-engineer:execute "memory-bank/plan/2025-12-04_13-30-00_permission_modal_keybindings.md"`
