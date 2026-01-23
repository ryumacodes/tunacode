# Research - Submit Tool Permission Issue

**Date:** 2026-01-19
**Owner:** agent
**Phase:** Research

## Goal

Investigate why the `submit` tool asks for user permission when it should auto-execute when the agent is ready to submit its answer.

## Findings

### Root Cause

The `submit` tool is **not classified as a read-only tool** in `constants.py`, causing the authorization system to require user confirmation.

**Relevant files:**

| File | Why it matters |
|------|----------------|
| `src/tunacode/constants.py:80-89` | Defines `READ_ONLY_TOOLS` list - `ToolName.SUBMIT` is missing |
| `src/tunacode/tools/authorization/rules.py:25-32` | `ReadOnlyToolRule` allows tools in `READ_ONLY_TOOLS` to execute without confirmation |
| `src/tunacode/tools/submit.py` | The submit tool implementation - purely returns a string, no side effects |

### Current State

```python
# constants.py:80-89
READ_ONLY_TOOLS = [
    ToolName.READ_FILE,
    ToolName.GREP,
    ToolName.LIST_DIR,
    ToolName.GLOB,
    ToolName.REACT,
    ToolName.RESEARCH_CODEBASE,
    ToolName.WEB_FETCH,
    ToolName.PRESENT_PLAN,
]
# ToolName.SUBMIT is MISSING
```

### Authorization Flow

1. Agent calls `submit` tool
2. `ReadOnlyToolRule.should_allow_without_confirmation()` checks if tool is in `READ_ONLY_TOOL_NAMES`
3. `submit` is NOT in that set, so returns `False`
4. No other rule grants auto-approval
5. System prompts user for confirmation

## Key Patterns / Solutions Found

**Fix:** Add `ToolName.SUBMIT` to `READ_ONLY_TOOLS` in `constants.py`:

```python
READ_ONLY_TOOLS = [
    ToolName.READ_FILE,
    ToolName.GREP,
    ToolName.LIST_DIR,
    ToolName.GLOB,
    ToolName.REACT,
    ToolName.RESEARCH_CODEBASE,
    ToolName.WEB_FETCH,
    ToolName.PRESENT_PLAN,
    ToolName.SUBMIT,  # ADD THIS
]
```

**Justification for auto-approval:**
1. `submit` performs no file writes
2. `submit` executes no shell commands
3. `submit` has no side effects - it just returns a confirmation string
4. The tool's purpose is to signal task completion - requiring permission defeats the UX goal
5. `PRESENT_PLAN` is already auto-approved and has similar "signaling" semantics

## Knowledge Gaps

None - the fix is straightforward.

## References

- `src/tunacode/constants.py` - Tool classification constants
- `src/tunacode/tools/authorization/rules.py` - Authorization rule implementations
- `src/tunacode/tools/submit.py` - Submit tool implementation
- `src/tunacode/tools/prompts/submit_prompt.xml` - Tool prompt
