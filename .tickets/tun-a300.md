---
id: tun-a300
status: closed
deps: []
links: []
created: 2026-01-26T21:16:40Z
type: task
priority: 2
assignee: tunahorse1
tags: [ui, dependencies]
---
# Fix UI->configuration dependency violations

UI imports from tunacode.configuration are now disallowed. Current count: 8 (e.g. tunacode.ui.screens.setup -> tunacode.configuration.models). Route through core.

