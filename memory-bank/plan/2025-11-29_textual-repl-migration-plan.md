---
title: "Textual REPL Replacement Plan"
phase: Plan
date: "2025-11-29T16:30:00Z"
owner: "gemini:plan"
parent_research: "memory-bank/research/2025-11-29_14-53-40_rich-to-textual-migration.md"
parent_communication: "memory-bank/communication/2025-11-29_gemini_textual-migration-discussion.md"
git_commit_at_plan: "f2e5f01"
tags: [plan, textual, repl, ui-replacement, orchestrator]
---

## Goal

Replace the prompt_toolkit/Rich CLI REPL with a Textual-based shell that drives the real orchestrator. Deliver the eight requested artifacts: branch + runnable Textual entry point, custom editor widget, async tool-confirmation modal, streaming pause/resume via RichLog, real `agent.process_request()` wiring, an end-to-end test for mid-stream confirmation, and a review-ready PR.

## Scope & Assumptions

### In Scope
- New Textual App in `src/tunacode/cli/textual_repl.py` that becomes the default CLI entry point (replaces `cli/repl.py` invocation).
- Custom Textual editor widget providing multiline input, `Esc+Enter` newline binding, and completion for `/commands` + `@file` references.
- Future-based tool confirmation modal (non-blocking Textual modal resolves `asyncio.Future[bool]`).
- Streaming integration using the real orchestrator `agent.process_request()` with `streaming_callback` writing to `RichLog`, including pause/resume buffering.
- Wiring to orchestrator state management without stubs or fake agents.
- End-to-end Textual test that exercises mid-stream tool confirmation without breaking streaming output.

### Out of Scope
- Changing orchestrator business logic, tool implementations, or agent state machine semantics.
- Adding new model providers or tool types.
- Reworking prompt_toolkit UX (we replace it entirely).
- Additional theming/branding beyond what Textual needs for functionality.

### Assumptions
- Textual, Rich, and `textual-dev` remain available in the environment; prompt_toolkit can be removed once Textual shell replaces it.
- `.venv` + `uv` remain the package workflow; `ruff check --fix .` is run before PR.
- Existing orchestrator interface (`agent.process_request`) stays stable per research doc.

## Deliverables (DoD)

1. **Branch:** `textual_repl` branch created; Textual app runs without crashing via CLI entry point.
2. **Textual Shell:** `cli/repl.py` entry point replaced by Textual launcher targeting `textual_repl.py` app class.
3. **Editor Widget:** Multiline Textual widget with `Esc+Enter` newline binding, `/command` + `@file` completion, and basic syntax cues.
4. **Tool Confirmation Modal:** Future-based, non-blocking Yes/No modal that resolves `tool_callback` futures.
5. **Streaming Integration:** `streaming_callback` writes to `RichLog`; pause/resume buffers in-flight chunks and flushes on resume.
6. **Real Orchestrator:** Worker tasks call `agent.process_request()` (no demo stubs) with proper tool + streaming hooks.
7. **End-to-End Test:** Automated test demonstrates mid-stream tool confirmation works without breaking streaming flow.
8. **Review-Ready PR:** Draft cleaned (no WIP), `ruff` + `pytest` green, docs and `.claude` KB updated.

## Architectural Tenets

- **Event-driven only:** No blocking `input()`; all user interactions happen via Textual messages/modals.
- **Explicit async coordination:** Tool confirmations use `asyncio.Future` resolved by modal handlers; streaming uses buffer + pause flag to avoid lost chunks.
- **Single source of truth:** Orchestrator state lives in `state_manager`; Textual app mirrors state via messages, not shared globals.
- **Replace, don’t wrap:** `cli/repl.py` becomes a thin launcher delegating to Textual app; prompt_toolkit is removed rather than shimmed.
- **Test-first:** Create golden baseline for Textual shell startup, then failing mid-stream confirmation test before implementation.

## Milestones

**M1: Branch & Entry Point Scaffold**
- Create `textual_repl` branch and add `src/tunacode/cli/textual_repl.py` skeleton (Textual App class + `RichLog` + placeholder editor).
- Update CLI entry point (likely `scripts/tunacode` or `pyproject` script) to launch Textual app instead of `cli/repl.py`.

**M2: Editor Widget**
- Implement custom multiline Textual widget with `Esc+Enter` newline binding and `/` + `@` completions.
- Wire submit events to queue requests for orchestrator worker.

**M3: Tool Confirmation Modal**
- Implement Future-based modal that posts Yes/No back to worker via message and resolves pending `asyncio.Future[bool]`.
- Ensure modal can be triggered mid-stream without blocking UI loop.

**M4: Streaming Integration**
- Implement streaming callback that writes to `RichLog`, supports pause/resume, and buffers while paused.
- Add UI controls for pause/resume and buffer flush.

**M5: Orchestrator Wiring**
- Connect worker tasks to real `agent.process_request()` with `tool_callback` + `streaming_callback`.
- Ensure state_manager interactions match current orchestrator contract.

**M6: Testing & QA**
- Add golden baseline test for Textual app startup.
- Add failing test for mid-stream tool confirmation, then implement until green.
- Run `ruff check --fix .` and `pytest`.

**M7: PR & Knowledge Base**
- Prepare review-ready PR (no WIP markers); update docs describing new Textual shell and removal of prompt_toolkit.
- Update `.claude` delta summaries/semantic index and sync/validate KB.

## Work Breakdown (Tasks)

### Task 1: Scaffold Textual App & Branch
**Owner:** Gemini  
**Dependencies:** None  
**Acceptance Tests:**
- [ ] Branch `textual_repl` exists with `textual_repl.py` skeleton committed.
- [ ] `python -m tunacode.cli.textual_repl` (or equivalent script) launches Textual app without runtime errors in `.venv`.
**Files/Interfaces:** `src/tunacode/cli/textual_repl.py`, `scripts/*` or `pyproject.toml` entry point.

### Task 2: Replace Entry Point
**Owner:** Gemini  
**Dependencies:** Task 1  
**Acceptance Tests:**
- [ ] `cli/repl.py` is removed (or reduced to a thin import shim with zero prompt_toolkit references); Textual launcher is the sole entry path.
- [ ] Packaging/CLI docs updated to reference Textual shell.
**Files/Interfaces:** `src/tunacode/cli/repl.py`, `pyproject.toml`, `README.md`/`documentation`.

### Task 3: Build Editor Widget
**Owner:** Gemini  
**Dependencies:** Task 1  
**Acceptance Tests:**
- [ ] Multiline input with `Esc+Enter` newline binding implemented via Textual bindings.
- [ ] Completion popover for `/commands` and `@file` paths (filesystem-backed).
- [ ] Submit event emits normalized request payload to worker queue.
*Note:* If this completion work threatens the critical path, defer it explicitly with a follow-up issue and PR note while keeping the rest of the shell intact.
**Files/Interfaces:** `src/tunacode/cli/textual_repl.py` (editor widget module), potential `src/tunacode/ui` removal references.

### Task 4: Tool Confirmation Modal
**Owner:** Gemini  
**Dependencies:** Task 3  
**Acceptance Tests:**
- [ ] Modal opens on tool invocation, resolves `asyncio.Future[bool]` without blocking UI.
- [ ] User Yes/No updates RichLog with decision and resumes streaming appropriately.
**Files/Interfaces:** `src/tunacode/cli/textual_repl.py` (modal + message handlers), `core/tool_handler.py` integration hooks.

### Task 5: Streaming Callback with Pause/Resume
**Owner:** Gemini  
**Dependencies:** Task 3  
**Acceptance Tests:**
- [ ] `streaming_callback` writes Rich renderables to `RichLog`.
- [ ] Pause flag buffers new chunks; resume flushes buffer in order.
- [ ] UI exposes pause/resume controls and reflects state.
**Files/Interfaces:** `src/tunacode/cli/textual_repl.py` (streaming handler, buffer), `core/agents.py` integration.

### Task 6: Wire Real Orchestrator
**Owner:** Gemini  
**Dependencies:** Tasks 3-5  
**Acceptance Tests:**
- [ ] Worker uses `agent.process_request()` with actual state_manager and tool callbacks.
- [ ] No demo/fake agents remain; `cli/repl.py` references removed or redirected.
- [ ] Error handling surfaces to Textual UI (fail-fast, no silent swallow).
**Files/Interfaces:** `src/tunacode/core/agents.py`, `src/tunacode/core/state.py`, `src/tunacode/cli/textual_repl.py`.

### Task 7: Testing & QA
**Owner:** Gemini  
**Dependencies:** Tasks 1-6  
**Acceptance Tests:**
- [ ] Golden baseline test for Textual shell launch added (characterization of startup render).
- [ ] Failing test for mid-stream tool confirmation added, then passes once modal + streaming wiring complete.
- [ ] `ruff check --fix .` and `source .venv/bin/activate && pytest` succeed.
**Files/Interfaces:** `tests/e2e/test_textual_repl.py` (new), potential fixtures under `tests/fixtures`.

### Task 8: PR, Docs, & KB
**Owner:** Gemini  
**Dependencies:** Tasks 1-7  
**Acceptance Tests:**
- [ ] PR titled without WIP markers; description links research + plan and summarizes tests.
- [ ] Docs updated for new Textual shell usage and prompt_toolkit removal.
- [ ] `.claude` KB updated (delta summary, semantic index, QA entry) and `claude-kb sync --verbose` + `claude-kb validate` run.
**Files/Interfaces:** `README.md`, `documentation/*`, `.claude/*`, PR description template.

## Risks & Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Textual editor keybindings conflict with defaults | Medium | Medium | Define explicit bindings and document; add tests for Esc+Enter behavior |
| Tool confirmation races with streaming flush | High | Medium | Use queued messages + Future; buffer writes while modal open; integration test covers mid-stream case |
| Prompt_toolkit removal breaks packaging scripts | Medium | Low | Update entry points and dependency lists in lockstep; add smoke test invoking CLI script |
| Performance regression in RichLog with large streams | Medium | Low | Buffer flush in batches; measure during E2E test; add pause/resume controls |
| Missing KB update causes drift | Medium | Medium | Include KB sync/validate in Task 8 acceptance tests |

## Test Strategy (TDD)

- **Baseline:** Add golden test capturing Textual app startup (ensures initial layout stays stable).
- **Red:** Add failing E2E test for mid-stream tool confirmation (pause streaming, modal decision, resume flush).
- **Green:** Implement streaming + modal coordination until test passes.
- **Blue:** Refactor for clarity, enforce `ruff`, and ensure tests stay green.

## References

- Research: `memory-bank/research/2025-11-29_14-53-40_rich-to-textual-migration.md`
- Communication: `memory-bank/communication/2025-11-29_gemini_textual-migration-discussion.md`
- Current REPL (for replacement): `src/tunacode/cli/repl.py`
- Orchestrator contract: `src/tunacode/core/agents.py`, `src/tunacode/core/state.py`
