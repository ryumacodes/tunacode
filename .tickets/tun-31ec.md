---
id: tun-31ec
status: closed
deps: []
links: []
created: 2026-01-27T22:59:43Z
type: task
priority: 2
assignee: tunahorse1
parent: tun-33a8
tags: [ui, app, streaming]
---
# Refactor app.py to ChatContainer

Replace RichLog + streaming_output with ChatContainer, simplify streaming callback, and update user/tool/error/system output paths.

## Acceptance Criteria

app.py composes ChatContainer; RichLog/streaming_output removed; streaming uses chat API; tool panels still render.

