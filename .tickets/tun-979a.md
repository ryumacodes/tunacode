---
id: tun-979a
status: closed
deps: [tun-3f92]
links: []
created: 2026-01-27T06:20:44Z
type: task
priority: 1
tags: [architecture, types]
---
# Move 9 core-specific types to core/types/

Move ResponseState, AgentState, StateManagerProtocol, SessionStateProtocol, ConversationState, TaskState, RuntimeState, UsageState, ToolCallRegistry from types/ to core/types/

## Acceptance Criteria

All 9 types importable from tunacode.core.types

