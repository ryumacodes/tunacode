---
id: tun-970b
status: closed
deps: []
links: []
created: 2026-01-26T21:16:34Z
type: task
priority: 2
assignee: tunahorse1
tags: [ui, dependencies]
---
# Fix UI->utils dependency violations

UI imports from tunacode.utils are now disallowed. Current count: 11 (e.g. tunacode.ui.screens.setup -> tunacode.utils.config). Route through core.

