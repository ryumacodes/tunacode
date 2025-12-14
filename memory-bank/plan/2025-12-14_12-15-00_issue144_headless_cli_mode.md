---
title: "Issue #144 – Headless CLI Mode Plan"
phase: Plan
date: "2025-12-14T12:15:00Z"
owner: "agent"
parent_research: "memory-bank/research/2025-12-14_11-30-00_issue144_headless_cli_mode.md"
git_commit_at_plan: "7670377"
tags: [plan, headless, cli, issue-144, benchmark]
---

## Goal

**Add a `tunacode run "<prompt>"` command that executes TunaCode in non-interactive headless mode for benchmark automation (Harbor tbench integration).**

Non-goals:
- MCP server support in headless mode (future issue)
- Session persistence for headless runs (future issue)
- Streaming progress indicators to stderr (future issue)

## Scope & Assumptions

### In Scope
- New `@app.command("run")` in `src/tunacode/ui/main.py`
- `--auto-approve` flag reusing existing `session.yolo = True`
- `--output-json` flag for trajectory serialization
- `--timeout` flag with `asyncio.wait_for()` wrapping
- `--cwd` flag for working directory
- `--model` flag for model selection
- Exit code 0 (success) / 1 (failure)

### Out of Scope
- Detailed exit code taxonomy (timeout=2, auth=3, etc.) - defer to future PR
- Harbor tbench JSON schema validation - Harbor team will validate
- Session history persistence for headless runs

### Assumptions
- Harbor tbench consumes stdout JSON (not stderr)
- `session.messages` items have `.model_dump()` (Pydantic models)
- ToolHandler initialization pattern from TUI is correct

### Constraints
- Must NOT break existing TUI mode
- Must reuse global `state_manager` pattern (per PR #170 lesson: fresh StateManager breaks API key access)

## Deliverables (DoD)

| Artifact | Acceptance Criteria |
|----------|---------------------|
| `tunacode run` command | `tunacode run "hello" --auto-approve` completes without TUI |
| JSON output | `--output-json` produces valid JSON to stdout |
| Auto-approve | `--auto-approve` skips all tool confirmations via yolo mode |
| Exit codes | Returns 0 on success, 1 on any failure |
| No TUI deps | No curses/textual imports in headless path |

## Readiness (DoR)

| Precondition | Status |
|--------------|--------|
| Research doc complete | Done |
| `process_request()` headless-ready | Verified - all callbacks optional |
| `YoloModeRule` exists | Verified at rules.py:47-54 |
| `session.yolo` flag exists | Verified at state.py:47 |
| Typer CLI framework | In place at main.py:15 |

## Milestones

### M1: Core Headless Command
- Add `@app.command("run")` with basic execution
- Wire `--auto-approve` to `session.yolo = True`
- Return exit codes

### M2: Output & Options
- Implement `--output-json` trajectory serialization
- Add `--timeout`, `--cwd`, `--model` options

## Work Breakdown (Tasks)

### Task 1: Add `run_headless` command skeleton
- **Owner:** agent
- **Dependencies:** None
- **Milestone:** M1
- **Files:** `src/tunacode/ui/main.py`

**Acceptance Tests:**
- `tunacode run "print hello"` executes without launching TUI
- `tunacode --help` shows `run` command

**Implementation Notes:**
- Add imports: `json`, `sys`, `process_request`, `ModelName`
- Use global `state_manager` (do NOT create fresh instance per PR #170 pattern)
- Set `state_manager.session.yolo = True` when `--auto-approve`

### Task 2: Wire process_request with null callbacks
- **Owner:** agent
- **Dependencies:** Task 1
- **Milestone:** M1
- **Files:** `src/tunacode/ui/main.py`

**Acceptance Tests:**
- Agent executes prompt and returns result
- No confirmation prompts when `--auto-approve` set
- Exit code 0 on success

**Implementation Notes:**
- Call `process_request()` with `tool_callback=None`, `streaming_callback=None`
- Wrap in `asyncio.wait_for()` for timeout support
- Catch exceptions and return exit code 1

### Task 3: Implement --output-json trajectory
- **Owner:** agent
- **Dependencies:** Task 2
- **Milestone:** M2
- **Files:** `src/tunacode/ui/main.py`

**Acceptance Tests:**
- `tunacode run "test" --auto-approve --output-json` outputs valid JSON
- JSON contains `messages`, `tool_calls`, `usage`, `success` fields

**Implementation Notes:**
- Serialize `state_manager.session.messages` via `.model_dump()`
- Include `state_manager.session.tool_calls`
- Include `state_manager.session.session_total_usage`

### Task 4: Add --cwd and --model options
- **Owner:** agent
- **Dependencies:** Task 2
- **Milestone:** M2
- **Files:** `src/tunacode/ui/main.py`

**Acceptance Tests:**
- `--cwd /tmp` changes working directory before execution
- `--model anthropic/claude-sonnet-4-20250514` uses specified model

**Implementation Notes:**
- `os.chdir(cwd)` before execution
- Set `state_manager.session.current_model = model`

## Risks & Mitigations

| Risk | Impact | Likelihood | Mitigation | Trigger |
|------|--------|------------|------------|---------|
| Fresh StateManager breaks API keys | High | Medium | Use global singleton per PR #170 | Task 1 |
| Message serialization fails | Medium | Low | Verify `.model_dump()` exists, add fallback | Task 3 |
| Harbor JSON schema mismatch | Medium | Low | Document output format, iterate with Harbor team | Task 3 |

## Test Strategy

**ONE boundary test:**

```python
# tests/test_headless_cli.py
def test_run_command_executes_without_tui():
    """Verify headless mode doesn't import Textual."""
    result = subprocess.run(
        ["tunacode", "run", "echo test", "--auto-approve", "--timeout", "10"],
        capture_output=True,
        text=True,
        timeout=15,
    )
    # Should complete without TUI (exit code 0 or model error, not import error)
    assert "Textual" not in result.stderr
    assert result.returncode in (0, 1)  # 0=success, 1=model/network error is OK
```

This single test validates:
1. CLI command exists and runs
2. No TUI framework is invoked
3. Exit codes work

## References

- **Research:** `memory-bank/research/2025-12-14_11-30-00_issue144_headless_cli_mode.md`
- **GitHub Issue:** https://github.com/alchemiststudiosDOTai/tunacode/issues/144
- **PR #170 Pattern:** Commit `67f0414` - always use parent StateManager, not fresh instance
- **Key Files:**
  - `src/tunacode/ui/main.py:15` - Typer app
  - `src/tunacode/core/agents/main.py:526` - `process_request()`
  - `src/tunacode/core/state.py:47` - `session.yolo`
  - `src/tunacode/tools/authorization/rules.py:47` - `YoloModeRule`

---

## Alternative Approach (Not Recommended)

**Fresh StateManager per run:** Create isolated `StateManager()` for each headless invocation to prevent state pollution.

**Why rejected:** PR #170 demonstrated this breaks API key access and configuration inheritance. The singleton pattern is safer.

---

## Final Gate Summary

| Item | Value |
|------|-------|
| Plan Path | `memory-bank/plan/2025-12-14_12-15-00_issue144_headless_cli_mode.md` |
| Milestones | 2 (M1: Core Command, M2: Output & Options) |
| Tasks | 4 |
| Test Count | 1 boundary test |
| Files Modified | 1 (`src/tunacode/ui/main.py`) |

**Next Command:** `/context-engineer:execute "memory-bank/plan/2025-12-14_12-15-00_issue144_headless_cli_mode.md"`
