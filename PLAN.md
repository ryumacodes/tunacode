# LSP Architecture Analysis & Plan

## History (Important Context)

**LSP diagnostics were actively used until today.** Commit `690c4760` (Jan 27, 2026) removed them:

```
refactor(tun-be3d): remove LSP import from file_tool decorator

- Remove LSP diagnostics integration from tools/decorators.py
- Simplify file_tool decorator (remove writes parameter)
- Update update_file.py and write_file.py to use simplified decorator
- Eliminates tools→lsp lateral coupling
```

**How it worked (before removal):**
- `@file_tool(writes=True)` decorator on `write_file` and `update_file`
- After file write, automatically called `_get_lsp_diagnostics(filepath)`
- Appended formatted diagnostics to tool result
- Agent received immediate feedback on type errors/lint issues

**Why it was removed:**
- Gate 2 dependency violation: `tools → lsp` coupling
- LSP was positioned as a "layer" but was actually infrastructure
- Cleanup work to fix architecture before reimplementing properly

---

## Current State (After Removal)

### File Structure

```
src/tunacode/
├── lsp/                          # DORMANT - exists but unused
│   ├── __init__.py               # get_diagnostics, format_diagnostics (no callers)
│   ├── client.py                 # LSPClient class (no instances created)
│   └── servers.py                # Server command mapping (only by lsp_status)
│
├── core/
│   └── lsp_status.py             # FACADE - UI checks if LSP enabled/server available
│
├── tools/
│   └── lsp_status.py             # Imports from lsp.servers for status check
│
└── utils/
    └── formatting.py             # truncate_diagnostic_message (moved from lsp/)
```

### What's Working
- UI displays LSP status: `LSP: ruff` or `LSP: no server` or hidden if disabled
- Status check looks for binary availability (`which ruff`, etc.)

### What's Dormant
- Full LSP client infrastructure (JSON-RPC, process management, caching)
- `get_diagnostics()` function exists but has **zero callers**
- `format_diagnostics()` exists but unused

### Dependencies

```
ui → core/lsp_status.py → tools/lsp_status.py → lsp/servers.py
```

- `lsp/__init__.py` exports `get_diagnostics`, `format_diagnostics` → **unused**
- `lsp/client.py` → **unused**
- `lsp/servers.py` → only used by `tools/lsp_status.py` for binary detection

---

## The Plan: Two-Phase Approach

### Phase 1: Complete Removal (Now)

**Rationale:** The code is already unused. Full removal is cleaner than leaving dormant infrastructure.

**Files to delete:**
- `src/tunacode/lsp/` (entire directory)
- `src/tunacode/core/lsp_status.py`
- `src/tunacode/tools/lsp_status.py`

**UI changes:**
- Remove LSP indicator from `ResourceBar` (or keep as "not configured")

**Result:** Clean slate. No LSP concepts anywhere in codebase.

### Phase 2: Reimplement as Tool-Only Layer (Later)

**Design principles:**
1. **LSP is a tool concern** - not a core service, not utils-level
2. **No automatic diagnostics** - agent must explicitly request them
3. **Simple architecture** - one module, clear boundaries

**Proposed structure:**

```
src/tunacode/tools/
├── check_file.py          # NEW: Tool for explicit diagnostic check
└── lsp/                   # NEW: Sub-package within tools (not top-level)
    ├── __init__.py        # Minimal exports
    ├── client.py          # Same LSPClient (moved from top-level lsp/)
    └── servers.py         # Server command mapping
```

**Tool API:**
```python
# tools/check_file.py
@tool
async def check_file(filepath: str) -> str:
    """Check a file for errors using the appropriate language server.

    Returns diagnostics (errors, warnings) or empty string if clean.
    """
    # Spawn LSP, get diagnostics, format result
```

**Key differences from old approach:**
| Old | New |
|-----|-----|
| Automatic after write | Explicit tool call |
| Decorator magic | Explicit in tool function |
| `tools → lsp` import | `tools.check_file → tools.lsp` import (same layer) |
| Top-level `lsp/` layer | Nested `tools/lsp/` implementation detail |
| UI status indicator | Optional - maybe just log when server found |

**Dependency flow (new):**
```
core/agent_config.py → tools/check_file.py → tools/lsp/client.py
```

This is valid: core → tools is allowed. tools.lsp is just an implementation detail of tools.

---

## Why This Approach?

1. **Clean slate** - Remove broken architecture completely
2. **Proper boundaries** - LSP is a tool, lives in tools/
3. **Explicit over implicit** - Agent asks for diagnostics, not automatic
4. **Simpler mental model** - One way to get diagnostics: the check_file tool
5. **No layer violations** - tools.lsp is internal to tools layer

---

## Open Questions

1. **Should we keep UI status indicator?** Shows which LSP server is available (ruff, pyright, etc.)
2. **Should check_file be in the default tool set?** Or only enabled when LSP configured?
3. **Cache LSP processes?** Old code kept clients alive per workspace. Worth the complexity?

---

## Next Steps

1. **Phase 1:** Delete all LSP-related code
2. **Test:** Verify no regressions (UI works without LSP indicator)
3. **Phase 2:** Implement check_file tool with nested tools/lsp/ package
4. **Register:** Add check_file to agent tool list when LSP enabled
