---
title: Core Formatting Facade
path: src/tunacode/core/formatting.py
type: file
depth: 1
description: Core-layer access to shared formatting helpers
exports: [truncate_diagnostic_message]
seams: [M]
---

# Core Formatting Facade

## Purpose
Expose formatting helpers for UI rendering without direct utils imports.

## Key Functions

### truncate_diagnostic_message
Trims verbose diagnostic messages for compact display in the UI.

## Integration Points

- **ui/renderers/tools/diagnostics.py** - diagnostic line rendering
