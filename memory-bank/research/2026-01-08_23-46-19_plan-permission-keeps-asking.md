# Research – Plan/Permission "Keeps Asking" Bug Report

**Date:** 2026-01-08
**Owner:** Claude Agent
**Phase:** Research

## Goal

Investigate user complaint: "hit 2 and it keeps asking" for plan approval and/or tool confirmation flows.

## Findings

### Root Cause Summary

**The "keeps asking" behavior for plan approval is EXPECTED BEHAVIOR, not a bug.** However, there are two issues:

1. **UX Design Issue**: Plan denial (key "2") triggers a revision loop by design, but users expect it to abort
2. **UX Inconsistency**: Key "2" means different things in different contexts

### Key Semantic Inconsistency

| Context | Key 1 | Key 2 | Key 3 |
|---------|-------|-------|-------|
| **Plan Approval** | Approve | Deny (revise loop) | *none* |
| **Tool Confirmation** | Yes | Yes + Skip Future | No (abort) |

**Users pressing "2" expect "No" behavior but get:**
- Plan approval: Revision loop (agent keeps trying)
- Tool confirmation: Approval + skip (tool executes!)

### File Analysis

#### Plan Approval Flow

**Entry Point:** `src/tunacode/ui/commands/__init__.py:190-228`
- `/plan` toggles `session.plan_mode`
- Sets `session.plan_approval_callback` to UI function

**Tool:** `src/tunacode/tools/present_plan.py:39-81`
- Calls `approval_callback(plan_content)`
- On denial: Returns `"Plan denied by user... Revise your plan and call present_plan again."`
- **Critical:** `session.plan_mode` stays `True` on denial (line 77 never executes)

**UI Handler:** `src/tunacode/ui/plan_approval.py:73-100`
```python
if event.key == "2":
    rich_log.write(Text("Plan denied - agent will revise", style=STYLE_ERROR))
    pending.future.set_result((False, "Please revise the plan based on my requirements."))
```

**Result:** Agent is explicitly told to revise and try again = infinite revision loop until user approves.

#### Tool Confirmation Flow

**UI Handler:** `src/tunacode/ui/app.py:573-586`
```python
elif event.key == "2":
    response = ToolConfirmationResponse(approved=True, skip_future=True, abort=False)
    self.rich_log.write(Text("Approved (skipping future)", style=STYLE_WARNING))
```

**Ignore List Update:** `src/tunacode/tools/authorization/handler.py:53-55`
```python
if response.skip_future:
    self.state.session.tool_ignore.append(tool_name)
```

**Secondary Issue - Parallel Tool Race Condition:**
- Read-only tools execute in parallel (`node_processor.py:424-435`)
- All check authorization simultaneously
- All see empty `tool_ignore` before user responds
- User's "Skip future" only helps AFTER current batch

## Key Patterns / Solutions Found

### Pattern 1: Revision Loop Design
- `present_plan.py:80-81` - Denial message explicitly instructs revision
- `session.plan_mode` only cleared on APPROVAL (line 77)
- **Intentional** iterative refinement loop

### Pattern 2: No Escape Mechanism for Plan Mode
- Plan approval only offers [1] Approve and [2] Deny
- No [3] Abort/Exit option
- User cannot cleanly exit plan mode without approving something

### Pattern 3: Race Condition Window
- `node_processor.py:424-435` - Parallel execution for read-only tools
- `repl_support.py:139` - Each callback checks auth independently
- No synchronization between parallel auth checks

## Knowledge Gaps

1. **User Intent:** Does user want "2" to abort entirely, or provide revision feedback?
2. **Parallel Tools:** How often do users encounter multiple simultaneous confirmations?
3. **Session State:** Is `tool_ignore` list persisting across sessions correctly?

## Recommended Fixes

### Fix 1: Add Abort Option to Plan Approval (HIGH PRIORITY)

Add key "3" or Escape to abort plan mode entirely:

```python
# plan_approval.py - Update actions zone
actions.append("[3]", style=f"bold {STYLE_WARNING}")
actions.append(" Exit Plan Mode")

# handle_plan_approval_key
if event.key == "3":
    rich_log.write(Text("Plan mode exited", style=STYLE_WARNING))
    pending.future.set_result((None, "abort"))  # Special signal
    # Caller must handle None as abort
```

### Fix 2: Harmonize Key Semantics (MEDIUM PRIORITY)

Option A: Match plan approval to confirmation
- Plan: [1] Approve, [2] Approve+Revise, [3] Deny/Exit

Option B: Match confirmation to plan approval
- Confirmation: [1] Yes, [2] No, [3] Yes+Skip

Option C: Use descriptive keys
- Plan: [A]pprove, [R]evise, [X] Exit
- Confirmation: [Y]es, [N]o, [S]kip future

### Fix 3: Sequential Auth Before Parallel Execution (LOW PRIORITY)

```python
# node_processor.py - Before parallel execution
# Collect all authorization decisions first
auth_results = []
for task in read_only_tasks:
    if tool_callback:
        await tool_callback(task.part, task.node)  # Sequential auth
    auth_results.append(True)

# Then execute in parallel
await execute_tools_parallel(read_only_tasks, None)  # No callback needed
```

## References

- `src/tunacode/ui/plan_approval.py` - Plan approval UI
- `src/tunacode/tools/present_plan.py` - Present plan tool
- `src/tunacode/ui/app.py:560-593` - Key event handling
- `src/tunacode/ui/commands/__init__.py:190-228` - /plan command
- `src/tunacode/tools/authorization/handler.py` - Tool auth handler
- `src/tunacode/core/agents/agent_components/node_processor.py:424-435` - Parallel execution
- `tests/test_plan_approval.py` - Test coverage
