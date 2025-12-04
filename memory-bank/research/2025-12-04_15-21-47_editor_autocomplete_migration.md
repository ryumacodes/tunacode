# Research - Editor to Input Migration & FileAutoComplete Fix

**Date:** 2025-12-04
**Owner:** claude
**Phase:** Research

## Goal

Research the migration from TextArea-based Editor to Input-based Editor, diagnose why FileAutoComplete is not working, and identify all codebase inconsistencies for uniformity.

## Findings

### Critical Issue: FileAutoComplete Not Working

**Root Cause:** The `FileAutoComplete` widget incorrectly passes a callback to the constructor instead of properly overriding AutoComplete methods.

#### Current Implementation (BROKEN):
```python
# file_autocomplete.py:14-16
def __init__(self, target: Input) -> None:
    self._filter = FileFilter()
    super().__init__(target, candidates=self._get_candidates)  # WRONG
```

#### Why It Fails:
1. AutoComplete base class has `get_search_string()` that returns ALL text up to cursor
2. When user types `"check @src"`, base class returns `"check @src"` as search string
3. But `_get_candidates()` extracts just `"src"` - MISMATCH
4. Fuzzy matching fails because search string doesn't align with filtering

#### Required Fix - Override Methods Properly:
```python
class FileAutoComplete(AutoComplete):
    def __init__(self, target: Input) -> None:
        self._filter = FileFilter()
        super().__init__(target)  # Don't pass candidates callback

    def get_search_string(self, state: TargetState) -> str:
        """Extract ONLY the part after @ symbol."""
        text = state.text
        cursor = state.cursor_position
        at_pos = text.rfind("@", 0, cursor)
        if at_pos == -1:
            return ""
        prefix_region = text[at_pos + 1 : cursor]
        if " " in prefix_region:
            return ""
        return prefix_region  # Return "src" not "check @src"

    def get_candidates(self, state: TargetState) -> list[DropdownItem]:
        """Return file candidates for current search."""
        search = self.get_search_string(state)
        at_pos = state.text.rfind("@", 0, state.cursor_position)
        if at_pos == -1:
            return []
        candidates = self._filter.complete(search)
        return [DropdownItem(main=f"@{path}") for path in candidates]

    def apply_completion(self, value: str, state: TargetState) -> None:
        """Replace @path region with completed value."""
        text = state.text
        cursor = state.cursor_position
        at_pos = text.rfind("@", 0, cursor)
        if at_pos != -1:
            new_text = text[:at_pos] + value + text[cursor:]
            self.target.value = new_text
            self.target.cursor_position = at_pos + len(value)
```

### Relevant Files & Why They Matter

| File | Relevance |
|------|-----------|
| `src/tunacode/ui/widgets/file_autocomplete.py` | CRITICAL - Root cause of autocomplete failure |
| `src/tunacode/ui/widgets/editor.py` | CLEAN - Properly uses Input, no changes needed |
| `src/tunacode/ui/app.py:86` | Composition correct, yields FileAutoComplete after Editor |
| `src/tunacode/utils/ui/file_filter.py` | FileFilter logic is correct |
| `src/tunacode/utils/ui/completion.py` | DEAD CODE - unused, should be deleted |
| `src/tunacode/utils/ui/__init__.py:3,10-11` | DEAD EXPORTS - remove `replace_token`, `textual_complete_paths` |

### Dead Code to Remove

**File:** `src/tunacode/utils/ui/completion.py`
- `textual_complete_paths()` - NOT USED anywhere
- `replace_token()` - NOT USED anywhere

**File:** `src/tunacode/utils/ui/__init__.py`
- Remove exports: `replace_token`, `textual_complete_paths`

### Documentation with Outdated References

These docs reference "TextArea" but Editor now uses "Input":

| File | Lines | Status |
|------|-------|--------|
| `memory-bank/research/2025-11-29_textual-tui-architecture-and-style-guide.md` | 53, 65 | Outdated |
| `memory-bank/research/2025-11-29_textual-repl-tui-modernization.md` | 46, 66 | Outdated |
| `memory-bank/research/2025-11-29_textual-tui-architecture-diagrams.md` | 25 | Outdated |
| `memory-bank/research/2025-11-30_13-45-00_tui-architecture-map.md` | 27, 99, 309 | Historical (keep) |

### Codebase Uniformity Verification

**Active Implementation Files - ALL UNIFORM:**
- Widget class: `Editor` (extends `Input`)
- CSS selector: `Editor { ... }`
- Messages: `EditorSubmitRequested`, `EditorCompletionsAvailable`
- App references: `self.editor: Editor`

**No `TextArea` imports found in `/src/tunacode`**

## Key Patterns / Solutions Found

### textual-autocomplete 4.x Integration Pattern

**Correct Composition:**
```python
def compose(self) -> ComposeResult:
    self.editor = Editor()  # Extends Input
    yield self.editor
    yield FileAutoComplete(self.editor)  # After target
```

**Method Override Requirements:**
1. `get_search_string(state)` - Return the portion to match against candidates
2. `get_candidates(state)` - Return list of DropdownItem
3. `apply_completion(value, state)` - Handle inserting the completion

**CSS Requirements:**
- AutoComplete provides DEFAULT_CSS with `overlay: screen`
- Theme variables `$surface`, `$foreground` must be defined
- No custom CSS required unless overriding defaults

## Knowledge Gaps

1. **Theme verification needed:** Check `constants.py` for `$surface`, `$foreground` theme variables
2. **Tab key handling:** Verify AutoComplete's Tab handling doesn't conflict with Editor
3. **apply_completion testing:** Need to verify the replacement logic works for mid-string completions

## Implementation Plan Summary

### Phase 1: Fix FileAutoComplete (CRITICAL)
1. Rewrite `file_autocomplete.py` with proper method overrides
2. Override `get_search_string()` to return part after `@`
3. Override `get_candidates()` without passing callback to constructor
4. Override `apply_completion()` to handle @path replacement

### Phase 2: Remove Dead Code
1. Delete `src/tunacode/utils/ui/completion.py`
2. Update `src/tunacode/utils/ui/__init__.py` to remove dead exports

### Phase 3: Update Documentation (Optional)
1. Update outdated research docs to reflect Input-based Editor
2. Keep historical migration docs as-is

## References

- textual-autocomplete source: `.venv/lib/python3.13/site-packages/textual_autocomplete/_autocomplete.py`
- Previous research: `memory-bank/research/2025-12-04_14-50-38_at_file_picker_autocomplete.md`
- Editor widget: `src/tunacode/ui/widgets/editor.py`
- App composition: `src/tunacode/ui/app.py:75-87`
