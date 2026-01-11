# Research - Register present_plan Tool (Issue 222)

**Date:** 2026-01-09
**Owner:** agent
**Phase:** Research

## Goal

Summarize all existing knowledge about registering the `present_plan` tool with the pydantic-ai agent when in plan mode, including cache invalidation concerns.

## Findings

### Primary Issue: Tool Never Registered

The `present_plan` tool exists but is **never registered** with any agent:

- `src/tunacode/tools/present_plan.py:32-102` - Factory function `create_present_plan_tool(state_manager)` exists
- `src/tunacode/core/agents/agent_components/agent_config.py:418-444` - Tool list assembly **omits** present_plan

**Evidence:** The tool list includes 12 tools:
- Core: `bash`, `glob`, `grep`, `list_dir`, `read_file`, `update_file`, `web_fetch`, `write_file`
- Delegation: `research_codebase`
- Task tracking: `todowrite`, `todoread`, `todoclear`
- **Missing**: `present_plan`

### Plan Mode Flow Analysis

**Command Execution** (`src/tunacode/ui/commands/__init__.py:194-228`):
1. User types `/plan`
2. `session.plan_mode = True` toggled at line 198
3. `plan_approval_callback` set on session at lines 202-205
4. System message injected listing `present_plan` as available (line 216)
5. **No agent cache invalidation occurs**

**Tool Execution** (`src/tunacode/tools/present_plan.py:45-93`):
1. Tool checks `session.plan_mode` at line 64
2. Retrieves callback via `getattr(session, "plan_approval_callback", None)` at line 68
3. Awaits user approval at line 72
4. Returns result message based on approval state

**The Problem**: Step 1 of Tool Execution never happens because the LLM doesn't see `present_plan` in its available tools.

### Cache Invalidation Analysis (Issue 222)

**Current Version Hash** (`agent_config.py:144-153`):
```python
def _compute_agent_version(settings, request_delay) -> int:
    return hash((
        str(settings.get("max_retries", 3)),
        str(settings.get("tool_strict_validation", False)),
        str(request_delay),
        str(settings.get("global_request_timeout", 90.0)),
    ))
```

**NOT included**: `plan_mode`, `yolo`, `tool_ignore`, `active_template`

**Why Cache Invalidation is NOT Required**:
1. `present_plan` should be registered **unconditionally** (always in tool list)
2. The tool handles mode checking internally (`if not session.plan_mode: return error`)
3. Plan mode blocking uses runtime authorization (`PlanModeBlockRule` at `rules.py:72-87`)
4. All tools registered once, authorization decides availability at runtime

### Related Files

| File | Purpose |
|------|---------|
| `src/tunacode/tools/present_plan.py` | Tool definition with factory function |
| `src/tunacode/tools/prompts/present_plan_prompt.xml` | XML prompt template |
| `src/tunacode/core/agents/agent_components/agent_config.py` | Agent creation, tool registration |
| `src/tunacode/ui/commands/__init__.py:169-228` | Plan command and mode instruction |
| `src/tunacode/tools/authorization/rules.py:72-87` | PlanModeBlockRule |
| `src/tunacode/core/state.py:52-55` | Session state (plan_mode, plan_approval_callback) |

## Key Patterns / Solutions Found

- **Factory pattern**: `create_present_plan_tool(state_manager)` follows same pattern as `create_todowrite_tool`, `create_research_codebase_tool`
- **Signature preservation**: Line 100 preserves `__signature__` for pydantic-ai schema generation
- **Runtime authorization**: `PlanModeBlockRule.evaluate()` blocks write/execute tools at runtime, not registration time
- **Callback injection**: UI sets `session.plan_approval_callback`, tool consumes it

## Implementation Approach

### Fix Location
`src/tunacode/core/agents/agent_components/agent_config.py`

### Changes Required

**1. Add import** (around line 38):
```python
from tunacode.tools.present_plan import create_present_plan_tool
```

**2. Register tool** (after todo tools, around line 444):
```python
# Add present_plan tool for plan mode workflow
present_plan = create_present_plan_tool(state_manager)
tools_list.append(Tool(present_plan, max_retries=max_retries, strict=tool_strict_validation))
```

### Why This Works

1. Tool is always registered (LLM always sees it)
2. Tool checks `session.plan_mode` internally and returns error if not in plan mode
3. No cache invalidation needed - tool availability doesn't change with mode
4. Matches existing pattern for todo tools and research_codebase tool

### Cache Invalidation Verdict

**Not required** for this fix because:
- pydantic-ai agents have immutable tool lists
- Conditional tool availability achieved via runtime checks inside tool
- Authorization layer handles blocking at execution time
- `present_plan` works correctly outside plan mode (returns error message)

The issue title mentions cache invalidation as a concern, but the correct architecture is:
- Register all tools unconditionally
- Tools/authorization decide availability at runtime
- Cache invalidation only needed for configuration changes (max_retries, etc.)

## Knowledge Gaps

- No automated test verifying `present_plan` is in agent's tool list
- No integration test for full plan mode workflow
- `tests/test_present_plan.py` exists but coverage unknown

## References

- `memory-bank/research/2026-01-08_23-46-19_plan-permission-keeps-asking.md` - Prior research on plan approval flow
- `.claude/qa/no-cargo-cult-fixes.md` - Documents signature preservation requirement
- `src/tunacode/tools/todo.py:124-197` - Pattern for tool factory functions
