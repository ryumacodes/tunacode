---
id: tun-c4ab
status: in_progress
deps: []
links: []
created: 2026-01-27T22:05:40Z
type: task
priority: 2
assignee: tunahorse1
tags: [typing, mypy, batch1]
---
# Batch 1: mypy typing hygiene

Add missing return/argument/variable annotations in low-risk modules per PLAN.md Batch 1. Scope only: ripgrep.py, retry.py, gitignore.py, settings.py, paths.py, grep.py, glob.py, bash.py, core/state.py. No behavior changes.


## Notes

**2026-01-27T22:09:16Z**

Batch 1 edits: added type annotations in ripgrep, retry, gitignore, settings, paths, grep, glob, bash, core/state. No behavior changes.

**2026-01-27T22:12:02Z**

Batch 1 verification: mypy passed for batch files after fixing gitignore patterns typing and grep task creation.
