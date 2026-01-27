---
id: tun-2ddf
status: closed
deps: [tun-8218]
links: []
created: 2026-01-27T19:17:17Z
type: task
priority: 1
tags: [issue-314, architecture, lateral-coupling]
---
# Merge tools/lsp_status.py into core/lsp_status.py

Move get_lsp_status() logic from tools/lsp_status.py to core/lsp_status.py. Delete tools/lsp_status.py. Update any imports. This eliminates the tools→lsp lateral import for server status.

## Acceptance Criteria

tools/lsp_status.py deleted; grep 'from tunacode.lsp' tools/lsp_status.py returns no match; tests pass


## Notes

**2026-01-27T19:31:13Z**

Completed in commit b1ae6dc5
