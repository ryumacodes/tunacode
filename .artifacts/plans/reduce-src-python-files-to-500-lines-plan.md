---
title: Reduce src Python Files to 500 Lines or Less
link: reduce-src-python-files-to-500-lines
type: plan
ontological_relations:
  - relation: depends_on
    target: dependency-layer-rules
    note: Refactors must preserve architecture boundaries enforced by tests.
  - relation: informed_by
    target: file-length-baseline-2026-03-17
    note: Baseline counts from wc -l scan of src/*.py.
  - relation: validated_by
    target: ci-and-architecture-gates
    note: Changes must pass pytest, lint, and architecture checks.
tags:
  - refactor
  - maintainability
  - code-health
  - file-size
  - architecture
created_at: 2026-03-17T11:04:19-05:00
updated_at: 2026-03-17T11:04:19-05:00
uuid: f383340a-29e0-4a07-b539-2128899feec2
---

# Goal
Reduce each `src/` Python file that is over 500 lines to **500 lines or fewer** while preserving behavior, test coverage, and architecture constraints.

## Current files above 500 lines
- `src/tunacode/core/agents/main.py` — 729 lines
- `src/tunacode/ui/app.py` — 625 lines
- `src/tunacode/core/agents/agent_components/agent_config.py` — 548 lines
- `src/tunacode/ui/renderers/panels.py` — 542 lines
- `src/tunacode/core/compaction/controller.py` — 534 lines

## Plan
1. **Stabilize baseline**
   - Run tests and lint once before refactoring.
   - Capture line-count baseline and key behavior expectations.

2. **Refactor one file at a time**
   - For each oversized file:
     - Identify cohesive sections (helpers, view logic, parsing, state transitions, adapters).
     - Extract into focused modules in the same layer/package.
     - Keep public APIs stable where possible.
     - Update imports and type hints.

3. **Validate after each file split**
   - Run targeted tests for touched modules.
   - Run architecture/import-order tests to ensure layer compliance.
   - Re-check line counts to confirm file is now <= 500.

4. **Final verification**
   - Run full test suite, lint, and architecture gates.
   - Confirm no new exemptions or rule bypasses were added.

## Implementation rules
- Do not change runtime behavior unless explicitly intended and documented.
- Prefer small extraction commits over broad rewrites.
- Keep module responsibilities clear and single-purpose.
- Preserve dependency-layer constraints:
  - `types -> utils -> infrastructure -> configuration -> tools -> core -> ui`

## Done criteria
- Every Python file in `src/` is **<= 500 lines**.
- Tests, lint, and architecture checks pass.
- Documentation and module maps are updated if structure changes.
