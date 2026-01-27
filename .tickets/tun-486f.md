---
id: tun-486f
status: closed
deps: [tun-c2f8]
links: []
created: 2026-01-27T20:18:42Z
type: task
priority: 1
parent: tun-c2f8
tags: [lsp, removal]
---
# Delete src/tunacode/lsp/ directory


## Notes

**2026-01-27T20:18:45Z**

Remove the entire src/tunacode/lsp/ directory including:
- __init__.py (unused exports get_diagnostics, format_diagnostics)
- client.py (LSPClient class, no callers)
- servers.py (server command mapping)

Acceptance: Directory deleted, no imports reference tunacode.lsp
