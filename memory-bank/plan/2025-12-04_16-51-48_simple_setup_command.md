---
title: "Simple --setup Command – Plan"
phase: Plan
date: "2025-12-04_16-51-48"
owner: "Claude Agent"
parent_research: "memory-bank/research/2025-12-04_16-46-37_simple_setup_command.md"
git_commit_at_plan: "8cf2fc0"
tags: [plan, setup, cli, configuration]
---

## Goal

**Singular Objective:** Add `tunacode --setup` CLI flag that launches a simple TUI wizard allowing users to select a provider, model, and enter an API key—then saves config and starts the REPL.

**Non-Goals:**
- Dynamic fetching from models.dev (future enhancement)
- Multi-provider configuration in one session
- Azure/complex provider support
- Refactoring existing setup.py (reuse what exists)

## Scope & Assumptions

### In Scope
- Add `--setup` flag to CLI entry point (`main.py`)
- Launch existing `SetupWizardScreen` when flag is set
- Ensure config saves correctly and app starts after setup

### Out of Scope
- New providers beyond what's already in `setup.py` (openrouter, openai, anthropic, google)
- models.dev API integration
- Modifying PROVIDER_CONFIG dynamically
- Adding `base_url` to config (not needed for existing providers)

### Assumptions
- Existing `SetupWizardScreen` in `screens/setup.py` is functional
- User has terminal with TUI support
- Typer CLI framework is correctly configured

### Constraints
- Minimal code changes (< 20 lines added)
- No new dependencies
- Must work with existing config structure

## Deliverables (DoD)

| Artifact | Acceptance Criteria |
|----------|---------------------|
| `--setup` CLI flag | `tunacode --setup` launches setup wizard |
| Setup flow completion | After saving, app starts REPL normally |
| Config persistence | `~/.config/tunacode.json` contains selected provider/model/key |

## Readiness (DoR)

- [x] Research document completed
- [x] Codebase analyzed
- [x] Existing SetupWizardScreen located at `src/tunacode/ui/screens/setup.py`
- [x] CLI entry point identified at `src/tunacode/ui/main.py:40-72`

## Milestones

| ID | Milestone | Description |
|----|-----------|-------------|
| M1 | CLI Flag | Add `--setup` option to Typer command |
| M2 | Screen Launch | Wire flag to launch SetupWizardScreen |
| M3 | Verification | Test end-to-end flow works |

## Work Breakdown (Tasks)

### Task 1: Add --setup CLI Flag
**Summary:** Add `setup` boolean option to `main()` function in main.py
**Owner:** Agent
**Dependencies:** None
**Target Milestone:** M1

**Files/Interfaces:**
- `src/tunacode/ui/main.py:40-50` - Add Typer option

**Implementation:**
```python
setup: bool = typer.Option(False, "--setup", help="Run setup wizard")
```

**Acceptance Tests:**
- [ ] `tunacode --help` shows `--setup` flag
- [ ] Flag parses without error

---

### Task 2: Wire Setup Flow in async_main
**Summary:** Add conditional logic to launch SetupWizardScreen when `--setup` is True
**Owner:** Agent
**Dependencies:** Task 1
**Target Milestone:** M2

**Files/Interfaces:**
- `src/tunacode/ui/main.py:55-72` - Modify async_main flow
- Import `SetupWizardScreen` from `tunacode.ui.screens.setup`

**Implementation Pattern:**
```python
# In async_main, after StateManager init, before run_textual_repl:
if setup:
    # Run app with setup screen first
    # Then continue to normal REPL
```

**Acceptance Tests:**
- [ ] `tunacode --setup` shows provider selection screen
- [ ] After setup completion, REPL starts normally

---

### Task 3: End-to-End Verification
**Summary:** Manually test the complete flow
**Owner:** Agent
**Dependencies:** Task 1, Task 2
**Target Milestone:** M3

**Acceptance Tests:**
- [ ] Fresh install: `tunacode --setup` → select provider → enter key → saves config → REPL starts
- [ ] Existing config: `tunacode --setup` → can reconfigure → overwrites config → REPL starts
- [ ] Normal flow: `tunacode` (without --setup) works as before

## Risks & Mitigations

| Risk | Impact | Likelihood | Mitigation | Trigger |
|------|--------|------------|------------|---------|
| SetupWizardScreen not wired correctly | High | Low | Follow existing screen mounting patterns | Screen doesn't appear |
| Config not saved properly | High | Low | Existing save logic is tested | Config file empty/missing |
| REPL doesn't start after setup | Medium | Low | Ensure screen dismissal triggers REPL | App exits after setup |

## Test Strategy

**ONE test only** (as per constraint):

```python
# tests/test_cli_setup_flag.py
def test_setup_flag_exists():
    """Verify --setup flag is registered in CLI."""
    from typer.testing import CliRunner
    from tunacode.ui.main import app

    runner = CliRunner()
    result = runner.invoke(app, ["--help"])
    assert "--setup" in result.output
```

**Manual verification required for TUI flow** (no automated TUI testing).

## References

### Research Document
- `memory-bank/research/2025-12-04_16-46-37_simple_setup_command.md`

### Key Codebase Files
- `src/tunacode/ui/main.py:40-72` - CLI entry point
- `src/tunacode/ui/screens/setup.py` - Existing SetupWizardScreen
- `src/tunacode/configuration/defaults.py` - Default config values

### Patterns
- Screen mounting: `app.push_screen(SetupWizardScreen(state_manager))`
- Typer options: `typer.Option(default, "--flag", help="...")`

---

## Alternative Option: Inline Setup (Not Recommended)

If the existing `SetupWizardScreen` proves problematic, an alternative is to prompt directly in the terminal before TUI launch:

```python
if setup:
    provider = input("Provider [openrouter]: ") or "openrouter"
    api_key = input("API Key: ")
    # Save config directly
    # Then launch REPL
```

**Why not recommended:** Less polished UX, loses dropdown selection, doesn't reuse existing code.

---

## Final Gate

| Check | Status |
|-------|--------|
| Plan path | `memory-bank/plan/2025-12-04_16-51-48_simple_setup_command.md` |
| Milestones count | 3 |
| Gates | CLI flag exists → Setup screen launches → Config saves → REPL starts |
| Estimated LOC | ~15 lines |

**Next command:** `/context-engineer:execute "memory-bank/plan/2025-12-04_16-51-48_simple_setup_command.md"`
