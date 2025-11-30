# Research – Rich/prompt_toolkit to Textual TUI Migration: Deletion & Reorganization Map

**Date:** 2025-11-30
**Owner:** Claude (context-engineer:research)
**Phase:** Research
**Branch:** textual_repl
**Commit:** b1ae6f0af8740c4350ebbe3ea79d0c5833b4122d
**Last Updated:** 2025-11-30T17:45
**Last Updated Note:** Added setup/, tutorial/ to deletion scope; addressed junior dev review feedback

---

## Goal

Map all code from the old Rich/prompt_toolkit REPL that can be deleted now that the Textual TUI is in place, identify what must be preserved, and outline the reorganization plan.

---

## Executive Summary

The migration from Rich/prompt_toolkit REPL to Textual TUI is well underway. The new TUI (`cli/textual_repl.py`, `cli/widgets.py`, `cli/screens.py`) is functional.

**DECISIONS:**
1. Remove slash commands entirely - not wired to TUI, can add back later
2. Remove interactive setup flows - users can edit config files for now
3. Remove tutorial system - can rebuild on Textual later

**Updated Key Numbers:**
- **Files to delete:** ~55 files (~7,000+ lines)
- **Directories to delete:** `ui/`, `cli/commands/`, `cli/repl_components/`, `core/setup/`, `tutorial/`
- **Pure backend to KEEP:** `core/agents/`, `core/llm/`, `core/logging/`, `tools/`, `services/`, `utils/`, `configuration/`

---

## Junior Dev Review - Issues Addressed

### Issue 1: Dead stubs post-migration
> `tool_executor.py`, `output_display.py`, `error_recovery.py` not referenced; `tool_ui.py` only pulled by dead executor

**Status:** ✅ Already in deletion list. Confirmed dead.

### Issue 2: Broken ParseToolsCommand
> `ParseToolsCommand` in `debug.py` calls `_tool_handler` from `repl.py` which raises immediately

**Status:** ✅ Entire `cli/commands/` being deleted. This broken command goes with it.

### Issue 3: prompt_toolkit still active in setup/tutorial
> `input.py`, `prompt_manager.py`, `keybindings.py`, `lexers.py`, `model_selector.py` feed setup flows and tutorial

**Status:** ✅ Decision made to delete `core/setup/` and `tutorial/` entirely. Interactive setup can be rebuilt on Textual later. Users edit config files for now.

### Issue 4: Hybrid output path
> `output.py` registers Textual sink, `main.py` calls `ui.version`/`ui.error` before TUI boots

**Status:** ✅ Will remove these calls from `main.py` and delete `output.py`. TUI handles all output.

### Issue 5: No tests for Textual REPL
> Nothing covers `textual_repl.py`, `widgets.py`, `screens.py`

**Status:** ⚠️ Accepted risk. Existing tests in repo. Can rollback via git if needed. Tests can be added post-cleanup.

---

## Findings

### 1. DELETE ENTIRE DIRECTORIES

#### `src/tunacode/ui/` - DELETE ALL (18 files, ~2,885 lines)

| File | Lines | Purpose | Status |
|------|-------|---------|--------|
| `ui/__init__.py` | 1 | Package marker | DELETE |
| `ui/prompt_manager.py` | 139 | prompt_toolkit PromptSession | DELETE |
| `ui/keybindings.py` | 53 | prompt_toolkit KeyBindings | DELETE |
| `ui/validators.py` | 23 | prompt_toolkit Validator | DELETE |
| `ui/lexers.py` | 45 | prompt_toolkit Lexer | DELETE |
| `ui/model_selector.py` | 395 | prompt_toolkit model picker | DELETE |
| `ui/utils.py` | 3 | Rich Console instance | DELETE |
| `ui/path_heuristics.py` | 91 | Directory skip lists | DELETE |
| `ui/decorators.py` | 59 | async-to-sync wrapper | DELETE |
| `ui/logging_compat.py` | 44 | UILogger compat layer | DELETE |
| `ui/console.py` | 178 | UI facade | DELETE |
| `ui/output.py` | 246 | Rich output + sink | DELETE |
| `ui/panels.py` | 538 | Rich panels | DELETE |
| `ui/tool_ui.py` | 234 | Tool confirmation UI | DELETE |
| `ui/input.py` | 115 | prompt_toolkit input | DELETE |
| `ui/completers.py` | 590 | Completers | DELETE (extract 2 funcs first) |
| `ui/constants.py` | 16 | UI constants | DELETE |
| `ui/tool_descriptions.py` | 115 | Tool name strings | MIGRATE to `utils/` |

#### `src/tunacode/cli/commands/` - DELETE ALL (19 files, ~2,462 lines)

```
cli/commands/           # ENTIRE DIRECTORY
├── __init__.py
├── base.py
├── registry.py
└── implementations/
    ├── __init__.py
    ├── command_reload.py   # /command-reload
    ├── conversation.py     # /compact
    ├── debug.py            # /yolo, /dump, /thoughts, /iterations, /fix, /parsetools (BROKEN)
    ├── development.py      # /branch, /init
    ├── model.py            # /model
    ├── quickstart.py       # /quickstart
    ├── system.py           # /help, /clear, /refresh, /update, /streaming
    └── template.py         # /template
```

#### `src/tunacode/cli/repl_components/` - DELETE ALL (5 files, ~377 lines)

| File | Lines | Status |
|------|-------|--------|
| `__init__.py` | 10 | DELETE |
| `tool_executor.py` | 86 | DELETE (dead, confirmed) |
| `output_display.py` | 44 | DELETE (dead, confirmed) |
| `error_recovery.py` | 169 | DELETE (dead, confirmed) |
| `command_parser.py` | 68 | MIGRATE to `cli/` then DELETE dir |

#### `src/tunacode/core/setup/` - DELETE ALL (9 files, ~1,000 lines)

```
core/setup/             # ENTIRE DIRECTORY - prompt_toolkit dependent
├── __init__.py
├── agent_setup.py
├── base.py
├── config_setup.py     # Uses ui/input.py, prompt_toolkit
├── config_wizard.py    # Uses ui/input.py, model_selector
├── coordinator.py
├── environment_setup.py
└── template_setup.py
```

**Rationale:** Interactive setup uses prompt_toolkit throughout. Delete now, rebuild on Textual later. Users can edit `~/.config/tunacode/config.yaml` manually.

#### `src/tunacode/tutorial/` - DELETE ALL (4 files, ~367 lines)

```
tutorial/               # ENTIRE DIRECTORY
├── __init__.py
├── content.py
├── manager.py          # Uses prompt_toolkit input
└── steps.py
```

**Rationale:** Tutorial depends on prompt_toolkit input. Can rebuild as Textual walkthrough later.

---

### 2. FILES TO KEEP

#### Core TUI (Keep as-is)
```
cli/
├── __init__.py
├── main.py              # Entry point (remove ui imports)
├── repl.py              # Shim to textual_repl
├── textual_repl.py      # Main TUI app
├── widgets.py           # Custom widgets
├── screens.py           # Modal screens
├── textual_repl.tcss    # Styles
└── command_parser.py    # (migrated from repl_components/)
```

#### Backend (100% preserved)
```
src/tunacode/
├── configuration/       # Config handling
├── utils/               # Utilities
├── services/            # Service layer
├── tools/               # Tool implementations
├── templates/           # Prompt templates
├── prompts/             # System prompts
├── core/
│   ├── agents/          # Agent logic (remove ui imports)
│   ├── llm/             # LLM clients
│   ├── logging/         # Logging
│   ├── background/      # Background tasks
│   ├── token_usage/     # Token tracking
│   ├── state.py
│   ├── tool_handler.py
│   ├── tool_authorization.py
│   └── code_index.py
├── constants.py
├── types.py
├── exceptions.py
└── setup.py
```

---

### 3. PRE-DELETION MIGRATIONS

Before deleting, extract/migrate these:

#### 3.1 Extract from `ui/completers.py` → `utils/completion_utils.py`
```python
# Lines ~546-590 - Used by widgets.py for @file completion
def textual_complete_paths(prefix: str) -> list[str]: ...
def replace_token(text: str, start: int, end: int, replacement: str) -> str: ...
```

**Note:** `get_command_names()` no longer needed since commands are being deleted.

#### 3.2 Move `cli/repl_components/command_parser.py` → `cli/command_parser.py`
- Update import in `textual_repl.py`

#### 3.3 Migrate `ui/tool_descriptions.py` → `utils/tool_descriptions.py`
- Pure string data, no UI dependencies
- Used by agent system for status text

---

### 4. BACKEND UI ENTANGLEMENTS (Must Fix Before Delete)

These backend files import from `ui/`:

| File | Import | Fix |
|------|--------|-----|
| `core/agents/main.py` | `tunacode.ui.console` | Remove import, use callbacks |
| `core/agents/node_processor.py` | `tunacode.ui.console` | Remove import, use callbacks |
| `core/agents/response_handler.py` | `tunacode.ui.console` | Remove import, use callbacks |
| `cli/main.py` | `tunacode.ui.console` | Remove `ui.version()`, `ui.error()` calls |

**Note:** `core/setup/` files also import ui, but entire directory is being deleted.

---

## Deletion Roadmap

### Phase 1: Pre-deletion Migrations
```bash
# 1. Create utils/completion_utils.py
# Extract textual_complete_paths, replace_token from ui/completers.py

# 2. Move command_parser
mv src/tunacode/cli/repl_components/command_parser.py src/tunacode/cli/command_parser.py

# 3. Move tool_descriptions
mv src/tunacode/ui/tool_descriptions.py src/tunacode/utils/tool_descriptions.py
```

### Phase 2: Remove Backend UI Imports
```bash
# Update these files to remove ui.console imports:
# - core/agents/main.py
# - core/agents/node_processor.py
# - core/agents/response_handler.py
# - cli/main.py
```

### Phase 3: Delete Everything
```bash
# Delete ui/ directory
rm -rf src/tunacode/ui/

# Delete commands/ directory
rm -rf src/tunacode/cli/commands/

# Delete repl_components/ directory
rm -rf src/tunacode/cli/repl_components/

# Delete setup/ directory
rm -rf src/tunacode/core/setup/

# Delete tutorial/ directory
rm -rf src/tunacode/tutorial/
```

### Phase 4: Cleanup
```bash
# Run ruff to find broken imports
ruff check src/tunacode/

# Fix any remaining references

# Run tests to verify
hatch run test
```

---

## Summary Table (Final)

| Category | Files | Lines | Action |
|----------|-------|-------|--------|
| `ui/` directory | 18 | ~2,885 | DELETE (migrate 2 files first) |
| `cli/commands/` directory | 19 | ~2,462 | DELETE |
| `cli/repl_components/` | 5 | ~377 | DELETE (move 1 file first) |
| `core/setup/` directory | 9 | ~1,000 | DELETE |
| `tutorial/` directory | 4 | ~367 | DELETE |
| Backend UI imports | 4 | n/a | REFACTOR to callbacks |
| **TOTAL DELETION** | **55** | **~7,091** | Phased approach |

---

## What We Lose (Acceptable)

| Feature | Old Implementation | Replacement |
|---------|-------------------|-------------|
| `/help` | Rich panel | Future: help modal |
| `/clear` | Screen + history clear | `Ctrl+L` keybinding |
| `/model` | Interactive selector | Natural language |
| `/yolo` | Toggle flag | Keybinding |
| `/compact` | Conversation pruning | Natural language |
| `/parsetools` | Debug command | Was already broken |
| Interactive setup | prompt_toolkit wizard | Edit config file |
| Tutorial | Step-by-step prompts | Documentation |

**Philosophy:** Start minimal. Add back what users actually request.

---

## Risk Mitigation

1. **No Textual tests** - Accepted. Can rollback via git. Tests added post-cleanup.
2. **No interactive setup** - Users edit config. Can rebuild wizard on Textual.
3. **No tutorial** - Point to docs. Can rebuild on Textual.
4. **Broken during cleanup** - Work on branch, test before merge.

---

## References

### Files Analyzed
- `src/tunacode/ui/` - 18 files, ~2,885 lines
- `src/tunacode/cli/commands/` - 19 files, ~2,462 lines
- `src/tunacode/cli/repl_components/` - 5 files, ~377 lines
- `src/tunacode/core/setup/` - 9 files, ~1,000 lines
- `src/tunacode/tutorial/` - 4 files, ~367 lines

### Related Research
- `memory-bank/research/2025-11-29_14-53-40_rich-to-textual-migration.md`
- `memory-bank/research/2025-11-29_textual-tui-architecture-and-style-guide.md`
- `memory-bank/research/2025-11-30_13-45-00_tui-architecture-map.md`
