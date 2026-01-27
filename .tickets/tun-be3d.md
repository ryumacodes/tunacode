---
id: tun-be3d
status: closed
deps: [tun-2ddf]
links: []
created: 2026-01-27T19:17:26Z
type: task
priority: 2
tags: [issue-314, architecture, lateral-coupling]
---
# Remove LSP import from file_tool decorator

Remove lazy import of tunacode.lsp in _get_lsp_diagnostics() from tools/decorators.py. Add optional diagnostics_callback parameter to @file_tool decorator. Core will inject the LSP callback when appropriate.

## Acceptance Criteria

grep 'from tunacode.lsp' src/tunacode/tools/decorators.py returns empty; tests pass


## Notes

**2026-01-27T19:32:58Z**

Completed in commit 690c4760
