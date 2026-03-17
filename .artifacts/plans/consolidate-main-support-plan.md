---
title: Audit main_support cutover needs (no implementation decisions)
type: plan
ontological_relations:
  - relation: depends_on
    target: agents-core-module
    note: Scope is limited to orchestrator support responsibilities in core/agents.
  - relation: informs
    target: utils-boundary-definition
    note: Audit output will identify what is truly utility vs orchestrator-local.
tags:
  - audit
  - refactor
  - code-health
  - scope-control
created_at: 2026-03-17T11:40:00-05:00
updated_at: 2026-03-17T17:35:00-05:00
uuid: 8a2f3b4c-5d6e-7f8a-9b0c-1d2e3f4a5b6c
---

# Goal
Map what **actually** needs to change after `main_support.py` removal.

This document is intentionally audit-only.
- No design proposals
- No relocation recommendations
- No implementation strategy

# Context
We are explicitly auditing responsibilities before any extraction/consolidation work.
Potential future utility-module work is out of scope for this document until this audit is complete.

# Current State Snapshot (as observed)
- `src/tunacode/core/agents/main.py` currently imports support symbols from `._main_support`.
- `src/tunacode/core/agents/_main_support.py` is not present.
- `main.py` directly reads max iterations via:
  - `session.user_config["settings"]["max_iterations"]`

# Audit Inventory

## Former main_support surface area

| Symbol | Kind | Current definition status | Current usage status | Notes to capture in audit |
|---|---|---|---|---|
| `EmptyResponseHandler` | class | Missing in current tree | Referenced by `main.py` | Track whether behavior is required vs removable |
| `coerce_runtime_config()` | function | Not used now | Not referenced | Confirm replacement path and whether any behavior was dropped |
| `coerce_tool_callback_args()` | function | Missing in current tree | Referenced by `main.py` | Track callback contract expectations |
| `log_tool_execution_end()` | function | Missing in current tree | Referenced by `main.py` | Track lifecycle log contract |
| `log_tool_execution_start()` | function | Missing in current tree | Referenced by `main.py` | Track lifecycle log contract |
| `normalize_tool_event_args()` | function | Missing in current tree | Referenced by `main.py` | Track event arg shape assumptions |
| `StreamLifecycleState` | protocol | Missing in current tree | Indirectly required by logging helpers | Track whether protocol typing is still needed |
| `_EmptyResponseStateView` | class | Missing in current tree | Indirect dependency of empty-response path | Track whether path remains in scope |
| `TOOL_EXECUTION_LIFECYCLE_PREFIX` | constant | Missing in current tree | Indirect via logging helpers | Track whether log text contract is externally relied upon |
| `PARALLEL_TOOL_CALLS_LIFECYCLE_PREFIX` | constant | Missing in current tree | Indirect via logging helpers | Track whether log text contract is externally relied upon |
| `DURATION_NOT_AVAILABLE_LABEL` | constant | Missing in current tree | Indirect via logging helpers | Track formatting expectations |

## Max-iterations configuration path (single-source audit)

| Concern | Observed source | Observed read path | Audit check |
|---|---|---|---|
| Main request loop iteration limit | `~/.config/tunacode.json` (`settings.max_iterations`) | `main.py` -> `_coerce_max_iterations(session)` -> `session.user_config["settings"]["max_iterations"]` | Verify no duplicate fallback/default remains in code paths |

# Read-Only Audit Checklist
1. Confirm every referenced symbol in `main.py` has a concrete definition (or record gap).
2. Map each symbol to: required runtime behavior, typing-only behavior, logging-only behavior, or removable behavior.
3. Record all call sites for each symbol and classify dependency criticality.
4. Confirm max-iterations path is singular and not duplicated by fallback constants/defaults.
5. Document layer ownership facts only (what is), not placement decisions (what should be).

# Audit Output Format (required)
For each symbol, record:
- `status`: present / missing / replaced
- `used_by`: explicit file+line references
- `behavioral_impact_if_missing`: none / low / medium / high
- `category`: orchestrator-local / cross-cutting utility / config-contract / logging-contract
- `decision_state`: needs follow-up / no action

# Done Criteria
- Complete inventory of all former `main_support` symbols with current status.
- Complete usage map for all currently referenced support symbols in `main.py`.
- Explicit single-source mapping for `max_iterations` documented and verified.
- No implementation recommendations in this document.
