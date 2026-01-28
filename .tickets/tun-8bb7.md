---
id: tun-8bb7
status: closed
deps: []
links: []
created: 2026-01-28T19:22:08Z
type: task
priority: 2
assignee: tunahorse1
---
# Update docs after limit removal

Update docs/configuration README and utils-limits module doc to reflect removal of read_file limits and stale references.

## Acceptance Criteria

Docs no longer mention removed limits or point to stale files; examples updated as needed.


## Notes

**2026-01-28T19:22:48Z**

Context: docs currently mention read_limit/max_line_length and read_file usage; update to reflect intentional removal and keep docs in sync with current behavior.

**2026-01-28T19:23:24Z**

Note: This is a temporary solution. We understand the drift risk but are prioritizing larger issues; as a side OSS project we don't have time for smaller fixes right now.
