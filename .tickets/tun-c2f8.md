---
id: tun-c2f8
status: open
deps: []
links: []
created: 2026-01-27T20:18:34Z
type: epic
priority: 1
tags: [lsp, architecture, refactor]
---
# LSP Complete Removal and Tool-Only Reimplementation


## Notes

**2026-01-27T20:18:39Z**

Complete removal of dormant LSP infrastructure followed by clean reimplementation as tool-only layer.

Background: LSP diagnostics were removed from file_tool decorator in commit 690c4760 to fix dependency violations. The infrastructure still exists but is unused (zero callers to get_diagnostics).

Approach: Two-phase plan documented in PLAN.md
Phase 1: Complete removal of all LSP code
Phase 2: Reimplement as tools/check_file.py with nested tools/lsp/ package

Key design change: From automatic diagnostics (decorator) to explicit tool call (agent asks for diagnostics).
