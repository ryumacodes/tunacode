---
id: tun-c3c4
status: in_progress
deps: []
links: []
created: 2026-01-27T22:12:00Z
type: task
priority: 2
assignee: tunahorse1
tags: [typing, mypy, batch3]
---
# Batch 3: protocol/interface mismatches

Resolve StateManagerProtocol vs StateManager usage in src/tunacode/core/agents/main.py and orchestrator callback argument mismatches in src/tunacode/core/agents/agent_components/orchestrator/orchestrator.py per PLAN.md Batch 3. No behavior changes.


## Notes

**2026-01-27T22:24:50Z**

Updated agent_components to use StateManagerProtocol (agent_config, streaming, orchestrator, tool_dispatcher), expanded SessionStateProtocol with missing fields, and aligned tool_result_callback call to positional signature. Updated message_recorder/usage_tracker to accept SessionStateProtocol. Mypy passes for touched files.
