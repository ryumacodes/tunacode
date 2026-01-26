---
id: tun-18bc
status: closed
deps: [tun-4086]
links: []
created: 2026-01-26T23:25:59Z
type: task
priority: 1
assignee: tunahorse1
tags: [local-mode-removal agent]
---
# Remove local_mode from agent_config.py - full tool set only

Delete is_local_mode import. Remove conditional tool set logic (lines 369-396). Always use full tool set (9 tools) with standard descriptions. No 1-word descriptions for local mode.

## Acceptance Criteria

is_local_mode import deleted; conditional tool selection removed; full tool set always used; no short descriptions

