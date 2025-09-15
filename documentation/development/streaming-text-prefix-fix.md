# Streaming Text Prefix Fix

**Date:** 2025-09-15
**Status:** Implemented
**Files Modified:** `src/tunacode/core/agents/main.py`
**Related Issue:** First-character loss in streaming display

## Problem Overview

TunaCode's streaming text display was consistently dropping the first few characters of LLM responses. Messages like "Good morning!" would appear as "morning!" and "TUNACODE DONE:" would show as "UNACODE DONE:".

### Root Cause Analysis

The issue stemmed from a mismatch between the provider's event structure and our streaming implementation:

1. **Provider Event Sequence:**
   - `PartStartEvent` contains initial text in `event.part.content` (e.g., "Good", "This", "Based")
   - `FinalResultEvent` may also arrive with complete text
   - `TextPartDelta` events then continue mid-string (e.g., " morn", " file", "'m", " on")

2. **Original Implementation Problem:**
   - Only forwarded `TextPartDelta.content_delta` content
   - Ignored text carried by `PartStartEvent` and `FinalResultEvent`
   - UI never received the initial substring and started from the middle

3. **Character Loss Mechanism:**
   - First visible characters lived in `PartStartEvent` or `FinalResultEvent`
   - These weren't forwarded to the streaming callback
   - First `TextPartDelta` started several characters in
   - Result: consistent first-character truncation

## Solution Implementation

### Core Fix Strategy

The solution implements a one-time prefix seeding mechanism that:

1. **Captures Pre-Delta Text** on stream initialization
2. **Aligns and Seeds** the missing prefix when the first delta arrives
3. **Prevents Duplication** through careful text alignment

### Implementation Details

#### 1. Pre-Delta Text Capture

```python
# Capture from PartStartEvent.part.content
if not first_delta_seen and type(event).__name__ == "PartStartEvent":
    try:
        p = getattr(event, "part", None)
        pcontent = getattr(p, "content", None) if p is not None else None
        if isinstance(pcontent, str) and pcontent:
            pre_first_delta_text = pcontent
    except Exception:
        pass

# Capture from FinalResultEvent
if not first_delta_seen and type(event).__name__ == "FinalResultEvent":
    text = _extract_text(getattr(event, "result", None))
    # Try multiple locations: response, final, message, model_response
    if not text:
        for attr in ("response", "final", "message", "model_response"):
            text = _extract_text(getattr(event, attr, None))
            if text:
                break
    if text:
        pre_first_delta_text = text
```

#### 2. Prefix Seeding Logic

When the first non-empty `TextPartDelta` arrives:

```python
if pre_first_delta_text and not seed_attempted and not seeded_prefix_sent:
    seed_attempted = True
    idx = pre_first_delta_text.find(delta_text)

    if idx > 0:
        # Delta found inside pre-text: emit prefix before delta
        prefix = pre_first_delta_text[:idx]
        await streaming_callback(prefix)
        seeded_prefix_sent = True

    elif idx == -1:
        # Delta not found: emit pre-text directly
        if pre_first_delta_text.strip():
            await streaming_callback(pre_first_delta_text)
            seeded_prefix_sent = True

    # idx == 0: delta starts at beginning, no seeding needed
```

#### 3. Text Extraction Helper

```python
def _extract_text(obj) -> Optional[str]:
    """Extract text from various response object formats."""
    if isinstance(obj, str):
        return obj
    if hasattr(obj, 'content') and isinstance(obj.content, str):
        return obj.content
    if hasattr(obj, 'text') and isinstance(obj.text, str):
        return obj.text
    # ... additional field checks
    return None
```

## Fix Characteristics

### Safety Features

- **One-Time Operation:** Seeding only occurs once per stream
- **Alignment-Based:** Uses string matching to prevent duplication
- **Exception-Safe:** All operations wrapped in try-catch blocks
- **Minimal Impact:** Only affects the first frame of streaming

### Guard Mechanisms

1. **`first_delta_seen`**: Ensures we only capture during stream initialization
2. **`seed_attempted`**: Prevents multiple seeding attempts
3. **`seeded_prefix_sent`**: Tracks successful prefix emission
4. **Text Alignment**: Prevents duplicate content through careful string matching

### Diagnostic Features

Debug logging is available for troubleshooting:

```python
state_manager.session._debug_events.append(
    f"[src] pre_part_captured ts_ns={ts_ns} len={len(pcontent)} preview={repr(pcontent[:20])}"
)
state_manager.session._debug_events.append(
    f"[src] seeded_prefix_direct len={len(pre_text)} preview={repr(pre_text)}"
)
```

## Before and After Behavior

### Before Fix

```text
PartStartEvent: p0='Good' (plen=4)
First TextPartDelta: " morn"
UI Display: "morning!" ❌
```

### After Fix

```text
PartStartEvent: p0='Good' (plen=4) → captured
First TextPartDelta: " morn" → alignment check
Seeded Prefix: "Good" → sent to UI
UI Display: "Good morning!" ✅
```

## Configuration and Maintenance

### Debug Mode

Diagnostic logging is gated behind internal debug flags and only runs when `thoughts` mode is enabled to avoid noise in normal operations.

### Future Considerations

1. **Config Flag Option:** Could wrap seeding behind a configuration flag
2. **Provider Adapter:** Could add normalization layer for different provider event shapes
3. **Log Cleanup:** Debug logs can be removed or tightened after verification

## Testing and Validation

### Validation Approach

1. **Stream Comparison:** Compare raw stream accumulation vs UI display
2. **Character Counting:** Verify no characters are lost or duplicated
3. **Edge Case Testing:** Test with various provider event sequences
4. **Performance Impact:** Ensure minimal overhead in normal streaming

### Test Cases

- Empty `PartStartEvent` content
- Missing `FinalResultEvent`
- Delta starting at position 0
- Very short pre-text content
- Long pre-text with multiple matches

## Related Files

- **Primary Implementation:** `src/tunacode/core/agents/main.py:283-378`
- **UI Display:** `src/tunacode/ui/panels.py` (StreamingAgentPanel)
- **Debug Research:** `memory-bank/research/2025-09-15_13-54-11_first-chunk_character_loss_investigation.md`

## Impact Assessment

- **User Experience:** Eliminates frustrating character loss in streaming responses
- **Performance:** Minimal overhead, one-time operation per stream
- **Reliability:** Robust error handling and fallback mechanisms
- **Maintainability:** Clear separation of concerns with diagnostic capabilities

This fix resolves the streaming text truncation issue while maintaining system performance and providing comprehensive debugging capabilities for future troubleshooting.
