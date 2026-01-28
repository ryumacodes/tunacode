---
id: tun-795f
status: closed
deps: []
links: []
created: 2026-01-28T19:22:04Z
type: task
priority: 2
assignee: tunahorse1
---
# Remove unused read_file/command constants

Delete unused constants for read_file size/messages and bash output truncation and JSON parse retries now duplicated in tools.

## Acceptance Criteria

constants.py no longer defines read_file size/message constants, command output truncation constants, or JSON parse retry constants.


## Notes

**2026-01-28T19:22:44Z**

Context: read_file, bash, and command_parser now define local constants to reduce entropy surface; constants.py duplicates are now dead code and should be removed to avoid drift.

**2026-01-28T19:23:24Z**

Note: This is a temporary solution. We understand the drift risk but are prioritizing larger issues; as a side OSS project we don't have time for smaller fixes right now.
