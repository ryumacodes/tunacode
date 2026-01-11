---
title: "Shell Panel NeXTSTEP Standardization – Plan"
phase: Plan
date: "2026-01-10T09:40:00"
updated: "2026-01-10T11:30:00"
owner: "claude"
parent_research: "memory-bank/research/2026-01-10_09-33-00_shell_panel_nextstep_standardization.md"
git_commit_at_plan: "b827de5"
tags: [plan, shell, ui, nextstep, panel, bash-mode]
---

## Goal

Standardize the `!shell` command output to use the 4-zone NeXTSTEP panel pattern, matching the agent `bash` tool format. Enhance shell mode indication to be visually apparent.

**Non-goals:**
- Interactive shell sessions with readline/job control (future work)
- Dedicated modal shell screen (inline panel only)
- Deployment or observability concerns
- Creating duplicate renderer code (reuse `BashRenderer`)

## Scope & Assumptions

### In Scope
1. **Shell output standardization:** Replace plain `Text()` output with 4-zone NeXTSTEP panels
2. **Mode indication enhancement:** Add prominent visual indicator for shell mode
3. **Code path unification:** Reuse existing `BashRenderer` for user `!shell` commands
4. **CSS styling updates:** Ensure `mode-active` class has visual representation

### Out of Scope
- Interactive shell sessions (persistent REPL)
- Shell history management beyond current implementation
- Terminal emulation features (tab completion, job control)
- Shell configuration profiles
- New renderer classes (reuse existing)

### Assumptions
- **Rich text framework:** Textual/Rich for rendering panels
- **Existing reference:** `BashRenderer` at `src/tunacode/ui/renderers/tools/bash.py` is reusable as-is
- **CSS framework:** Existing `.tcss` files for styling
- **NeXTSTEP principles:** 4-zone layout (header, parameters, viewport, status)

## Deliverables

| Deliverable | Description |
|-------------|-------------|
| `ShellRunnerHost` protocol update | Accept `RenderableType` instead of `Text` |
| `shell_runner.py` modifications | Format output and call `render_bash()` |
| CSS updates | Style `mode-active` class for prominent mode indication |
| Integration validation | Verify end-to-end flow works |

## Readiness

### Preconditions
- ✅ Existing `BashRenderer` implements full 4-zone pattern
- ✅ `BashRenderer.parse_result()` documents expected text format
- ✅ `ShellRunnerHost` protocol defined
- ✅ CSS framework in place (`.tcss` files)

### External Dependencies
- None (all internal)

### Sample Inputs
```
User types: "!ls -la"
Expected output: 4-zone panel with command, cwd, stdout/stderr, exit code, duration
```

## Milestones

### M1: Protocol & Wiring
- Update `ShellRunnerHost` protocol to accept `RenderableType`
- Modify `ShellRunner._run()` to use `BashRenderer`

### M2: Mode Indication Enhancement
- Style `mode-active` CSS class
- Add visual feedback for mode transitions

### M3: Integration & Validation
- Verify end-to-end flow
- Basic validation tests

## Work Breakdown (Tasks)

### Task 1: Update ShellRunnerHost Protocol
**ID:** T1 | **Owner:** claude | **Estimate:** M1 | **Deps:** None

Change protocol to accept `RenderableType` instead of `Text` for flexibility.

```python
# Before
def write_shell_output(self, renderable: Text) -> None: ...

# After
def write_shell_output(self, renderable: RenderableType) -> None: ...
```

**Acceptance test:** Protocol compiles, existing `Text` calls still work (backward compatible).

**Files touched:**
- `src/tunacode/ui/shell_runner.py` (line 23)

---

### Task 2: Wire ShellRunner to BashRenderer
**ID:** T2 | **Owner:** claude | **Estimate:** M1 | **Deps:** T1

Modify `ShellRunner._run()` to:
1. Capture command, exit code, cwd, stdout, stderr, duration
2. Format as text matching `BashRenderer.parse_result()` expected format
3. Call `render_bash()` to produce panel
4. Pass panel to `write_shell_output()`

**Expected format for BashRenderer:**
```
Command: <command>
Exit Code: <code>
Working Directory: <path>

STDOUT:
<output>

STDERR:
<errors>
```

**Acceptance test:** `!ls -la` command produces 4-zone panel instead of plain text.

**Files touched:**
- `src/tunacode/ui/shell_runner.py` (lines 94-129, `_run` method)
- `src/tunacode/ui/app.py` (update `write_shell_output` type hint if needed)

---

### Task 3: Style mode-active CSS Class
**ID:** T3 | **Owner:** claude | **Estimate:** M2 | **Deps:** None

Add CSS styling for `mode-active` class to make status bar mode indication visually distinct.

**Acceptance test:** Status bar `[bash mode]` text has distinct styling (bold, color, background).

**Files touched:**
- `src/tunacode/ui/styles/layout.tcss` or `theme-nextstep.tcss`

---

### Task 4: Integration Testing
**ID:** T4 | **Owner:** claude | **Estimate:** M3 | **Deps:** T2, T3

Verify end-to-end flow: `!` prefix → mode activation → command execution → panel output → mode deactivation.

**Acceptance test:** Manual test confirms full flow works as expected.

**Files touched:**
- `tests/` (add basic shell panel test if needed)

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| **BashRenderer format mismatch:** Shell output doesn't match expected parse format | Medium | Test parser with shell-specific edge cases; format string carefully |
| **CSS conflicts:** New styles may conflict with existing theme | Low | Test against both dracula and NeXTSTEP themes |
| **Type compatibility:** `RenderableType` may need import changes | Low | Verify Rich imports work in all consumers |

## Test Strategy

At most ONE new test per task, only for validation of main coding work.

**T4 (Integration Test):**
```python
def test_shell_command_produces_panel():
    """Verify !shell command produces 4-zone NeXTSTEP panel."""
    # Execute shell command via ShellRunner
    # Verify output is Panel (not plain Text)
    # Verify panel contains command, exit code, output
```

## References

### Code References
- **BashRenderer (reuse this):** `src/tunacode/ui/renderers/tools/bash.py:1-242`
- **BashRenderer.parse_result format:** `src/tunacode/ui/renderers/tools/bash.py:42-98`
- **Base 4-zone pattern:** `src/tunacode/ui/renderers/tools/base.py:375-441`
- **Shell runner protocol:** `src/tunacode/ui/shell_runner.py:20-27`
- **Shell execution (modify this):** `src/tunacode/ui/shell_runner.py:94-129`
- **Status bar mode:** `src/tunacode/ui/widgets/status_bar.py:90-98`

### Key Insight
The `BashRenderer` already implements the complete 4-zone pattern with:
- Zone 1: Command + exit status (`build_header`)
- Zone 2: cwd + timeout (`build_params`)
- Zone 3: stdout/stderr with syntax highlighting (`build_viewport`)
- Zone 4: Line counts, duration (`build_status`)

No new renderer needed. Just format shell output to match `BashRenderer.parse_result()` expected format.

## Final Gate

**Output Summary:**
- Plan saved to: `memory-bank/plan/2026-01-10_09-40-00_shell_panel_nextstep_standardization.md`
- Milestones: 3 (Protocol/Wiring, Enhancement, Integration)
- Tasks: 4 (protocol, wiring, CSS, testing)

**Next Command:**
```bash
/execute "memory-bank/plan/2026-01-10_09-40-00_shell_panel_nextstep_standardization.md"
```

**Developer Ready-Check:**
- ✅ All tasks have clear acceptance criteria
- ✅ File locations specified with line numbers
- ✅ Dependencies between tasks explicit
- ✅ Reference implementation identified (BashRenderer)
- ✅ Non-goals defined to prevent scope creep
- ✅ DRY principle followed (no duplicate renderer code)

---

## Execution Log

### 2026-01-10 Session

**Commit:** `41ca17d` on branch `bash-shell-panel`

#### Task 1: Update ShellRunnerHost Protocol ✅
- Added `from rich.console import RenderableType` import
- Changed protocol: `write_shell_output(self, renderable: Text)` → `write_shell_output(self, renderable: RenderableType)`
- Backward compatible (Text is subtype of RenderableType)

#### Task 2: Wire ShellRunner to BashRenderer ✅
- Added imports: `os`, `time`, `render_bash`
- Changed stderr capture from combined (`STDOUT`) to separate (`PIPE`)
- Added `_format_shell_panel()` helper method to format output for BashRenderer
- Updated `_run()` to track duration, capture stdout/stderr separately, produce panel
- Updated `_on_done()` error handler to also use panel format
- Updated `app.py`: added `RenderableType` import, changed `write_shell_output` signature, added `expand=True` to RichLog.write()

**Files modified:**
- `src/tunacode/ui/shell_runner.py`
- `src/tunacode/ui/app.py`

#### Task 3: Style mode-active CSS Class ✅
- Added base `.mode-active` style in `widgets.tcss`: bold teal text (#4ec9b0)
- Added NeXTSTEP override in `theme-nextstep.tcss`: dark background (#3a3a3a) with teal text
- Matches Editor bash-mode border color for visual consistency

**Commit:** `bb750d4`

**Files modified:**
- `src/tunacode/ui/styles/widgets.tcss`
- `src/tunacode/ui/styles/theme-nextstep.tcss`

#### Task 4: Integration Testing ✅
- Verified imports work without error
- All files pass ruff checks

### Session Summary

| Task | Status | Commit |
|------|--------|--------|
| T1: Protocol update | ✅ | `41ca17d` |
| T2: BashRenderer wiring | ✅ | `41ca17d` |
| T3: CSS styling | ✅ | `bb750d4` |
| T4: Integration test | ✅ | — |

**Branch:** `bash-shell-panel`
**Total commits:** 2
**Files modified:** 4
**Next:** Merge to master

### Known Issues

**Issue #225:** Shell error handling in `_on_done` callback needs improvement
- Uses placeholder `"(shell error)"` as command
- Loses context about original command
- See: https://github.com/alchemiststudiosDOTai/tunacode/issues/225

### Context Preserved
- `.claude/JOURNAL.md` - Full session narrative
- `CLAUDE.md` - Quick reference entry added
