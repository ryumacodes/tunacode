# Plan: Fix Mypy Type Errors

## Current Errors

```
src/tunacode/constants.py:326: Argument 1 to "Theme" has incompatible type "**dict[str, object]"; expected "str"
src/tunacode/constants.py:326: Argument 1 to "Theme" has incompatible type "**dict[str, object]"; expected "bool"
src/tunacode/constants.py:326: Argument 1 to "Theme" has incompatible type "**dict[str, object]"; expected "float"
src/tunacode/constants.py:326: Argument 1 to "Theme" has incompatible type "**dict[str, object]"; expected "dict[str, str]"

src/tunacode/ui/thinking_state.py:72: "Widget" has no attribute "update"
```

## Issue 1: constants.py Theme kwargs

### Root Cause

`_wrap_builtin_theme()` uses `**kwargs` unpacking with `dict[str, object]`, which is too loose for mypy to verify against Textual's `Theme` signature.

### Fix Options

**Option A: Build Theme explicitly (preferred)**

```python
return ThemeCls(
    name=theme.name,
    dark=theme.dark,
    primary=theme.primary,
    secondary=theme.secondary,
    # ... all other fields explicitly
    variables=merged_vars,
)
```

### Recommended: Option A

- Most explicit and type-safe
- No runtime overhead
- Clear what fields are being passed

## Issue 2: thinking_state.py Widget.update

### Root Cause

Rich's `Widget` class may not have `update` method in type stubs, or it's a method that exists at runtime but isn't in the type definitions.

### Fix Options

**Option A: Check if method exists, use alternative**

```python
# Check what method Rich Widget actually has for updating content
```

**Option B: Suppress with type: ignore if runtime works**

```python
widget.update(...)  # type: ignore[attr-defined]
```

**Option C: Cast to correct type**

```python
from typing import cast
cast(SomeOtherType, widget).update(...)
```

### Recommended: Investigate Option A first

- Check Rich documentation for correct method
- May be `render` or different update API

## Files to Modify

1. `/home/tuna/tunacode/src/tunacode/constants.py` - Lines 295-326
2. `/home/tuna/tunacode/src/tunacode/ui/thinking_state.py` - Line 72
