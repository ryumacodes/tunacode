---
id: tun-c2f8
status: closed
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

**2026-01-27T20:19:32Z**

Phase 1 Acceptance Criteria:
- src/tunacode/lsp/ directory deleted
- core/lsp_status.py deleted
- tools/lsp_status.py deleted
- No references to tunacode.lsp in codebase
- UI works without LSP indicator

Phase 2 Acceptance Criteria:
- tools/lsp/ package created with client and servers
- tools/check_file.py tool implemented
- Tool registered in agent when LSP enabled
- Agent can request diagnostics via check_file tool

**2026-01-27T20:24:41Z**

DECISION 2026-01-27: Option 2 - Keep LSP in Tools Layer

LSP is a tools concern only. File tools (write_file, update_file) will:
1. Perform the file operation
2. Call tools.lsp.get_diagnostics(filepath) automatically
3. Append diagnostics to the result

Agent receives contextual feedback and decides what to do with it.

Dependencies:
- tools.write_file → tools.lsp (same layer, valid)
- tools.update_file → tools.lsp (same layer, valid)

No core changes needed. Clean, simple, explicit.

**2026-01-27T20:25:22Z**

UPDATED TICKET STRUCTURE:

Phase 1 - Removal:
- tun-486f: Delete src/tunacode/lsp/ directory
- tun-d9c6: Delete tools/lsp_status.py  
- tun-0db4: Delete core/lsp_status.py facade

Phase 2 - Reimplementation (Keep in Tools):
- tun-d150: Create tools/lsp/ sub-package
- tun-2d43: Update write_file to call LSP diagnostics
- tun-22f7: Update update_file to call LSP diagnostics

CLOSED (design changed):
- tun-3149: check_file tool (not needed)
- tun-2cd6: Tool registration (not needed)

**2026-01-27T20:27:57Z**

PHASE 1 COMPLETE: All LSP code removed

Commits:
- ba84e4c4: Delete src/tunacode/lsp/ directory (tun-486f)
- f75b8a89: Remove LSP status files and UI indicator (tun-d9c6, tun-0db4)

Deleted:
- src/tunacode/lsp/ (entire directory)
- src/tunacode/tools/lsp_status.py
- src/tunacode/core/lsp_status.py
- LSP indicator from UI resource bar

Ready for Phase 2: Reimplementation in tools layer.

**2026-01-27T20:30:58Z**

PHASE 2 COMPLETE: LSP reimplemented in tools layer

Commits:
- 5f2a0902: Create tools/lsp/ sub-package (tun-d150)
- ecda2c82: Add LSP diagnostics to write_file and update_file (tun-2d43, tun-22f7)

Architecture:
- tools/lsp/ provides get_diagnostics(), format_diagnostics()
- write_file and update_file call tools.lsp automatically
- Dependencies: tools -> tools.lsp (same layer, valid)

Flow:
1. Agent calls write_file/update_file
2. Tool writes/updates file
3. If LSP enabled in config, fetches diagnostics
4. Appends <file_diagnostics> block to result
5. Agent sees feedback and decides what to do

EPIC COMPLETE.
