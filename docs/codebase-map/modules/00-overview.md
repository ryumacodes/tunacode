---
title: TunaCode Modules Overview
path: src/tunacode
type: directory
depth: 0
description: Root module structure for TunaCode CLI application
exports: [core, ui, tools, configuration, types, utils, lsp, prompts]
seams: [M, D]
---

# TunaCode Modules Overview

## Package Structure

The TunaCode CLI is organized into focused modules with clear responsibilities:

### Core Modules
- **core/** - Agent orchestration, state management, and prompt engineering
- **ui/** - Textual-based TUI interface
- **tools/** - Tool implementations

### Supporting Modules
- **configuration/** - User settings, model registry, and pricing
- **types/** - Type definitions and protocols
- **utils/** - Shared utilities (parsing, messaging)
- **lsp/** - Language Server Protocol client
- **prompts/** - Prompt template sections

## Module Dependencies

```
core/
  ├── configuration/ (user config)
  ├── types/ (data structures)
  ├── tools/ (agent capabilities)
  └── prompts/ (system prompts)

ui/
  ├── core/ (request processing)
  ├── tools/ (rendering)
  └── types/ (state management)

tools/
  ├── types/ (type definitions)
  └── utils/ (shared helpers)
```

## Design Principles

1. **Separation of Concerns** - Each module has a single, well-defined purpose
2. **Type Safety** - Extensive use of type hints and Pydantic models
3. **Async First** - All I/O operations are asynchronous
4. **Fail Fast** - Explicit error handling with custom exceptions
5. **NeXTSTEP UI** - Clean, uniform interface design philosophy
