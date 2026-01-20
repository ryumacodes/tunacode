# Research - Compaction System

**Date:** 2026-01-20
**Owner:** claude-agent
**Phase:** Research
**Git Commit:** 41ae26a

## Goal

Document the compaction system architecture, algorithms, and integration points in tunacode to provide a complete understanding of how context window management works.

## Findings

### Core Files

| File | Purpose |
|------|---------|
| `src/tunacode/core/compaction.py` | Main compaction logic, thresholds, pruning algorithm |
| `src/tunacode/core/limits.py` | Mode detection (`is_local_mode()`), limit resolution |
| `src/tunacode/utils/messaging/token_counter.py` | Token estimation (4 chars/token heuristic) |
| `src/tunacode/core/agents/main.py:342` | Integration point - triggers compaction |
| `src/tunacode/core/state.py` | Token tracking in `SessionState` |

### Algorithm Overview

The compaction system uses a **backward-scanning placeholder replacement** strategy:

```
Phase 1: Early Exit Checks
  - Empty messages? Return.
  - Less than 2 user turns? Return.

Phase 2: Backward Scanning
  - Iterate messages newest-to-oldest
  - Collect all tool-return parts with token counts

Phase 3: Protection Boundary
  - Accumulate tokens from newest parts
  - When accumulated > protect_tokens, mark boundary
  - Everything at boundary and older = prune candidates

Phase 4: Apply Pruning
  - Check if total savings > minimum_threshold
  - Replace each candidate's content with placeholder
```

### Thresholds

| Mode | protect_tokens | minimum_threshold | Use Case |
|------|----------------|-------------------|----------|
| Standard | 40,000 | 20,000 | Cloud APIs (200k context) |
| Local | 2,000 | 500 | Local models (10k context) |

Local mode is **20x more aggressive** to accommodate smaller context windows.

### What Gets Pruned

**Pruned (replaced with placeholder):**
- Tool return parts (`part_kind == "tool-return"`)
- Only those beyond the protection window
- Only if batch exceeds minimum threshold

**Never touched:**
- User messages
- System prompts
- Tool call requests (only returns are pruned)
- Recent tool outputs within protection window
- Messages without `parts` attribute

**Placeholder text:**
```
[Old tool result content cleared]
```

### Token Counting

```python
CHARS_PER_TOKEN: int = 4

def estimate_tokens(text: str, model_name: str | None = None) -> int:
    if not text:
        return 0
    return len(text) // CHARS_PER_TOKEN
```

Simple heuristic - does not use actual tokenizers. Model name parameter is accepted but not used.

### Integration Flow

```
1. User sends request
   |
2. RequestOrchestrator._run_impl() called (main.py:310)
   |
3. prune_old_tool_outputs(session.messages, model) (main.py:342)
   |
4. Compaction scans backwards, identifies boundary
   |
5. Old tool outputs mutated in-place with placeholder
   |
6. Pruned messages copied to message_history for agent run
   |
7. After agent completes, messages persisted
   |
8. session.update_token_count() recalculates totals
```

### Notable Design Decisions

1. **In-Place Mutation**: Messages are mutated directly, not copied
2. **Idempotent**: Already-pruned parts (containing placeholder) are skipped
3. **Graceful Degradation**: Immutable parts silently return 0 reclaimed
4. **Proactive, Not Reactive**: Compaction runs at request start, not on overflow
5. **No Summarization**: Pure placeholder replacement, no semantic preservation

### Configuration

Mode is controlled by `local_mode` setting in user config:

```json
{
  "local_mode": true,
  "context_window_size": 10000
}
```

Detection via `is_local_mode()` in `limits.py` (cached with `@lru_cache`).

### UI Presentation

Compaction activity is logged via:
```python
logger.lifecycle(f"History pruned (reclaimed_tokens={tokens_reclaimed})", request_id=request_id)
```

Only visible when `debug_mode` is enabled.

## Key Patterns / Solutions Found

- **Backward scanning**: Process newest-first to establish protection boundary
- **Binary mode switch**: Two completely different threshold sets, not sliding scale
- **Part-level granularity**: Prunes individual parts, not entire messages
- **Token estimation heuristic**: 4 chars/token is fast but approximate

## Knowledge Gaps

1. **Calibration**: Are the threshold values (40k/20k, 2k/500) optimal?
2. **Summarization**: Would LLM-based summarization preserve more useful context?
3. **Model-specific tokenization**: Current heuristic ignores actual tokenizer differences
4. **Overflow handling**: No reactive mechanism when context actually overflows

## References

### Source Files
- [compaction.py](https://github.com/alchemiststudiosDOTai/tunacode/blob/41ae26a/src/tunacode/core/compaction.py)
- [limits.py](https://github.com/alchemiststudiosDOTai/tunacode/blob/41ae26a/src/tunacode/core/limits.py)
- [token_counter.py](https://github.com/alchemiststudiosDOTai/tunacode/blob/41ae26a/src/tunacode/utils/messaging/token_counter.py)
- [main.py (integration)](https://github.com/alchemiststudiosDOTai/tunacode/blob/41ae26a/src/tunacode/core/agents/main.py#L342)
- [state.py](https://github.com/alchemiststudiosDOTai/tunacode/blob/41ae26a/src/tunacode/core/state.py)

### Test Files
- `tests/unit/core/test_compaction.py`
- `tests/unit/core/test_limits.py`
- `tests/unit/core/test_token_counter.py`

### Documentation
- `docs/codebase-map/modules/core-compaction.md`
- `docs/codebase-map/modules/core-limits.md`
- `docs/configuration/tunacode.local.json.example`
