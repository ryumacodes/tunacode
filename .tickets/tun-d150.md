---
id: tun-d150
status: closed
deps: [tun-486f, tun-d9c6]
links: []
created: 2026-01-27T20:19:01Z
type: task
priority: 2
parent: tun-c2f8
tags: [lsp, reimplementation]
---
# Create tools/lsp/ sub-package for LSP client


## Notes

**2026-01-27T20:19:05Z**

Create nested tools/lsp/ package for LSP client infrastructure.

This is an implementation detail within the tools layer (not a top-level layer).

Files:
- tools/lsp/__init__.py
- tools/lsp/client.py (LSPClient from old lsp/client.py)
- tools/lsp/servers.py (server command mapping)

Acceptance: Package created, imports work within tools/

**2026-01-27T20:24:56Z**

DESIGN UPDATE: tools.lsp provides get_diagnostics() for file tools

Package structure:
- tools/lsp/__init__.py: exports get_diagnostics, format_diagnostics
- tools/lsp/client.py: LSPClient (JSON-RPC implementation)
- tools/lsp/servers.py: server command mapping

Usage in file tools:


Dependencies:
tools.write_file → tools.lsp (same layer, valid)
