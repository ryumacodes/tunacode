---
id: tun-32f0
status: closed
deps: []
links: []
created: 2026-01-27T23:36:51Z
type: task
priority: 1
assignee: tunahorse1
tags: [ui, agent-panel]
---
# Remove duration from agent panel

Remove the duration display from the agent response panel. Currently shown as '245ms' or '1.2s' in the status bar. The panel should still show model name, tokens, and t/s.

## Acceptance Criteria

- Duration no longer appears in agent panel status bar
- Model, tokens, and t/s still displayed
- render_agent_response function updated

