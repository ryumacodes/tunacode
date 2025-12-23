# TUI Confirmation Preview Hang

**Date:** 2025-12-18
**Severity:** High
**Status:** Resolved in v0.1.12

## Symptoms

- TUI becomes completely unresponsive (frozen)
- Cannot close the app cleanly
- Occurs when `write_file` or `update_file` tools are called with large content
- Most commonly triggered by minified JSON, base64 data, or any single-line payload

## Root Cause

The freeze was **not** in the actual file write operation - it was in the **confirmation preview UI**.

### The Bug Chain

1. `ConfirmationRequestFactory` builds `request.diff_content` for `write_file` by embedding file content into a "creation diff"
2. Location: `src/tunacode/tools/authorization/requests.py`
3. The logic only limited **number of lines**, not **total size**
4. A huge single-line payload (minified JSON, long base64, etc.) produced a multi-MB diff string
5. The TUI tried to render that entire diff with Rich Syntax in the inline confirmation panel (`src/tunacode/ui/app.py`)
6. Rich's syntax highlighting on MB-sized content stalled the UI/event loop
7. App appeared frozen and wouldn't close cleanly

### Why It Was Deceptive

- The hang happened **before** any file I/O
- Looked like a write operation hang, but was actually a rendering hang
- Only affected large single-line content (not large multi-line files that would hit the line limit)

## The Fix

Bounded the preview in `src/tunacode/tools/authorization/requests.py`:

1. **Max total characters** - caps the entire diff string length
2. **Max lines** - existing limit retained
3. **Max line width** - truncates individual lines that exceed threshold
4. **Truncation marker** - adds `... [truncated for safety]` when content is cut

```python
# Constants added
MAX_DIFF_CHARS = 50000
MAX_DIFF_LINES = 100
MAX_LINE_WIDTH = 500
```

## Files Changed

- `src/tunacode/tools/authorization/requests.py` - Added truncation logic
- `src/tunacode/tools/authorization/handler.py` - Fixed import cycle (moved StateManager import)
- `tests/test_confirmation_preview.py` - Regression tests

## Lessons Learned

1. **UI rendering can be the bottleneck** - Don't assume I/O is always the slow path
2. **Single-line content bypasses line limits** - Always consider both dimensions (lines AND characters)
3. **Rich syntax highlighting is expensive** - Large content + syntax highlighting = freeze
4. **Truncation markers help debugging** - Users can see when content was cut

## Regression Test

```python
def test_large_single_line_content_truncated():
    """Ensure huge single-line content doesn't freeze the UI."""
    huge_content = "x" * 100000  # 100KB single line
    diff = build_creation_diff(huge_content)
    assert len(diff) < MAX_DIFF_CHARS + 1000  # Some buffer for markers
```

## Related

- Commit: `e820d7d`
- Delta log: `.claude/delta/confirmation-preview-hang-fix.md`
