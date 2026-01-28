---
id: tun-c36f
status: closed
deps: [tun-5a52]
links: []
created: 2026-01-26T22:46:17Z
type: task
priority: 2
assignee: tunahorse1
tags: [deletion, cleanup, constants]
---
# Remove research constants, config, and template refs

Remove ToolName.RESEARCH_CODEBASE from constants.py, settings.py, tool_dispatcher.py, agent_helpers.py. Remove RESEARCH_TEMPLATE from templates.py and prompting __init__.py

## Acceptance Criteria

ToolName.RESEARCH_CODEBASE raises AttributeError, RESEARCH_TEMPLATE not exported, ruff passes

