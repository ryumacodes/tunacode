# Research - Rich to Textual Migration

**Date:** 2025-11-29
**Last Updated:** 2025-11-29
**Owner:** claude
**Phase:** Research
**Git Commit:** 2eac952

## Goal

Evaluate migration from Rich to Textual for the UI layer.

## Key Insight: Replacement, Not Migration

This is NOT a component-by-component migration. It's a full UI layer replacement.

We don't need to:
- Map Rich components to Textual equivalents
- Keep lazy-loading workarounds
- Maintain Rich console proxies
- Convert Rich.Live to Textual reactive
- Port the StreamingAgentPanel
- Preserve async/sync wrapper patterns
- Keep run_in_terminal() hacks
- Migrate UI_COLORS dict

Textual already provides:
- Input widgets (replaces prompt_toolkit)
- RichLog widget (accepts Rich renderables directly)
- Built-in reactive updates
- Built-in layouts and containers
- Built-in CSS theming
- Built-in async event loop
- Built-in widget lifecycle

## Scope Analysis

### What to Keep (Orchestrator Layer)

| File | Reason |
|------|--------|
| `core/agents.py` | Agent logic, process_request() |
| `core/state.py` | State management |
| `core/tool_handler.py` | Tool execution |
| Tool implementations | Business logic |

### What to Replace (UI Layer)

| File | Reason |
|------|--------|
| `ui/panels.py` | StreamingAgentPanel - replaced by RichLog |
| `ui/tool_ui.py` | Panel rendering - Textual widgets |
| `ui/output.py` | Console abstraction - not needed |
| `ui/console.py` | Lazy console - not needed |
| `ui/utils.py` | Console utilities - not needed |
| `ui/input.py` | prompt_toolkit input - Textual Input widget |
| `ui/decorators.py` | async/sync wrappers - Textual event model |
| `cli/repl.py` | REPL loop - becomes Textual App |

### REPL Coupling Analysis

`cli/repl.py` has direct coupling to prompt_toolkit + Rich that requires rewriting:

| Line | Coupling Point |
|------|----------------|
| 10 | `from prompt_toolkit.application import run_in_terminal` |
| 11 | `from prompt_toolkit.application.current import get_app` |
| 277, 402 | `run_in_terminal()` calls |
| 351 | `await ui.multiline_input(...)` |
| 412 | `get_app().create_background_task(...)` |
| 184-201 | `StreamingAgentPanel` integration |
| 394, 398, 431 | Direct `ui.console.print()` calls |

## Orchestrator Interface (Unchanged)

The key interface stays the same:

```python
res = await agent.process_request(
    text,
    model,
    state_manager,
    tool_callback=...,
    streaming_callback=lambda content: ...,  # <-- Textual hooks here
)
```

The `streaming_callback` is all Textual needs:
- Current: `streaming_panel.update(content)`
- Textual: `rich_log.write(content)`

## Migration Path

```
1. Keep orchestrator logic exactly the same
2. Delete ui/ entirely
3. Rewrite cli/repl.py as a Textual App
4. Wire:
   - Input widget submit -> worker calls orchestrator
   - Orchestrator streaming_callback -> RichLog.write()
5. Delete prompt_toolkit dependency
```

## Files with Rich Imports (Reference Only)

For completeness, these are the 7 files currently using Rich:

| File | Components |
|------|------------|
| `ui/panels.py` | Markdown, Padding, Pretty, Table, Text, ROUNDED, Live, Panel |
| `ui/tool_ui.py` | ROUNDED, Markdown, Padding, Panel |
| `ui/output.py` | Padding, Console |
| `ui/console.py` | Console, Markdown |
| `ui/utils.py` | Console |
| `core/logging/handlers.py` | Console, Text |
| `utils/diff_utils.py` | Text |

Note: `diff_utils.py` returns Rich Text objects which RichLog accepts directly - may not need changes.

## Dependencies

From `pyproject.toml`:
- Rich: `>=14.2.0,<15.0.0`
- Textual: `textual` (already installed)
- Textual Dev: `textual-dev` (dev dependency)

---

## Maintainer Discussion

### Context

Initial research framed this as a component-by-component migration with complexity ratings per file. Another maintainer correctly identified this as over-engineering.

### Response to Maintainer

You're right about the mental model - it's a replacement, not a migration.

But the scope is slightly bigger than just `ui/`. Checked `cli/repl.py` and it has direct coupling:

```
- prompt_toolkit.application.run_in_terminal (lines 10, 277, 402)
- prompt_toolkit.application.current.get_app (lines 11, 412)
- ui.multiline_input (line 351)
- StreamingAgentPanel (lines 184-201)
- direct ui.console.print() calls (lines 394, 398, 431)
```

So the actual scope is:

| Keep | Replace |
|------|---------|
| `core/agents.py` | `ui/*` (7 files) |
| `core/state.py` | `cli/repl.py` |
| `core/tool_handler.py` | |
| Tool implementations | |

The orchestrator interface stays clean:

```python
res = await agent.process_request(
    text,
    model,
    state_manager,
    tool_callback=...,
    streaming_callback=lambda content: ...,  # <-- this is the hook
)
```

That `streaming_callback` is all Textual needs. Instead of `streaming_panel.update(content)`, it becomes `rich_log.write(content)`.

So yes - delete `ui/` + rewrite `cli/repl.py` as a Textual App. Orchestrator untouched.

The minimal Textual shell you mentioned would be helpful - specifically how the REPL loop translates to Textual's event model (Input widget submit -> worker calls orchestrator -> worker posts to RichLog).

---

## Next Steps

1. Get minimal Textual App shell from maintainer
2. Verify orchestrator interface compatibility
3. Delete `ui/` and rewrite `cli/repl.py`
4. Wire streaming_callback to RichLog
5. Remove prompt_toolkit dependency

## References

- `src/tunacode/cli/repl.py` - Current REPL implementation (to be replaced)
- `src/tunacode/core/agents.py` - Orchestrator (unchanged)
- `pyproject.toml:34-37` - Dependency versions
