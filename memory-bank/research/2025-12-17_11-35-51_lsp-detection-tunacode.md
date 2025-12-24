# Research - LSP Detection Integration for Tunacode

**Date:** 2025-12-17
**Owner:** Research Agent
**Phase:** Research
**Git Commit:** 5047a4e
**Last Updated:** 2025-12-17
**Last Updated Note:** Added decision discussion - simplified LSP over single-language linters

## Goal

Research how to integrate LSP (Language Server Protocol) detection into tunacode, taking inspiration from opencode's implementation. Understand tunacode's current architecture and identify optimal injection points for automatic diagnostic feedback to the AI agent.

## Findings

### Current Tunacode Architecture Overview

Tunacode uses **pydantic-ai** as its agent framework. Tools are wrapped with decorators, registered at agent creation, and executed through a parallel batching system. No LSP or diagnostic infrastructure currently exists.

### Relevant Files & Why They Matter

| File | Purpose |
|------|---------|
| `src/tunacode/tools/update_file.py` | Edit tool - primary target for LSP diagnostic injection |
| `src/tunacode/tools/write_file.py` | Write tool - secondary target for LSP diagnostics |
| `src/tunacode/tools/read_file.py` | Read tool - potential LSP warmup point (like opencode) |
| `src/tunacode/tools/decorators.py` | Tool decorators - `@file_tool`, `@base_tool` - injection point |
| `src/tunacode/tools/bash.py` | Subprocess pattern - reference for LSP process management |
| `src/tunacode/core/agents/agent_components/tool_executor.py` | Parallel tool execution - understand result flow |
| `src/tunacode/core/agents/agent_components/node_processor.py` | Tool result processing - callback injection point |
| `src/tunacode/ui/app.py:585-623` | `build_tool_result_callback()` - UI injection point |
| `src/tunacode/ui/renderers/tools/update_file.py` | Update file renderer - display injection point |
| `src/tunacode/configuration/defaults.py` | Default config - add LSP settings here |
| `src/tunacode/types.py` | Type definitions - add LSP types |

### Tool Execution Flow in Tunacode

```
1. Agent calls update_file tool
   |
2. Tool function decorated with @file_tool (decorators.py:59-96)
   |
3. File modified via text_match strategies
   |
4. Result returned to pydantic-ai
   |
5. Tool result stored in conversation messages
   |
6. Next iteration: tool_result_callback invoked (app.py:585-623)
   |
7. Renderer displays result (ui/renderers/tools/update_file.py)
```

### Three Injection Points for LSP Diagnostics

#### Option 1: Decorator Level (Affects LLM Input)
**Location:** `src/tunacode/tools/decorators.py:59-96`

```python
# In @file_tool decorator wrapper
async def wrapper(filepath: str, *args, **kwargs) -> R:
    result = await func(filepath, *args, **kwargs)
    if lsp_enabled():
        diagnostics = await LSP.diagnostics(filepath)
        if diagnostics:
            result += f"\n<file_diagnostics>\n{format_diagnostics(diagnostics)}\n</file_diagnostics>"
    return result
```

**Pros:**
- Diagnostics fed to LLM for immediate correction
- Follows opencode's pattern exactly
- Tight feedback loop

**Cons:**
- More invasive change
- Affects all file tools uniformly

#### Option 2: Renderer Level (Display Only)
**Location:** `src/tunacode/ui/renderers/tools/update_file.py`

**Pros:**
- Non-invasive to core execution
- Easy to toggle on/off
- Follows existing patterns

**Cons:**
- LLM doesn't see diagnostics
- Agent cannot self-correct in next turn

#### Option 3: Callback Level (Middle Ground)
**Location:** `src/tunacode/ui/app.py:585-623`

**Pros:**
- Central interception for all tools
- Can selectively augment specific tools

**Cons:**
- Result already stringified
- Mixes concerns

### Recommended Architecture (Based on Opencode)

To achieve opencode's behavior where diagnostics are automatically injected into tool outputs:

```
src/tunacode/
├── lsp/
│   ├── __init__.py          # LSP orchestrator (like opencode's index.ts)
│   ├── client.py            # LSP client implementation (JSON-RPC over stdin/stdout)
│   ├── servers.py           # Server definitions for Python, TypeScript, etc.
│   └── diagnostics.py       # Diagnostic formatting utilities
├── tools/
│   └── decorators.py        # Augment @file_tool to inject diagnostics
└── configuration/
    └── defaults.py          # Add LSP config section
```

### Key Differences from Opencode

| Aspect | Opencode | Tunacode |
|--------|----------|----------|
| Language | TypeScript | Python |
| Agent Framework | Custom | pydantic-ai |
| Edit Tool | `edit.ts` | `update_file.py` |
| JSON-RPC | vscode-jsonrpc | pygls or python-lsp-jsonrpc |
| Async | Node.js async | asyncio |

### Subprocess Management Pattern (from bash.py)

Tunacode already has robust subprocess patterns to follow:

```python
# bash.py pattern for LSP process spawning
process = await asyncio.create_subprocess_shell(
    command,
    stdout=asyncio.subprocess.PIPE,
    stderr=asyncio.subprocess.PIPE,
    cwd=cwd,
)
stdout, stderr = await asyncio.wait_for(
    process.communicate(),
    timeout=timeout_seconds
)
```

### Configuration Structure Recommendation

Add to `src/tunacode/configuration/defaults.py`:

```python
DEFAULT_USER_CONFIG: UserConfig = {
    "settings": {
        # ... existing settings
        "lsp": {
            "enabled": False,
            "servers": {
                "python": {
                    "command": ["pyright-langserver", "--stdio"],
                    "extensions": [".py"],
                },
                "typescript": {
                    "command": ["typescript-language-server", "--stdio"],
                    "extensions": [".ts", ".tsx", ".js", ".jsx"],
                },
            },
            "inject_in_tools": ["update_file", "write_file"],
            "max_diagnostics": 20,
            "severity_filter": ["error", "warning"],
            "debounce_ms": 150,
        },
    },
}
```

### Python LSP Library Options

| Library | Purpose | Notes |
|---------|---------|-------|
| `pygls` | LSP server/client framework | Most comprehensive |
| `python-lsp-jsonrpc` | Low-level JSON-RPC | Minimal, like vscode-jsonrpc |
| `pylsp` | Python language server | Could be default server |
| `pyright` | Static type checker | Best for type errors |

## Key Patterns / Solutions Found

| Pattern | Description | Location |
|---------|-------------|----------|
| **@file_tool decorator** | Wraps file tools with error handling | `decorators.py:59-96` |
| **Subprocess async** | Pattern for spawning/managing processes | `bash.py:67-76` |
| **Tool result callback** | Hook for post-processing tool results | `app.py:585-623` |
| **Parallel execution** | Batch tool execution with `asyncio.gather` | `tool_executor.py:44-101` |
| **Configuration hierarchy** | Defaults + user config merge | `defaults.py` + `state.py:126-156` |

## Knowledge Gaps

- **Python LSP client libraries:** Need to evaluate pygls vs python-lsp-jsonrpc for client use
- **Debounce implementation:** Python equivalent of opencode's 150ms debounce pattern
- **Server auto-download:** How to handle missing language servers (pyright, typescript-language-server)
- **Multi-project roots:** How to handle monorepo scenarios with multiple project roots
- **Testing strategy:** How to create a fake LSP server for testing (like opencode's fake-lsp-server.js)

## Implementation Phases (No Timeline Estimates)

### Phase 1: Core LSP Infrastructure
1. Create `src/tunacode/lsp/` module structure
2. Implement basic JSON-RPC client over stdin/stdout
3. Add server spawn/lifecycle management
4. Implement diagnostic collection with debounce

### Phase 2: Tool Integration
1. Modify `@file_tool` decorator to call LSP
2. Add diagnostic formatting utilities
3. Inject diagnostics into `update_file` and `write_file` outputs
4. Add `read_file` warmup (non-blocking)

### Phase 3: Configuration & UX
1. Add LSP settings to configuration
2. Add UI indicators for LSP status
3. Handle graceful degradation when servers unavailable
4. Add server definition for common languages

### Phase 4: Advanced Features
1. Multi-file diagnostic reporting (like opencode's write tool)
2. Server auto-download capability
3. Custom server configuration support
4. Workspace symbol search integration

## References

### Tunacode Files
- `src/tunacode/tools/update_file.py` - Edit tool implementation
- `src/tunacode/tools/write_file.py` - Write tool implementation
- `src/tunacode/tools/decorators.py` - Tool decorators
- `src/tunacode/tools/bash.py` - Subprocess patterns
- `src/tunacode/core/agents/agent_components/tool_executor.py` - Tool execution
- `src/tunacode/configuration/defaults.py` - Configuration defaults

### Opencode Reference (External)
- `packages/opencode/src/lsp/index.ts` - LSP orchestrator
- `packages/opencode/src/lsp/client.ts` - LSP client
- `packages/opencode/src/lsp/server.ts` - Server definitions
- `packages/opencode/src/tool/edit.ts` - Edit tool LSP integration

### Python LSP Resources
- pygls: https://github.com/openlawlibrary/pygls
- python-lsp-jsonrpc: https://github.com/python-lsp/python-lsp-jsonrpc
- pyright: https://github.com/microsoft/pyright

---

## Architectural Decision: Injection Point Recommendation

**Recommended:** Option 1 (Decorator Level) with graceful fallback

This matches opencode's approach where diagnostics are part of the tool output that the LLM sees. The agent can immediately act on errors without needing to run separate lint commands.

```python
# Recommended pattern for decorators.py
@file_tool
async def update_file(filepath: str, target: str, patch: str) -> str:
    # ... existing file update logic
    result = f"Updated {filepath}"

    # LSP integration (automatic, non-blocking on failure)
    if lsp_enabled():
        try:
            await LSP.touch_file(filepath, wait=True)
            diagnostics = await LSP.diagnostics(filepath)
            if diagnostics:
                errors = [d for d in diagnostics if d.severity == 1][:20]
                result += f"\n<file_diagnostics>\n{format_diagnostics(errors)}\n</file_diagnostics>"
        except Exception:
            pass  # Graceful degradation - edit still works

    return result
```

This provides the tight feedback loop that makes opencode's LSP integration valuable while maintaining robustness.

---

## Decision Discussion: Linter Subprocess vs Simplified LSP

### Initial Consideration: Shell Out to Linters

The fastest path to value would be shelling out to existing linters:

```python
# Simple approach - just run ruff
async def get_file_diagnostics(filepath: str) -> str | None:
    proc = await asyncio.create_subprocess_exec(
        "ruff", "check", "--output-format=concise", filepath,
        stdout=asyncio.subprocess.PIPE
    )
    stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=5.0)
    return stdout.decode() if stdout else None
```

**Pros:**
- Pattern already exists in `bash.py`
- No JSON-RPC complexity
- Projects already have linters configured

**Cons:**
- Only covers one language per implementation
- Each linter has different output format to parse
- Becomes N parsers for N languages

### The Multi-Language Problem

| Approach | 1 Language | 5+ Languages |
|----------|------------|--------------|
| Shell to linters | Simple | Messy - N parsers, N output formats |
| LSP | Overkill | Makes sense - one protocol, consistent format |

For a tool like tunacode that edits Python, TypeScript, Go, Rust, etc., maintaining separate linter integrations becomes a burden.

### Decision: Simplified LSP (Not Full Opencode)

**Chosen approach:** Implement a minimal LSP client that provides multi-language support without opencode's full complexity.

#### What We Need (Minimal Viable LSP)

```python
# Core flow - ~150-200 lines total
1. Spawn server (pyright --stdio, typescript-language-server --stdio)
2. Send initialize + initialized
3. Send textDocument/didOpen with file content
4. Receive textDocument/publishDiagnostics
5. Format and inject into tool output
```

#### What We Skip Initially

| Opencode Feature | Skip? | Reason |
|------------------|-------|--------|
| 150ms debounce | Yes | Use fixed wait instead |
| Inflight spawn deduplication | Yes | Rare edge case |
| Broken server tracking | Yes | Add later if needed |
| Incremental document sync | Yes | Send full file content |
| Version-based sync | Yes | Simpler without |
| Hover/completion | Yes | Diagnostics only for now |

#### Final Architecture

```
src/tunacode/lsp/
├── __init__.py       # Simple orchestrator (~50 lines)
│                     # - get_diagnostics(filepath) entry point
│                     # - Client cache by (server, project_root)
│
├── client.py         # Minimal LSP client (~150 lines)
│                     # - Spawn subprocess
│                     # - JSON-RPC over stdin/stdout
│                     # - initialize/didOpen/publishDiagnostics only
│
└── servers.py        # Server definitions (~30 lines)
                      # - Extension to command mapping
```

#### Server Definitions

```python
# servers.py
SERVERS: dict[str, list[str]] = {
    ".py": ["pyright-langserver", "--stdio"],
    ".ts": ["typescript-language-server", "--stdio"],
    ".tsx": ["typescript-language-server", "--stdio"],
    ".js": ["typescript-language-server", "--stdio"],
    ".jsx": ["typescript-language-server", "--stdio"],
    ".go": ["gopls", "serve"],
    ".rs": ["rust-analyzer"],
    ".vue": ["vue-language-server", "--stdio"],
}
```

#### Why This Wins

1. **One client, many languages** - Same ~150 line client works for all
2. **Consistent diagnostic format** - LSP Diagnostic is standardized
3. **Future-proof** - Can add debouncing, caching, hover later
4. **Graceful degradation** - If server missing, edit still works

---

## Revised Implementation Plan

### Phase 1: Minimal LSP Client
1. Create `src/tunacode/lsp/` module
2. Implement basic JSON-RPC message send/receive over stdin/stdout
3. Implement `initialize` handshake
4. Implement `textDocument/didOpen` notification
5. Implement `textDocument/publishDiagnostics` handler
6. Add simple client cache by project root

### Phase 2: Tool Integration
1. Add `get_diagnostics(filepath)` function to LSP module
2. Modify `@file_tool` decorator to call LSP after file modifications
3. Format diagnostics as `<file_diagnostics>` XML block
4. Add config toggle (`settings.lsp.enabled`)

### Phase 3: Multi-Language Servers
1. Add server definitions for Python (pyright)
2. Add server definitions for TypeScript/JavaScript
3. Add server definitions for Go (gopls)
4. Add server definitions for Rust (rust-analyzer)
5. Handle missing servers gracefully

### Phase 4: Polish
1. Add timeout handling for slow servers
2. Add basic error logging
3. Add UI indicator for LSP status (optional)
4. Document configuration options

---

## Summary

**Decision:** Implement simplified LSP client for multi-language support.

**Rationale:** Single-language linter approach doesn't scale. LSP provides unified protocol for all languages with consistent diagnostic format. Simplified implementation (~200 lines) avoids opencode's complexity while delivering core value.

**Next Step:** Proceed to implementation planning phase with the simplified LSP architecture.
