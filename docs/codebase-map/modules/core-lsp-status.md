---
title: Core LSP Status
path: src/tunacode/core/lsp_status.py
type: file
depth: 1
description: UI-facing facade for LSP status lookup
exports: [get_lsp_status]
seams: [M]
---

# Core LSP Status

## Purpose
Provide a core-layer entry point for UI components to query LSP enabled/server status without importing the LSP or tools layers directly.

## Key Functions

### get_lsp_status
Returns a tuple of (enabled, server_name_or_none) derived from user configuration and tool-layer LSP checks.

## Integration Points

- **ui/widgets/resource_bar.py** - displays LSP status in the resource bar
- **tools/lsp_status.py** - performs the actual LSP command lookup
