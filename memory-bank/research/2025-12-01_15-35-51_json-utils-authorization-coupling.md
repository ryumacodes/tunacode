# Research - JSON Utils Authorization Coupling Issue

**Date:** 2025-12-01
**Owner:** agent
**Phase:** Research
**Git Commit:** 96297f2

## Goal

Analyze the architectural violation where `validate_tool_args_safety` in `parsing/json_utils.py` makes authorization decisions by importing `READ_ONLY_TOOLS` from application constants.

## Findings

### The Problem

**File:** `src/tunacode/utils/parsing/json_utils.py:91-128`

A JSON parsing utility is making authorization decisions:

```python
# json_utils.py:11
from tunacode.constants import READ_ONLY_TOOLS

# json_utils.py:111
if tool_name and tool_name in READ_ONLY_TOOLS:
    logger.info(f"Multiple JSON objects for read-only tool {tool_name} - allowing execution")
    return True
```

### Why This Is Problematic

| Issue | Impact |
|-------|--------|
| **Wrong layer** | Parsing should parse. Security decisions belong in security/authorization layer |
| **Tight coupling** | A general-purpose parsing module depends on application-specific tool classifications |
| **Hidden security logic** | Someone auditing security would look in `security/command.py`, not JSON utilities |
| **Untestable in isolation** | Testing requires full constants module and tool categorization understanding |

### Relevant Files & Why They Matter

| File | Purpose |
|------|---------|
| `src/tunacode/utils/parsing/json_utils.py` | Problematic file - parsing with embedded auth |
| `src/tunacode/constants.py:63-72` | Defines `READ_ONLY_TOOLS`, `WRITE_TOOLS`, `EXECUTE_TOOLS` |
| `src/tunacode/core/tool_authorization.py` | Proper location for authorization decisions |
| `src/tunacode/core/tool_handler.py` | Facade for authorization system |
| `src/tunacode/utils/security/command.py` | Command injection prevention (clean separation) |

### Current READ_ONLY_TOOLS Usage Map

| Location | Line | Purpose | Appropriate? |
|----------|------|---------|--------------|
| `constants.py` | 63-70 | Definition | Yes |
| `tool_authorization.py` | 337 | `is_read_only_tool()` auth helper | Yes |
| `tool_authorization.py` | 126-136 | `ReadOnlyToolRule` class | Yes |
| `node_processor.py` | 272 | Tool categorization for parallel exec | Yes |
| `agents/utils.py` | 136, 170 | Tool batching for performance | Yes |
| **`json_utils.py`** | **111** | **Safety validation during parsing** | **NO** |

### Dead Constants Discovery

`WRITE_TOOLS` and `EXECUTE_TOOLS` are defined in `constants.py:71-72` but **never imported or used in any Python source file**. They only appear in documentation.

## Key Patterns / Solutions Found

### Pattern 1: Strategy Injection (Recommended)

The authorization system already uses clean patterns that could be applied here:

```python
# tool_authorization.py uses Protocol pattern
class AuthorizationRule(Protocol):
    def should_allow_without_confirmation(self, tool_name: str, context: AuthContext) -> bool: ...
```

**Solution:** Inject a `safety_checker` callback into `validate_tool_args_safety`:

```python
# json_utils.py (refactored)
def validate_tool_args_safety(
    objects: List[Dict[str, Any]],
    tool_name: Optional[str] = None,
    is_safe_for_multiple: Optional[Callable[[str], bool]] = None  # Injected
) -> bool:
    if len(objects) <= 1:
        return True

    if is_safe_for_multiple and tool_name:
        if is_safe_for_multiple(tool_name):
            logger.info(f"Multiple JSON objects for tool {tool_name} - allowed by policy")
            return True
    # ... rest unchanged
```

### Pattern 2: Move to Authorization Layer

Alternative: Move `validate_tool_args_safety` entirely to `tool_authorization.py` since it's fundamentally an authorization decision.

### Pattern 3: Tool Registry Pattern

The codebase has hints of a tool registry in `schema_assembler.py:131`:

```python
safe_tools = ["read_file", "list_dir", "grep", "glob"]  # Hardcoded duplicate!
```

This is another instance of the same problem - tool categorization is scattered.

## Existing Security Architecture (Reference)

The codebase has a **clean authorization architecture** that json_utils.py bypasses:

```
Tool Execution Flow:
1. Agent creates tool calls
2. Node processor categorizes by READ_ONLY_TOOLS (node_processor.py:272)
3. Callback authorizes via ToolHandler.should_confirm() (textual_repl.py:291)
4. AuthorizationPolicy evaluates rules (tool_authorization.py:217-235)
5. Tool executes

The PROBLEM: json_utils.py short-circuits step 3-4 by making its own decision
```

## Knowledge Gaps

1. **Why was this pattern introduced?** Need to check git history for the rationale
2. **Who calls `safe_json_parse` with `allow_concatenated=True`?** Need usage analysis
3. **Can concatenated JSON objects ever reach write tools?** Need flow analysis to understand attack surface
4. **Is `validate_tool_args_safety` dead code?** Need to verify it's actually called in production paths

## Recommended Refactoring Approach

### Phase 1: Decouple (Low Risk)

1. Add optional `is_safe_for_multiple` callback to `validate_tool_args_safety`
2. Default to `None` (strict behavior - reject multiple objects for unknown tools)
3. Wire callers to inject `is_read_only_tool` from `tool_authorization.py`
4. Remove `READ_ONLY_TOOLS` import from `json_utils.py`

### Phase 2: Consolidate Tool Categorization

1. Create single source of truth for tool categorization
2. Remove duplicate `safe_tools` list from `schema_assembler.py:131`
3. Consider deleting unused `WRITE_TOOLS` and `EXECUTE_TOOLS` constants

### Phase 3: Audit All Security Decisions

1. Grep for `READ_ONLY_TOOLS`, `WRITE_TOOLS`, `EXECUTE_TOOLS` usage
2. Ensure all security decisions flow through `tool_authorization.py`
3. Document security boundaries in architecture docs

## References

- `/root/tunacode/src/tunacode/utils/parsing/json_utils.py` - Problematic file
- `/root/tunacode/src/tunacode/constants.py` - Tool categorization constants
- `/root/tunacode/src/tunacode/core/tool_authorization.py` - Proper auth location
- `/root/tunacode/src/tunacode/core/tool_handler.py` - Authorization facade
- `/root/tunacode/src/tunacode/utils/security/command.py` - Clean security module
- `/root/tunacode/src/tunacode/core/agents/agent_components/node_processor.py` - Tool categorization for execution
- `/root/tunacode/src/tunacode/tools/schema_assembler.py:131` - Another hardcoded tool list

## Summary

The `validate_tool_args_safety` function in `json_utils.py` violates separation of concerns by:
1. Importing application-specific constants (`READ_ONLY_TOOLS`) into a parsing utility
2. Making authorization decisions (what's "safe") outside the authorization layer
3. Creating hidden security logic that's hard to audit
4. Coupling parsing to tool categorization, preventing reuse

The fix should inject a callback or move the function to the authorization layer, keeping `json_utils.py` as pure parsing logic.
