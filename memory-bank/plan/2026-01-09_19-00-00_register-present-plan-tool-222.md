---
title: "Register present_plan Tool – Plan"
phase: Plan
date: "2026-01-09T19:00:00"
owner: "agent"
parent_research: "memory-bank/research/2026-01-09_18-41-11_register-present-plan-tool-222.md"
git_commit_at_plan: "ee69308"
tags: [plan, present_plan, tool-registration, issue-222, coding]
---

## Goal

- Register `present_plan` tool with pydantic-ai agent so LLM can invoke it during plan mode workflow.

**Non-goals:**
- Cache invalidation changes (not required per research)
- Plan mode UI changes
- New authorization rules
- Deployment/observability

## Scope & Assumptions

**In scope:**
- Import `create_present_plan_tool` in agent_config.py
- Add tool to `tools_list`
- Verify tool appears in agent's available tools

**Out of scope:**
- Cache invalidation logic
- Authorization rule changes
- UI command changes

**Assumptions:**
- Factory function `create_present_plan_tool(state_manager)` works correctly
- Signature preservation already handled in present_plan.py:100
- Existing test at `tests/test_present_plan.py` covers tool behavior

## Deliverables

1. Modified `src/tunacode/core/agents/agent_components/agent_config.py` with present_plan registration
2. Test verifying present_plan is in agent's tool list

## Readiness

- [x] Factory function exists: `src/tunacode/tools/present_plan.py:32-102`
- [x] XML prompt exists: `src/tunacode/tools/prompts/present_plan_prompt.xml`
- [x] State manager passed to tool factory pattern established
- [x] Branch ready: `feat/register-present-plan-222`

## Milestones

- **M1**: Add import and register tool (core fix)
- **M2**: Add unit test verifying registration

## Work Breakdown (Tasks)

### Task 1: Add import statement

| Field | Value |
|-------|-------|
| ID | T1 |
| Summary | Import create_present_plan_tool in agent_config.py |
| Owner | agent |
| Estimate | trivial |
| Dependencies | none |
| Milestone | M1 |
| Files | `src/tunacode/core/agents/agent_components/agent_config.py` |
| Acceptance | Import statement present, no import errors |

**Code location:** Around line 38, near other tool imports

```python
from tunacode.tools.present_plan import create_present_plan_tool
```

### Task 2: Register present_plan tool

| Field | Value |
|-------|-------|
| ID | T2 |
| Summary | Add present_plan to tools_list |
| Owner | agent |
| Estimate | trivial |
| Dependencies | T1 |
| Milestone | M1 |
| Files | `src/tunacode/core/agents/agent_components/agent_config.py` |
| Acceptance | Tool in list, ruff check passes |

**Code location:** After todo tools registration, around line 444

```python
# Add present_plan tool for plan mode workflow
present_plan = create_present_plan_tool(state_manager)
tools_list.append(Tool(present_plan, max_retries=max_retries, strict=tool_strict_validation))
```

### Task 3: Add registration test

| Field | Value |
|-------|-------|
| ID | T3 |
| Summary | Test that present_plan appears in agent tool list |
| Owner | agent |
| Estimate | small |
| Dependencies | T2 |
| Milestone | M2 |
| Files | `tests/test_present_plan.py` |
| Acceptance | Test passes, verifies tool name in list |

**Test approach:** Mock state_manager, call tool assembly, verify "present_plan" in tool names.

## Risks & Mitigations

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Import path wrong | Low | Factory function verified in research |
| Signature not preserved | Low | Already handled at present_plan.py:100 |
| Tool strict validation fails | Low | Same pattern as other tools |

## Test Strategy

- **T3 acceptance test:** Verify present_plan in agent's tool list
- Existing `tests/test_present_plan.py` covers tool behavior

## References

- Research doc: `memory-bank/research/2026-01-09_18-41-11_register-present-plan-tool-222.md`
- Factory pattern: `src/tunacode/tools/todo.py:124-197`
- Tool registration: `src/tunacode/core/agents/agent_components/agent_config.py:418-444`
- Signature preservation: `src/tunacode/tools/present_plan.py:100`

## Final Gate

- **Plan path:** `memory-bank/plan/2026-01-09_19-00-00_register-present-plan-tool-222.md`
- **Milestone count:** 2
- **Task count:** 3
- **Tasks ready for coding:** T1, T2 (immediate), T3 (after T2)

**Next command:** `/ce:ex "memory-bank/plan/2026-01-09_19-00-00_register-present-plan-tool-222.md"`
