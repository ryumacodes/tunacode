---
id: tun-a55b
status: closed
deps: []
links: []
created: 2026-01-26T21:16:30Z
type: task
priority: 2
assignee: tunahorse1
tags: [ui, dependencies]
---
# Fix UI->constants dependency violations

UI imports from tunacode.constants are now disallowed. Current count: 24 (e.g. tunacode.ui.renderers.tools.glob -> tunacode.constants). Route through core.

