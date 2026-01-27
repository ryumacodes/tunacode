---
id: tun-5f58
status: closed
deps: [tun-27ea]
links: []
created: 2026-01-27T19:22:32Z
type: task
priority: 1
tags: [issue-314, indexing, cleanup]
---
# Clean glob.py, state.py, ui/app.py after indexing deletion

Remove CodeIndex import and optimization from tools/glob.py (delete _get_code_index, _glob_with_index). Remove indexing_service property from core/state.py. Delete _run_startup_index() from ui/app.py.

## Acceptance Criteria

grep CodeIndex src/tunacode/ returns empty; grep IndexingService src/tunacode/ returns empty; app starts without indexing


## Notes

**2026-01-27T19:28:26Z**

Completed in commit 611bda11
