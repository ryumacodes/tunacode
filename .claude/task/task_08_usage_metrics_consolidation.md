---
title: "Task 08: Usage Metrics Consolidation"
type: task
created_at: 2026-03-06T05:18:58Z
updated_at: 2026-03-06T05:18:58Z
uuid: f99bc665-7a0e-4e56-a024-082111553c81
---

# Task 08: Usage Metrics Consolidation

## Summary
Usage tracking relies on ad hoc dictionary structures and duplicates totals across multiple fields. This makes metric definitions inconsistent and complicates reporting.

## Context
`src/tunacode/core/state.py` stores `last_call_usage` and `session_total_usage` as dicts with repeated fields. Canonical `UsageMetrics` exists in `src/tunacode/types/canonical.py`, and `TokenUsage` and `CostBreakdown` exist in `src/tunacode/types/dataclasses.py`, but production usage remains untyped.

## Related Docs
- [PLAN.md](../../PLAN.md)
- [Architecture Refactor Status Research](../../memory-bank/research/2026-01-25_architecture-refactor-status.md)
