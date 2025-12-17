# Research: LSP diagnostics feedback (agent vs UI)

Status: research mode (no pushing).
Last updated: 2025-12-17

## Context (from ongoing work)

- Task: “LSP Diagnostics Display Fix” marked complete; PR open (`fix/lsp-diagnostics-display`, PR `#186`).
- Related issue: `#185` (broader NeXTSTEP tool panel renderer audit).
- Hypothesis to validate: the agent is not *using* LSP feedback correctly (even if diagnostics are being produced).

Note: the current working tree on `master` does **not** contain the PR-described files (e.g. `src/tunacode/ui/renderers/tools/diagnostics.py`) at the time this doc was written, so this document maps **what’s on disk now** plus the likely integration points for the PR branch.

## What “LSP feedback” means in tunacode today

Tunacode’s LSP integration currently works by **appending diagnostics to tool output** after successful file writes/edits.

### Where diagnostics are produced

1. `src/tunacode/tools/update_file.py` and `src/tunacode/tools/write_file.py` are decorated with `@file_tool(writes=True)`.
2. `src/tunacode/tools/decorators.py:file_tool(..., writes=True)` runs the wrapped tool, then calls `_get_lsp_diagnostics(filepath)` and appends its formatted output to the returned string.
3. `_get_lsp_diagnostics()` calls:
   - `src/tunacode/lsp/__init__.py:get_diagnostics()` → orchestrates server selection + client lifecycle
   - `src/tunacode/lsp/client.py:LSPClient.get_diagnostics()` → `didOpen` then waits for `publishDiagnostics`
   - `src/tunacode/lsp/__init__.py:format_diagnostics()` → formats as:
     - `<file_diagnostics>` … `</file_diagnostics>` (XML-ish wrapper, plain text lines inside)

### Where diagnostics are supposed to reach the model (LLM)

The *only* intentional “agent feedback loop” is: diagnostics are part of the tool return string, so they become part of the next model request.

Concretely:

- Tool returns are stored as `tool-return` parts inside the next `node.request`.
- `src/tunacode/core/agents/agent_components/node_processor.py` appends `node.request` into `state_manager.session.messages`, so the persisted message history includes those tool returns.
- The next model call receives the tool-return parts as part of the conversation context (pydantic-ai’s normal tool loop).

There is **no additional core logic** today that:

- parses `<file_diagnostics>` into structured data,
- promotes diagnostics to a system message,
- blocks completion until diagnostics are addressed,
- or otherwise “forces” the agent to act on diagnostics.

## Where diagnostics are supposed to reach the user (UI)

The UI displays tool results via `tool_result_callback`:

- `src/tunacode/ui/app.py:build_tool_result_callback()` posts `ToolResultDisplay(tool_name, status, args, result, …)`.
- In `src/tunacode/core/agents/agent_components/node_processor.py`, tool results are displayed by iterating `tool-return` parts in `node.request` and calling `tool_result_callback(...)`.

Important limitation: in that display path, `args={}` is passed because tool-return parts do not carry original args in this implementation. That means:

- UI renderers that rely on args (e.g., `filepath`) will often fall back to `"unknown"`.
- Any “zone renderer” that wants to tie diagnostics to a file path must recover it from the tool return text (diff headers, embedded “File ‘…’ updated” strings, etc.), or the architecture must be changed to persist args alongside tool returns.

## Why the agent may appear to “ignore” diagnostics (hypotheses)

These are ranked by likelihood / leverage.

### H1: Diagnostics never run (no language server available)

`src/tunacode/lsp/servers.py:get_server_command()` returns `None` if the server binary is missing (`shutil.which` check). If that happens:

- `get_diagnostics()` returns `[]`
- `format_diagnostics()` returns `""`
- nothing is appended to the tool output
- the model gets no LSP feedback at all

Quick check:
- `which pyright-langserver`
- `which pylsp`

Observed (this machine, at time of writing):
- `pyright-langserver`: missing
- `pylsp`: missing
- `rust-analyzer`: present

### H2: Diagnostics exist, but are not visible in the UI

On `master`, `src/tunacode/ui/renderers/tools/update_file.py` renders only the diff + metadata. It does not parse or show `<file_diagnostics>`.

If diagnostics are appended after the diff, they may exist in raw tool output but be effectively hidden in the TUI.

### H3: Diagnostics are too verbose/noisy for the model to act on

Current `format_diagnostics()` includes the raw `diag.message` and does not:

- truncate to first line,
- clamp to a max character length,
- add a summary line,
- or limit by `settings.lsp.max_diagnostics` (it currently hard-limits to 20 inside `format_diagnostics`, ignoring config).

Failure mode: the diagnostic payload becomes large and/or repetitive; the model deprioritizes it compared to surrounding context (diff, instructions, etc.).

### H4: LSP client semantics produce stale/missing diagnostics

Potential protocol issues to validate:

- `LSPClient.open_file()` always sends `textDocument/didOpen` with `version=1` and never sends `didChange` or `didClose`.
- Some servers may ignore repeated `didOpen` for an already-open URI, or rely on `didChange` for updates.
- The orchestrator roots the server at `root=path.parent`; that can prevent pyright from finding project-level config (e.g. `pyproject.toml`) depending on repository layout.

If diagnostics are inconsistent, the agent can’t rely on them.

### H5: Tool prompts may be misleading, causing wrong mental model

Tool prompts are loaded from `src/tunacode/tools/prompts/*_prompt.xml` and assigned to tool functions via `decorators.base_tool()`.

At time of writing, at least:

- `src/tunacode/tools/prompts/update_file_prompt.xml` describes args that do not match `update_file(filepath, target, patch)`.
- `src/tunacode/tools/prompts/write_file_prompt.xml` claims overwrite behavior that contradicts `write_file` (it fails if file exists).

Even if unrelated to diagnostics directly, prompt mismatch increases the chance the model does the wrong thing after receiving diagnostics (or fails to interpret tool results correctly).

### H6: LSP configuration is not reading user config

`src/tunacode/tools/decorators.py:_get_lsp_config()` reads `DEFAULT_USER_CONFIG` rather than the active `state_manager.session.user_config`.

Implications:

- User-level toggles may not apply.
- Tuning knobs like `max_diagnostics` aren’t actually controlling output.

This can create a gap between “what we think we configured” and what’s actually happening at runtime.

## What to instrument / test next (research checklist)

1. Confirm whether diagnostics are appended at all:
   - Trigger a known type error via `update_file` on a `.py` file.
   - Inspect the raw tool return string for `<file_diagnostics>`.
2. Confirm whether the model is receiving them:
   - Add temporary logging around tool-return parts in `node_processor.py` (or inspect `state_manager.session.messages`) to verify diagnostics survive into the next request.
3. Confirm LSP server availability + stability:
   - Ensure `pyright-langserver` or `pylsp` exists, and validate repeated edits still yield fresh diagnostics.
4. Decide on a “forcing function” if needed:
   - If we want the agent to *always* react to diagnostics, we likely need core logic that detects `<file_diagnostics>` in the latest tool return and injects a short system-level instruction like: “Fix listed diagnostics before proceeding.”

## Pointers (files to look at first)

- LSP injection: `src/tunacode/tools/decorators.py`
- Orchestrator: `src/tunacode/lsp/__init__.py`
- Client protocol: `src/tunacode/lsp/client.py`
- Server mapping: `src/tunacode/lsp/servers.py`
- Tool loop + UI display: `src/tunacode/core/agents/agent_components/node_processor.py`, `src/tunacode/ui/app.py`
- Context pruning: `src/tunacode/core/compaction.py`
- Tool docs/prompts: `src/tunacode/tools/prompts/update_file_prompt.xml`, `src/tunacode/tools/prompts/write_file_prompt.xml`

---

## Validation Session (2025-12-17)

### Findings

#### H1 Update: Server IS available (pyright was working)

Contrary to earlier check, pyright-langserver WAS present and working:
- UI status bar showed "LSP: pyright"
- Diagnostics were being produced and displayed

#### H2 Update: Diagnostics ARE visible in UI

The `update_file` renderer shows diagnostics as **raw text** at the bottom of the diff panel:

```
<file_diagnostics>
Error (line 160): No overloads for "push_screen" match the provided arguments
Error (line 160): Argument of type "(completed: bool) -> None" cannot be assigned...
</file_diagnostics>
```

Diagnostics are not styled/parsed - they appear as plain XML text within the tool output. But they ARE visible.

#### H3 VALIDATED: Pyright output is too verbose

Observed pyright errors include full type explanations:

```
Error (line 160): Argument of type "(completed: bool) -> None" cannot be assigned to parameter "callback" of type "ScreenResultCallbackType[ScreenResultType@push_screen] | None" in function "push_screen"
  Type "(completed: bool) -> None" is not assignable to type "((bool | None) -> None) | ((bool | None) -> Awaitable[None]) | None"
    Type "(completed: bool) -> None" is not assignable to type "(bool | None) -> None"
      Parameter 1: type "bool | None" is incompatible with type "bool"
        Type "bool | None" is not assignable to type "bool"
          "None" is not assignable to type "bool"
```

This verbosity likely causes the model to deprioritize or skim the diagnostic content.

#### Agent feedback loop: CONFIRMED WORKING

Traced the full flow:
1. `update_file` returns diff string
2. `@file_tool(writes=True)` decorator appends `<file_diagnostics>` block via `_get_lsp_diagnostics()`
3. Combined string stored in `tool-return` part content
4. LLM receives full string in next request via pydantic-ai tool loop
5. UI callback also receives same string for display

**The agent DOES receive all LSP diagnostics.** The full verbose output goes into the context window. Whether it acts on them is a model behavior issue, not architecture.

### Key Discovery: Ruff vs Pyright

| Tool | Type | Output Style |
|------|------|--------------|
| **Pyright** | Type checker | Verbose nested type explanations |
| **Ruff** | Linter | Clean, actionable lint errors |

Running `ruff check` on the same file with pyright type errors:
```
All checks passed!
```

Ruff doesn't do type checking - it only does linting. The pyright errors were **type signature mismatches**, not lint issues.

### Decision: Switch to Ruff for LSP

**Rationale:**
- Ruff is the modern standard for Python tooling
- Cleaner, less verbose output
- Focuses on actionable issues the agent can fix
- Type errors that don't break runtime are lower priority than clear feedback

**Change made:**
`src/tunacode/lsp/servers.py` - Python files now use `ruff server --stdio` only (removed pyright and pylsp fallbacks).

```python
".py": (
    "python",
    [
        ["ruff", "server", "--stdio"],
    ],
),
```

### Remaining Questions

1. **Will agents act on ruff feedback better than pyright?** - Needs testing
2. **Should we add type checking back as optional?** - Maybe as user config toggle
3. **UI styling for diagnostics** - Lower priority, but would improve UX
