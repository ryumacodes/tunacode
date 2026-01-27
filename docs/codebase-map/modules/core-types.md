---
title: Core Types Facade
path: src/tunacode/core/types.py
type: file
depth: 1
description: Core-layer exports for UI-facing types
exports: [ModelName, ToolArgs, ToolCallback, ToolName, ToolResultCallback, ToolStartCallback, UsageMetrics, UserConfig]
seams: [M]
---

# Core Types Facade

## Purpose
Expose shared type aliases and callback protocols from the core layer so UI modules do not import `tunacode.types` directly.

## Key Exports

- **ModelName** - model identifier type alias
- **ToolArgs / ToolName** - tool invocation typing
- **ToolCallback / ToolResultCallback / ToolStartCallback** - UI-facing callback protocols
- **UsageMetrics** - canonical usage tracking data
- **UserConfig** - user configuration structure

## Integration Points

- **ui/app.py** - model name typing
- **ui/repl_support.py** - tool callback signatures
- **ui/widgets/** - tool display message typing
- **ui/commands/__init__.py** - usage metrics display
