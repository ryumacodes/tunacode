---
id: tun-83f5
status: closed
deps: []
links: []
created: 2026-01-26T21:16:43Z
type: task
priority: 2
assignee: tunahorse1
tags: [ui, dependencies]
---
# Fix UI->exceptions dependency violations

UI imports from tunacode.exceptions are now disallowed. Current count: 2 (e.g. tunacode.ui.repl_support -> tunacode.exceptions). Route through core.

