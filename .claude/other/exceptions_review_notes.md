# exceptions.py Review Notes

**File:** `src/tunacode/exceptions.py`
**Date:** 2026-01-04
**Reviewer:** Claude Code

---

## DRY Violations (High Priority)

The pattern of building enhanced error messages is **repeated 5 times** with nearly identical code:

| Class | Lines | Enhancement Pattern |
|-------|-------|---------------------|
| `ConfigurationError` | 20-31 | `suggested_fix`, `help_url` |
| `ValidationError` | 44-61 | `suggested_fix`, `valid_examples` |
| `ToolExecutionError` | 68-89 | `suggested_fix`, `recovery_commands` |
| `AgentError` | 95-114 | `suggested_fix`, `troubleshooting_steps` |
| `SetupValidationError` | 176-192 | Inherits from `ValidationError` but duplicates message building |

Each class manually:
1. Stores the enhancement args as instance attributes
2. Builds `full_message` by string concatenation
3. Passes `full_message` to `super().__init__()`

**Proposed Solution:**
Extract a helper function for building enhanced messages:
```python
def _build_enhanced_message(
    base: str,
    suggested_fix: str | None = None,
    extras: list[tuple[str, list[str]]] | None = None,
) -> str:
    """Build enhanced error message with optional fix and extra sections."""
```

---

## Dead Code (Low Priority)

No obvious dead code detected. The exception hierarchy appears fully utilized:
- Base: `TunaCodeError`
- Category roots: `ConfigurationError`, `ServiceError`, `FileOperationError`, `StateError`
- Specific errors inherit appropriately

**Verification Needed:**
Quick grep to confirm `GlobalRequestTimeoutError` (lines 208-218) is actively used/imported somewhere.

---

## Tight Coupling (Low Priority)

**Current State:**
- Imports from `tunacode.types` are appropriate for type annotations only
- Inheritance hierarchy is logical and clean

**Potential Improvements:**
- Consider a base exception class that accepts enhancement kwargs to standardize signatures
- Could use `dataclass` for exception classes with many attributes

---

## Minor Observations

1. **Emoji usage inconsistency** - Some messages use emojis (`💡`, `🔧`, `🔍`) while others don't
2. **No docstrings** - Exception classes lack docstrings (though base class has one)
3. **Type alias usage** - `ErrorMessage`, `FilePath`, `OriginalError`, `ToolName` from `tunacode.types` are used - verify these are properly exported

---

## Suggested Refactoring Order

1. Extract `_build_enhanced_message()` helper
2. Refactor one exception class to use the helper
3. Update remaining classes
4. Verify all tests pass
5. Add docstrings to each exception class
6. Standardize emoji usage (add or remove)
