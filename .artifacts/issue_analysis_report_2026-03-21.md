# Issue Audit Update
**Audit Date:** 2026-03-21
**Repository:** `alchemiststudiosDOTai/tunacode`
**Audited Against:** local codebase + current GitHub issue state

## Summary
- **Open issues after audit:** 15
- **Issues closed during audit:** 1
- **Closed issue:** `#382`
- **Issues confirmed still open:** 14
- **Issues with partially stale issue text:** `#321`, `#393`, `#395`, `#412`

## Audit Outcome
| Issue | Status | Audit result |
| :--- | :--- | :--- |
| `#430` | Open | Still open. `src/tunacode/tools/decorators.py` remains in runtime use and test coverage. |
| `#426` | Open | Still open. File-length enforcement still diverges between pre-commit and direct script runs, and direct runs still scan outside first-party scope. |
| `#424` | Open | Still open. `Any` remains in multiple `src/` files named by the issue. |
| `#418` | Open | Still open. Workflows still reference `actions/checkout@v4` and `actions/setup-python@v5`. |
| `#413` | Open | Still open. Skills dataclass overlap and copy-forward transformations remain present. |
| `#412` | Open | Still open, but issue text is partially stale. Headless tests exist again, but the underlying implementation is still the same basic task/timeout flow. |
| `#411` | Open | Still open. Only the existing HTML fetch tool is present; no strategy-selecting browser-backed tool exists. |
| `#401` | Open | Still open. `/update` still emits static chat text without loading/viewport/status integration. |
| `#395` | Open | Still open, but issue text is partially stale. `/compact` now writes an immediate chat message, though the larger context-panel / viewport feedback problems remain. |
| `#393` | Open | Still open, but issue text is partially stale. Provider-call retry logic now exists; broader tool-execution retry/orchestrator behavior still does not. |
| `#388` | Open | Still open. The custom adapter layer and manual tool translation remain in place. |
| `#321` | Open | Still open, but issue text is partially stale. Some checklist items now exist (`deptry`, `todo_scanner`), while others (`CODEOWNERS`, `.env.example`) still do not. |
| `#303` | Open | Still open. Callback and tool boundary contracts remain broad and partially `Any`-typed. |
| `#276` | Open | Still open. The custom logging stack is still present under `src/tunacode/core/logging/`. |
| `#241` | Open | Still open. Iteration limits exist, but there is still no user-facing continue/stop checkpoint flow. |
| `#382` | Closed | Closed during audit. Forced manual compaction now uses a force-specific retention boundary path and has passing tests. |

## Notable Corrections To The Original Snapshot
- The original artifact treated `#382` as open; it is now closed.
- The original artifact implied the backlog had almost no recent discussion. That was true at generation time, but is no longer true after this audit because each remaining issue now has a fresh audit update comment.
- Several issue bodies were not fully wrong, but had drifted enough to need dated codebase context:
  - `#321`
  - `#393`
  - `#395`
  - `#412`

## Validation Notes
- Verified issue state with `gh issue list` / `gh issue view`.
- Verified code claims directly against `src/`, `tests/`, `.github/workflows/`, and project config files.
- Ran focused tests where closure depended on behavior:
  - `uv run pytest tests/unit/core/test_compaction_controller_outcomes.py -q`
  - `uv run pytest tests/unit/core/test_tinyagent_openrouter_model_config.py -q`

## Recommended Next Cleanup
1. Rewrite stale issue bodies for `#321`, `#393`, `#395`, and `#412` instead of only leaving audit comments.
2. Split mixed issues where the original title is still valid but part of the body is now obsolete.
3. Re-run backlog triage after any code changes that affect workflows, retries, or headless mode.
