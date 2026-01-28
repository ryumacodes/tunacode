---
id: tun-ef47
status: closed
deps: []
links: []
created: 2026-01-27T22:52:18Z
type: bug
priority: 2
assignee: tunahorse1
tags: [tools, grep, coupling]
---
# Grep: remove private _use_python_fallback access

Avoid reaching into RipgrepExecutor._use_python_fallback; expose a public capability flag or method and use that instead.

