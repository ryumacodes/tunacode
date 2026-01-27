---
id: tun-27ea
status: closed
deps: []
links: []
created: 2026-01-27T19:22:21Z
type: task
priority: 1
tags: [issue-314, indexing, deletion]
---
# Delete indexing/ module and core/indexing_service.py

Delete entire src/tunacode/indexing/ directory (code_index.py, constants.py, __init__.py). Delete src/tunacode/core/indexing_service.py. This removes ~620 lines of premature optimization.

## Acceptance Criteria

indexing/ dir deleted; core/indexing_service.py deleted; no import errors


## Notes

**2026-01-27T19:26:21Z**

Completed in commit 802712ac
