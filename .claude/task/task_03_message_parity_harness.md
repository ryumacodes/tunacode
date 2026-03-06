---
title: "Task 03: Message Parity Harness"
type: task
created_at: 2026-03-06T05:18:58Z
updated_at: 2026-03-06T05:18:58Z
uuid: 126e3844-6c64-4499-9ce9-229beddb09e1
---

# Task 03: Message Parity Harness

## Summary
Parity validation between legacy message formats and canonical representations is incomplete. Without full parity coverage, there is limited confidence that adapter behavior matches real session data.

## Context
`tests/unit/types/test_adapter.py` includes limited parity checks and round-trip coverage, but `tests/parity/test_message_parity.py` does not exist. There is no validation against real historical session artifacts.

## Related Docs
- [PLAN.md](../../PLAN.md)
- [Architecture Refactor Status Research](../../memory-bank/research/2026-01-25_architecture-refactor-status.md)
