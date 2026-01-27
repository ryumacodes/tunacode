---
id: tun-b0c3
status: in_progress
deps: []
links: []
created: 2026-01-27T22:29:41Z
type: task
priority: 2
assignee: tunahorse1
tags: [typing, mypy, batch5]
---
# Batch 5: coroutine/task API correctness

Fix coroutine/task API misuse in src/tunacode/tools/grep.py (task handling). Ensure mypy passes for grep module.


## Notes

**2026-01-27T22:29:58Z**

Verified grep task handling: search tasks created with asyncio.create_task; mypy passes for tools/grep.py. No code changes required in this batch.
