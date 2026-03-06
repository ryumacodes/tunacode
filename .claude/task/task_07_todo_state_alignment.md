---
title: "Task 07: Todo State Alignment"
type: task
created_at: 2026-03-06T05:18:58Z
updated_at: 2026-03-06T05:18:58Z
uuid: 22c1a005-1d86-4f59-a6e4-4e115237bcd8
---

# Task 07: Todo State Alignment

## Summary
Todo items are represented as generic dictionaries with no explicit lifecycle semantics, creating inconsistent task status tracking across the session lifecycle.

## Context
`src/tunacode/core/state.py` stores todos as `list[dict[str, Any]]`. Typed `TodoItem` and `TodoStatus` are available in `src/tunacode/types/canonical.py` but are not referenced by runtime state.

## Related Docs
- [PLAN.md](../../PLAN.md)
- [Architecture Refactor Status Research](../../memory-bank/research/2026-01-25_architecture-refactor-status.md)
