---
id: tun-7fd3
status: in_progress
deps: []
links: []
created: 2026-01-27T22:11:57Z
type: task
priority: 2
assignee: tunahorse1
tags: [typing, mypy, batch2]
---
# Batch 2: optional handling & assignment mismatches

Fix None-attribute access in src/tunacode/tools/ignore.py and assignment mismatch in src/tunacode/tools/utils/ripgrep.py per PLAN.md Batch 2. No behavior changes.


## Notes

**2026-01-27T22:14:59Z**

Fixed None-attribute access in tools/ignore.py with early return when cache entry present. Ran mypy on ignore.py and utils/ripgrep.py: no issues found; ripgrep assignment mismatch not reproducible with current file/state.
