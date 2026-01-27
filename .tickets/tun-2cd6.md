---
id: tun-2cd6
status: closed
deps: [tun-3149]
links: []
created: 2026-01-27T20:19:17Z
type: task
priority: 2
parent: tun-c2f8
tags: [lsp, reimplementation]
---
# Register check_file tool in agent_config.py


## Notes

**2026-01-27T20:19:21Z**

Register check_file tool in agent tool list when LSP is enabled.

In agent_config.py get_or_create_agent(), add Tool(check_file, ...) to tools_list when user_config.settings.lsp.enabled is true.

Acceptance: Agent can see and use check_file tool when LSP enabled in config

**2026-01-27T20:24:51Z**

CLOSED: Design changed. No tool registration needed.

LSP is internal to file tools. write_file and update_file call it directly.
No changes to agent_config.py tool list.
