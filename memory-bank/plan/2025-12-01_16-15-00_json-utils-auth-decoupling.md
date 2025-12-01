---
title: "JSON Utils Authorization Decoupling - Plan"
phase: Plan
date: "2025-12-01T16:15:00"
owner: "agent"
parent_research: "memory-bank/research/2025-12-01_15-35-51_json-utils-authorization-coupling.md"
git_commit_at_plan: "96297f2"
tags: [plan, refactoring, authorization, decoupling]
---

## Goal

**Singular Focus:** Decouple `json_utils.py` from application-specific authorization constants by injecting a callback, and fix the broken tool_name wiring so the safety check actually works.

**Non-goals:**
- Moving `validate_tool_args_safety` to a different module (scope creep)
- Refactoring the entire authorization system
- Adding new authorization rules

## Scope & Assumptions

**In Scope:**
- Remove `READ_ONLY_TOOLS` import from `json_utils.py`
- Add optional `is_safe_for_multiple` callback parameter
- Wire `tool_name` through the call chain (textual_repl -> parse_args -> safe_json_parse)
- Fix `schema_assembler.py` hardcoded safe_tools list
- Delete dead `WRITE_TOOLS` and `EXECUTE_TOOLS` constants

**Out of Scope:**
- Changes to the core `AuthorizationPolicy` or rule system
- Performance optimizations in agents/utils.py or node_processor.py

**Assumptions:**
- The codebase has test coverage for json parsing (verify via existing tests)
- No external callers depend on `WRITE_TOOLS`/`EXECUTE_TOOLS` (verified: only in constants.py)

## Deliverables (DoD)

| Artifact | Acceptance Criteria |
|----------|---------------------|
| `json_utils.py` refactored | No `READ_ONLY_TOOLS` import; callback-based safety check |
| `command_parser.py` updated | Accepts and passes `tool_name` parameter |
| `textual_repl.py` wired | Passes `part.tool_name` to `parse_args()` |
| `schema_assembler.py` fixed | Uses `READ_ONLY_TOOLS` constant instead of hardcoded list |
| `constants.py` cleaned | `WRITE_TOOLS` and `EXECUTE_TOOLS` deleted |
| Tests pass | `hatch run test` green |

## Readiness (DoR)

- [x] Research document complete with file locations and line numbers
- [x] Current git state clean (96297f2)
- [x] Call chain mapped: textual_repl.py:297 -> parse_args -> safe_json_parse -> validate_tool_args_safety
- [x] `is_read_only_tool()` exists at tool_authorization.py:328-338 (ready for injection)

## Milestones

| ID | Name | Gate |
|----|------|------|
| M1 | Core Refactor | json_utils.py no longer imports READ_ONLY_TOOLS |
| M2 | Wire Call Chain | tool_name flows from textual_repl through to validation |
| M3 | Consolidate Constants | schema_assembler.py and constants.py cleaned up |
| M4 | Validation | All tests pass, ruff clean |

## Work Breakdown (Tasks)

### M1: Core Refactor

| Task | Summary | Files/Interfaces | Dependencies |
|------|---------|------------------|--------------|
| T1.1 | Add `is_safe_for_multiple: Optional[Callable[[str], bool]]` param to `validate_tool_args_safety` | `json_utils.py:91` | None |
| T1.2 | Replace `tool_name in READ_ONLY_TOOLS` with callback invocation | `json_utils.py:111` | T1.1 |
| T1.3 | Remove `READ_ONLY_TOOLS` import | `json_utils.py:11` | T1.2 |
| T1.4 | Add `is_safe_for_multiple` param to `safe_json_parse` and wire through | `json_utils.py:136` | T1.1 |

**Acceptance Tests:**
- `validate_tool_args_safety(objs, "read_file", lambda x: True)` returns True for multi-object
- `validate_tool_args_safety(objs, "bash", lambda x: False)` raises ConcatenatedJSONError
- No import of `READ_ONLY_TOOLS` in json_utils.py

### M2: Wire Call Chain

| Task | Summary | Files/Interfaces | Dependencies |
|------|---------|------------------|--------------|
| T2.1 | Add `tool_name: Optional[str]` param to `parse_args` | `command_parser.py:20` | None |
| T2.2 | Pass `tool_name` to `safe_json_parse` call | `command_parser.py:49` | T2.1 |
| T2.3 | Import `is_read_only_tool` in command_parser.py | `command_parser.py` | T1.3 |
| T2.4 | Pass callback to `safe_json_parse` | `command_parser.py:49` | T2.3 |
| T2.5 | Pass `part.tool_name` at call site | `textual_repl.py:297` | T2.1 |

**Acceptance Tests:**
- `parse_args(args, tool_name="read_file")` passes tool_name through chain
- Authorization decision uses `is_read_only_tool` from tool_authorization.py

### M3: Consolidate Constants

| Task | Summary | Files/Interfaces | Dependencies |
|------|---------|------------------|--------------|
| T3.1 | Import `READ_ONLY_TOOLS` in schema_assembler.py | `schema_assembler.py` | None |
| T3.2 | Replace hardcoded `safe_tools` with `READ_ONLY_TOOLS` check | `schema_assembler.py:131` | T3.1 |
| T3.3 | Delete `WRITE_TOOLS` constant | `constants.py:71` | None |
| T3.4 | Delete `EXECUTE_TOOLS` constant | `constants.py:72` | T3.3 |

**Acceptance Tests:**
- `schema_assembler.py` includes `react` and `research_codebase` as safe tools
- No `WRITE_TOOLS` or `EXECUTE_TOOLS` in codebase

### M4: Validation

| Task | Summary | Files/Interfaces | Dependencies |
|------|---------|------------------|--------------|
| T4.1 | Run `ruff check --fix .` | All modified files | M1-M3 |
| T4.2 | Run `hatch run test` | Test suite | T4.1 |
| T4.3 | Commit with focused diff | Git | T4.2 |

## Risks & Mitigations

| Risk | Impact | Likelihood | Mitigation | Trigger |
|------|--------|------------|------------|---------|
| Breaking existing tests | Medium | Low | Run tests after each milestone | Test failure |
| External callers of dead constants | Low | Very Low | Grep verified no usage | Import error |
| Callback signature mismatch | Medium | Low | Use same signature as `is_read_only_tool()` | Type error |

## Test Strategy

**Single focused test:** Add one test case to verify the callback injection works:

```python
def test_validate_tool_args_safety_with_callback():
    """Verify callback-based authorization works."""
    objects = [{"a": 1}, {"b": 2}]

    # Callback returns True -> should allow
    assert validate_tool_args_safety(objects, "read_file", lambda x: True) is True

    # Callback returns False -> should raise
    with pytest.raises(ConcatenatedJSONError):
        validate_tool_args_safety(objects, "bash", lambda x: False)
```

## References

- Research doc: `memory-bank/research/2025-12-01_15-35-51_json-utils-authorization-coupling.md`
- `src/tunacode/utils/parsing/json_utils.py:91-128` - Target function
- `src/tunacode/core/tool_authorization.py:328-338` - Callback source
- `src/tunacode/cli/command_parser.py:20-66` - Call chain entry
- `src/tunacode/cli/textual_repl.py:297` - Wire point
- `src/tunacode/tools/schema_assembler.py:131` - Hardcoded list
- `src/tunacode/constants.py:71-72` - Dead constants

## Alternative Approach

**Option B (Not recommended):** Move `validate_tool_args_safety` entirely to `tool_authorization.py`. This would require more extensive refactoring and is not necessary since the callback pattern cleanly decouples the modules.

---

## Summary

- **Plan path:** `memory-bank/plan/2025-12-01_16-15-00_json-utils-auth-decoupling.md`
- **Milestones:** 4 (Core Refactor, Wire Call Chain, Consolidate Constants, Validation)
- **Gates:** Tests pass at each milestone, ruff clean
- **Next command:** `/ce-ex "memory-bank/plan/2025-12-01_16-15-00_json-utils-auth-decoupling.md"`
