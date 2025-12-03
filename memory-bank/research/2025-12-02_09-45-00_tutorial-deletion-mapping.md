# Research – Tutorial System Deletion Mapping

**Date:** 2025-12-02
**Owner:** Claude (context-engineer:research)
**Phase:** Research
**Branch:** textual_repl
**Commit:** 2577fa0
**Last Updated:** 2025-12-02T09:45
**Last Updated Note:** Initial comprehensive tutorial deletion mapping

---

## Goal

Map all tutorial-related code, dependencies, and configuration to understand what can be safely deleted as part of the major rewrite from Rich/prompt_toolkit to Textual TUI.

---

## Executive Summary

The tutorial system has **already been deleted** from the codebase. The `/src/tunacode/tutorial/` directory was removed in a previous commit as part of the Rich/prompt_toolkit to Textual migration. However, there remain **configuration remnants** and **unused references** that should be cleaned up to prevent confusion and technical debt.

**Key Findings:**
- Tutorial directory already deleted (4 files, ~367 lines removed)
- Configuration references remain but are non-functional
- No active code dependencies on tutorial system
- Safe to remove remaining tutorial-related configuration

---

## Current Tutorial State

### Tutorial Directory Status: **DELETED**
```
src/tunacode/tutorial/    # ALREADY DELETED in previous commit
├── __init__.py          # Was: Package marker
├── content.py           # Was: Tutorial content definitions
├── manager.py           # Was: Tutorial session manager (used prompt_toolkit)
└── steps.py             # Was: Tutorial step definitions
```

**Evidence from deletion map:** `memory-bank/research/2025-11-30_17-15-00_rich-prompt_toolkit-to-textual-deletion-map.md:139` lists `tutorial/ # ENTIRE DIRECTORY` for deletion.

---

## Remaining Tutorial-Related Code

### 1. Configuration Settings (`src/tunacode/utils/user_configuration.py`)

#### Tutorial Settings (Lines 109-111, 129-132)
```python
# _ensure_onboarding_defaults()
"enable_tutorial": True,     # Line 110

# initialize_first_time_user()
"enable_tutorial": True,     # Line 131
```

**Impact:** Non-functional stub settings. No code reads these values.

### 2. Configuration Descriptions (`src/tunacode/configuration/key_descriptions.py`)

#### Tutorial Setting Descriptions (Lines 209-231)
```python
"settings.enable_tutorial": "Enable interactive tutorial..."        # Lines 210-216
"settings.tutorial_declined": "Track if user declined tutorial..." # Lines 224-231
"settings.first_installation_date": "Track first installation..."  # Lines 217-223
```

**Impact:** Documentation for non-existent functionality.

### 3. Exception Class (`src/tunacode/exceptions.py`)

#### OnboardingError (Lines 160-170)
```python
class OnboardingError(Exception):
    """Raised when onboarding or tutorial processes fail."""
    pass
```

**Impact:** Defined but never raised or caught anywhere in codebase.

---

## Dependency Analysis

### Zero Active Dependencies
Based on comprehensive codebase analysis:

1. **No imports:** No files import from tutorial directory (already deleted)
2. **No function calls:** No code calls tutorial functions
3. **No conditional logic:** No code checks tutorial settings to control flow
4. **No tests:** No test files reference tutorial functionality
5. **No runtime usage:** Tutorial settings are written but never read

### Configuration-Only Remnants
The only remaining references are:
- Default setting initialization in user_configuration.py
- Setting descriptions in key_descriptions.py
- Unused exception class in exceptions.py

**All are safe to remove without affecting functionality.**

---

## Safe Deletion Strategy

### Phase 1: Remove Configuration Stubs
```bash
# Remove tutorial defaults from user_configuration.py
# - Lines 109-111: enable_tutorial default setting
# - Lines 129-132: enable_tutorial first-time user setting
```

### Phase 2: Remove Documentation
```bash
# Remove tutorial descriptions from key_descriptions.py
# - Lines 210-216: enable_tutorial description
# - Lines 217-223: first_installation_date description
# - Lines 224-231: tutorial_declined description
```

### Phase 3: Remove Unused Exception
```bash
# Remove OnboardingError from exceptions.py
# - Lines 160-170: Entire OnboardingError class
```

### Phase 4: Cleanup
```bash
# Run ruff to verify no broken references
ruff check --fix .

# Run tests to ensure no regressions
hatch run test
```

---

## Impact Assessment

### What Breaks: **Nothing**
- No active code depends on tutorial functionality
- Configuration settings are write-only (never read)
- Exception class is never used
- No users rely on tutorial (directory already deleted)

### What Improves: **Code Clarity**
- Removes confusing non-functional settings
- Eliminates dead code and technical debt
- Cleans up configuration schema
- Reduces maintenance burden

---

## Implementation Plan

### Files to Modify
1. `src/tunacode/utils/user_configuration.py`
   - Remove `"enable_tutorial": True` from `_ensure_onboarding_defaults()`
   - Remove tutorial setting from `initialize_first_time_user()`

2. `src/tunacode/configuration/key_descriptions.py`
   - Remove all tutorial-related setting descriptions (lines 209-231)

3. `src/tunacode/exceptions.py`
   - Remove `OnboardingError` class (lines 160-170)

### Preservation Note
Keep `first_installation_date` setting if desired for analytics, as it has utility beyond tutorial context. Currently it's documented alongside tutorial but could be repurposed.

---

## Validation Checklist

### Before Deletion
- [ ] Create backup branch
- [ ] Run full test suite to establish baseline
- [ ] Document current settings for reference

### After Deletion
- [ ] Run `ruff check --fix .` to find broken references
- [ ] Run `hatch run test` to ensure no regressions
- [ ] Test CLI startup and basic functionality
- [ ] Verify configuration loading still works

### Final Verification
- [ ] No tutorial-related imports remain
- [ ] No tutorial settings in configuration
- [ ] No tutorial exceptions defined
- [ ] Application functions normally

---

## Related Context

### Previous Deletion Work
This cleanup follows the deletion of the entire tutorial directory as documented in:
- `memory-bank/research/2025-11-30_17-15-00_rich-prompt_toolkit-to-textual-deletion-map.md`

### Architecture Migration
Part of broader migration from Rich/prompt_toolkit to Textual TUI:
- Tutorial system was prompt_toolkit-dependent
- Decision made to rebuild on Textual later if needed
- Current focus: Clean removal of old system remnants

---

## References

### Files Analyzed
- `src/tunacode/utils/user_configuration.py` - Tutorial setting initialization
- `src/tunacode/configuration/key_descriptions.py` - Tutorial setting docs
- `src/tunacode/exceptions.py` - Unused OnboardingError class
- `memory-bank/research/2025-11-30_17-15-00_rich-prompt_toolkit-to-textual-deletion-map.md` - Previous deletion map

### Related Research
- Rich/prompt_toolkit to Textual migration documentation
- CLI architecture mapping research
- Codebase dependency analysis

---

**Conclusion:** The tutorial system has been successfully deleted with only non-functional configuration remnants remaining. These can be safely removed to complete the cleanup and eliminate confusion.