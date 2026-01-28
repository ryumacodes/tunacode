---
id: tun-ea6b
status: closed
deps: []
links: []
created: 2026-01-27T22:59:49Z
type: task
priority: 2
assignee: tunahorse1
parent: tun-33a8
tags: [ui, commands, refactor]
---
# Migrate RichLog call sites

Update commands, welcome, logger callback, session replay, and shell output to use chat.add_message/clear.

## Acceptance Criteria

All rich_log.write/clear usages in commands/welcome/app are replaced with chat API.

