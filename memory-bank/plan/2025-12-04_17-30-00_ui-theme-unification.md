---
title: "UI Theme Unification – Plan"
phase: Plan
date: "2025-12-04T17:30:00"
owner: "Claude Agent"
parent_research: "memory-bank/research/2025-12-04_ui-theme-unification.md"
git_commit_at_plan: "101d459"
tags: [plan, ui, theming, consistency]
---

## Goal

**Eliminate all hardcoded color strings from the TunaCode UI by replacing them with references to the centralized `UI_COLORS` dictionary.**

This is a focused refactoring task: 24 hardcoded color strings across 3 files will be replaced with symbolic references to `UI_COLORS` keys, ensuring consistent theming and future maintainability.

**Non-goals:**
- Creating new documentation files
- Changing the actual color values
- Refactoring the TCSS stylesheet system
- Adding new UI components

## Scope & Assumptions

**In Scope:**
- Replace hardcoded color strings in `app.py`, `resource_bar.py`, `commands/__init__.py`
- Create a small `styles.py` module for Rich-compatible style constants
- Verify visual consistency after changes

**Out of Scope:**
- Consolidating inline `DEFAULT_CSS` into `app.tcss` (future enhancement)
- Creating design system documentation
- Modifying the `UI_COLORS` values themselves

**Assumptions:**
- Rich's style strings accept hex color codes (verified: they do)
- All replacements are 1:1 substitutions (same visual appearance)
- Tests are not required for style-only changes (no logic changes)

## Deliverables (DoD)

| Artifact | Acceptance Criteria |
|----------|---------------------|
| `src/tunacode/ui/styles.py` | New file with Rich-compatible style constants derived from `UI_COLORS` |
| `src/tunacode/ui/app.py` | Zero hardcoded color strings; all use `UI_COLORS` or `styles.py` |
| `src/tunacode/ui/widgets/resource_bar.py` | Zero hardcoded color strings |
| `src/tunacode/ui/commands/__init__.py` | Zero hardcoded color strings |
| Visual verification | TUI displays correctly with no visual regressions |

## Readiness (DoR)

- [x] Research document completed identifying all occurrences
- [x] `UI_COLORS` dict exists with comprehensive color definitions
- [x] Pattern already established in `renderers/panels.py` for reference
- [x] Git repository clean enough to proceed (changes in staging area are unrelated)

## Milestones

| ID | Milestone | Description |
|----|-----------|-------------|
| M1 | Create styles module | Create `styles.py` with Rich-compatible constants |
| M2 | Refactor resource_bar | Replace 7 occurrences in resource_bar.py |
| M3 | Refactor commands | Replace 2 occurrences in commands/__init__.py |
| M4 | Refactor app.py | Replace 15 occurrences in app.py |
| M5 | Verify and commit | Run TUI, verify visuals, commit changes |

## Work Breakdown (Tasks)

### Task 1: Create `src/tunacode/ui/styles.py`
**Summary:** Create a module exporting Rich-compatible style constants
**Milestone:** M1
**Dependencies:** None
**Files:** `src/tunacode/ui/styles.py` (new)

**Acceptance Tests:**
- File imports successfully
- Constants reference `UI_COLORS` values
- Includes all needed style combinations (primary, accent, success, warning, error, muted)

**Implementation:**
```python
from tunacode.constants import UI_COLORS

# Rich Text style strings (single colors)
STYLE_PRIMARY = UI_COLORS["primary"]
STYLE_ACCENT = UI_COLORS["accent"]
STYLE_SUCCESS = UI_COLORS["success"]
STYLE_WARNING = UI_COLORS["warning"]
STYLE_ERROR = UI_COLORS["error"]
STYLE_MUTED = UI_COLORS["muted"]

# Composite styles
STYLE_HEADING = f"bold {STYLE_ACCENT}"
STYLE_SUBHEADING = f"bold {STYLE_PRIMARY}"
```

---

### Task 2: Refactor `resource_bar.py`
**Summary:** Replace 7 hardcoded color strings
**Milestone:** M2
**Dependencies:** Task 1
**Files:** `src/tunacode/ui/widgets/resource_bar.py`

**Replacements:**
| Line | Current | Replacement |
|------|---------|-------------|
| 54 | `"green"` | `STYLE_SUCCESS` |
| 56 | `"yellow"` | `STYLE_WARNING` |
| 57 | `"red"` | `STYLE_ERROR` |
| 79 | `"cyan"` | `STYLE_PRIMARY` |
| 80 | `"dim"` | `STYLE_MUTED` |
| 83 | `"dim"` | `STYLE_MUTED` |
| 84 | `"green"` | `STYLE_SUCCESS` |

**Acceptance Tests:**
- No hardcoded color strings remain
- Resource bar displays correctly

---

### Task 3: Refactor `commands/__init__.py`
**Summary:** Replace 2 hardcoded color strings
**Milestone:** M3
**Dependencies:** Task 1
**Files:** `src/tunacode/ui/commands/__init__.py`

**Replacements:**
| Line | Current | Replacement |
|------|---------|-------------|
| 33 | `style="cyan"` | `style=STYLE_PRIMARY` |
| 87 | `style="cyan"` | `style=STYLE_PRIMARY` |

**Acceptance Tests:**
- No hardcoded color strings remain
- `/help` and `/models` commands display correctly

---

### Task 4: Refactor `app.py`
**Summary:** Replace 15 hardcoded color strings
**Milestone:** M4
**Dependencies:** Task 1
**Files:** `src/tunacode/ui/app.py`

**Replacements:**
| Line | Current | Replacement |
|------|---------|-------------|
| 120 | `"magenta bold"` | `STYLE_HEADING` |
| 121 | `"dim"` | `STYLE_MUTED` |
| 122 | `"cyan"` | `STYLE_PRIMARY` |
| 203 | `"cyan"` | `STYLE_PRIMARY` |
| 204 | `"dim cyan"` | `f"dim {STYLE_PRIMARY}"` |
| 262 | `"red"` | `STYLE_ERROR` |
| 290 | `"bold cyan"` | `STYLE_SUBHEADING` |
| 296 | `"dim"` | `STYLE_MUTED` |
| 300 | `"bold green"` | `f"bold {STYLE_SUCCESS}"` |
| 302 | `"bold yellow"` | `f"bold {STYLE_WARNING}"` |
| 304 | `"bold red"` | `f"bold {STYLE_ERROR}"` |
| 309 | `"cyan"` (border_style) | `STYLE_PRIMARY` |
| 324 | `"green"` | `STYLE_SUCCESS` |
| 327 | `"yellow"` | `STYLE_WARNING` |
| 330 | `"red"` | `STYLE_ERROR` |

**Acceptance Tests:**
- No hardcoded color strings remain
- Welcome message, user messages, and confirmation dialogs display correctly

---

### Task 5: Visual Verification
**Summary:** Run TUI and verify no visual regressions
**Milestone:** M5
**Dependencies:** Tasks 2, 3, 4
**Files:** None (verification only)

**Verification Steps:**
1. Run `tunacode` and verify welcome message styling
2. Type a message and verify user message styling
3. Run `/help` and verify table styling
4. Run `/models` and verify table styling
5. Observe resource bar color transitions (if possible)

**Acceptance Tests:**
- All UI elements render with correct colors
- No crashes or import errors

---

### Task 6: Commit Changes
**Summary:** Create atomic commit with all theme unification changes
**Milestone:** M5
**Dependencies:** Task 5

**Commit Message:**
```
refactor(ui): replace hardcoded colors with UI_COLORS references

- Create styles.py with Rich-compatible style constants
- Replace 24 hardcoded color strings across 3 files
- Improves theming consistency and maintainability
```

## Risks & Mitigations

| Risk | Impact | Likelihood | Mitigation | Trigger |
|------|--------|------------|------------|---------|
| Rich style string format incompatible | HIGH | LOW | Verify Rich accepts hex codes before starting | Task 1 fails import |
| Line numbers shifted since research | MEDIUM | MEDIUM | Use search/replace by content, not line number | Edits fail to match |
| Import cycle with constants.py | MEDIUM | LOW | styles.py only imports from constants, no reverse deps | Import error |

## Test Strategy

**No new tests required.**

This is a pure refactoring of style values with no logic changes. Visual verification is sufficient. The existing tool tests (`tests/test_tools.py`, `tests/test_tool_conformance.py`) will catch any import errors.

## References

- Research: `memory-bank/research/2025-12-04_ui-theme-unification.md`
- Constants: `src/tunacode/constants.py:110-124` (UI_COLORS definition)
- Pattern: `src/tunacode/ui/renderers/panels.py:28-41` (PANEL_STYLES example)

## Alternative Approach

**Option B: Inline UI_COLORS references without styles.py**

Instead of creating `styles.py`, directly use `UI_COLORS["primary"]` etc. in each file.

**Trade-offs:**
- Pro: No new file to maintain
- Con: More verbose, harder to add composite styles like "bold primary"
- Con: More imports needed in each file

**Recommendation:** Proceed with Option A (create styles.py) for cleaner code.

---

## Next Command

```
/context-engineer:execute "memory-bank/plan/2025-12-04_17-30-00_ui-theme-unification.md"
```
