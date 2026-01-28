---
id: tun-33a8
status: closed
deps: []
links: []
created: 2026-01-27T22:59:32Z
type: epic
priority: 2
assignee: tunahorse1
tags: [ui, refactor, streaming]
---
# Chat container refactor

Replace RichLog + streaming_output with ChatContainer/MessageWidget for in-place streaming.

## Acceptance Criteria

ChatContainer is used in app.py; RichLog and streaming_output removed; call sites migrated; CSS updated; validators run.

