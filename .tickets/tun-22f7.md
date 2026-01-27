---
id: tun-22f7
status: closed
deps: [tun-d150]
links: []
created: 2026-01-27T20:25:10Z
type: task
priority: 2
parent: tun-c2f8
tags: [lsp, reimplementation]
---
# Update update_file to call LSP diagnostics


## Notes

**2026-01-27T20:25:14Z**

Update update_file tool to automatically fetch LSP diagnostics after updating.

Changes to tools/update_file.py:
- Import get_diagnostics from tools.lsp
- After successful update, call get_diagnostics(filepath)
- Append formatted diagnostics to result string

Agent receives: File updated message + diff + diagnostics section
Agent decides: Fix errors, ignore them, or continue editing

Acceptance: update_file returns diagnostics when LSP enabled
