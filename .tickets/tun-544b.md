---
id: tun-544b
status: closed
deps: [tun-32f0]
links: []
created: 2026-01-27T23:36:51Z
type: chore
priority: 2
assignee: tunahorse1
tags: [ui, cleanup]
---
# Clean up unused duration-related code

Remove dead code related to duration that is no longer used. Includes: _format_duration() function, render_agent_streaming() function, and duration_ms parameter from render_agent_response(). Update all call sites.

## Acceptance Criteria

- _format_duration() function removed
- render_agent_streaming() function removed
- duration_ms parameter removed from render_agent_response()
- Call sites in app.py updated
- Unused elapsed_ms code cleaned up

