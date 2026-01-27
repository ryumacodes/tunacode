---
id: tun-f757
status: closed
deps: []
links: []
created: 2026-01-26T21:16:36Z
type: task
priority: 2
assignee: tunahorse1
tags: [ui, dependencies]
---
# Fix UI->types dependency violations

UI imports from tunacode.types are now disallowed. Current count: 6 (e.g. tunacode.ui.widgets.messages -> tunacode.types). Route through core.

