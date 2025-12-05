# Research – Token Counting & Context Management Verification

**Date:** 2025-12-04
**Owner:** Claude Agent
**Phase:** Research
**Related:** memory-bank/research/2025-12-04_token-management-context-compaction.md

## Goal

Verify that the token counting and context compaction implementation is working correctly after recent updates. Identify any gaps, inconsistencies, or issues that need to be addressed.

---

## Findings

### Test Suite Status: All 27 Compaction Tests Pass

```
tests/test_compaction.py: 27 passed in 0.54s
```

The compaction module is well-tested and functioning correctly at the unit level.

---

### Token Counting Architecture

The system uses **two separate token tracking mechanisms**:

| Metric | Location | Purpose | Update Frequency |
|--------|----------|---------|------------------|
| `total_tokens` | `state.py:66` | Estimated context window usage (tiktoken) | On model response |
| `session_total_usage` | `state.py:76-82` | Cumulative API billing tokens | On each API call |

**Key Files:**
- `src/tunacode/utils/messaging/token_counter.py:58` → `estimate_tokens()` function using tiktoken
- `src/tunacode/core/state.py:91-102` → `update_token_count()` and `adjust_token_count()` methods
- `src/tunacode/core/agents/agent_components/node_processor.py:22-37` → `_update_token_usage()` for API tokens
- `src/tunacode/core/compaction.py` → Tool output pruning with placeholder replacement

---

### Integration Points Verified

#### 1. Compaction Integration (Working)
**Location:** `src/tunacode/core/agents/main.py:367-372`

```python
session_messages = self.state_manager.session.messages
_, tokens_reclaimed = prune_old_tool_outputs(session_messages, self.model)
if tokens_reclaimed > 0:
    logger.info("Pruned %d tokens from old tool outputs", tokens_reclaimed)
    self.state_manager.session.adjust_token_count(-tokens_reclaimed)
```

- Pruning runs at the start of each request
- Successfully reclaims tokens from old tool outputs
- Logging captures reclaimed token count

#### 2. Token Count Update After Model Response (Working)
**Location:** `src/tunacode/core/agents/agent_components/node_processor.py:77-79`

```python
_update_token_usage(node.model_response, state_manager)
# Update context window token count
state_manager.session.update_token_count()
```

- API usage extracted from model response
- Context tokens recalculated from message history

#### 3. UI Resource Bar Display (Working with Fallback)
**Location:** `src/tunacode/ui/app.py:273-283`

```python
context_tokens = session.total_tokens
self.resource_bar.update_stats(
    tokens=context_tokens,
    max_tokens=session.max_tokens or 200000,
)
```

- Displays current token usage
- Uses hardcoded 200000 fallback for max_tokens

---

## Critical Issues Found

### Issue 1: `max_tokens` Never Initialized from Config (HIGH)

**Location:** `src/tunacode/core/state.py:67`

```python
max_tokens: int = 0  # Always 0!
```

The `context_window_size` from user config (defaults to 200,000) is never assigned to `max_tokens`.

**Impact:**
- Context overflow detection impossible (`max_tokens == 0`)
- UI uses hardcoded fallback instead of user config
- Future auto-compaction cannot trigger on percentage thresholds

**Fix Required in `StateManager._load_user_configuration()`:**
```python
context_window = self._session.user_config.get("settings", {}).get("context_window_size", 200000)
self._session.max_tokens = context_window
```

---

### Issue 2: Token Count Not Updated After User Messages (MEDIUM)

**Location:** `src/tunacode/core/agents/agent_components/agent_helpers.py:50`

```python
def create_user_message(content: str, state_manager: StateManager):
    # ...
    state_manager.session.messages.append(message)
    return message  # NO token update!
```

`update_token_count()` is only called after model responses, not after:
- Iteration limit messages (`main.py:132`)
- No-progress nudges (`main.py:155`)
- Clarification requests (`main.py:167`)
- Empty response interventions

**Impact:** Token count lags behind actual conversation size until next model response.

**Fix Required:**
```python
state_manager.session.messages.append(message)
state_manager.session.update_token_count()  # Add this
return message
```

---

### Issue 3: `adjust_token_count()` Is Redundant (LOW)

**Location:** `src/tunacode/core/agents/main.py:372`

The pruning adjustment at request start:
```python
self.state_manager.session.adjust_token_count(-tokens_reclaimed)
```

Is immediately overwritten by the full recalculation in the first iteration:
```python
state_manager.session.update_token_count()  # Recalculates from scratch
```

**Impact:** No functional issue - the adjustment is redundant but harmless. The full recalculation correctly counts the pruned (placeholder) content.

**Optional Fix:** Remove `adjust_token_count()` call or keep for logging purposes only.

---

### Issue 4: `files_in_context` No Longer Counted (INFO)

**Location:** `src/tunacode/core/state.py:57, 91-98`

The `files_in_context` set exists in `SessionState` but is not included in token estimation (appears to have been removed in refactoring).

**Impact:** Unknown - need to verify if this field is still used. If files are tracked separately, token estimation may undercount.

**Action:** Clarify intent - is `files_in_context` obsolete or should it contribute to token counts?

---

### Issue 5: Compaction Only Runs at Request Start (INFO)

**Location:** `src/tunacode/core/agents/main.py:367`

Pruning runs once per request, not mid-conversation. OpenCode's implementation triggers auto-compaction at 92% context window usage.

**Impact:** Long conversations with many tool outputs during a single request could exceed context limits before the next request triggers pruning.

**Future Enhancement:** Add context overflow check in agent loop.

---

## Key Patterns / Solutions Found

### Pattern 1: Backward-Scanning Pruning Algorithm
```
constants: PRUNE_PROTECT = 40k, PRUNE_MINIMUM = 20k, MIN_TURNS = 2
algorithm: Scan backwards → Protect recent 40k → Prune if >20k savings
```

### Pattern 2: Placeholder Replacement
```
Original content → "[Old tool result content cleared]"
```
Preserves conversation structure while freeing token budget.

### Pattern 3: Dual Token Tracking
```
Estimated (tiktoken): For context window management
API-reported: For billing/usage tracking
```

---

## Test Coverage Status

**Covered:**
- Pruning algorithm (27 tests)
- Threshold enforcement
- Protection window
- Mixed message type handling
- Immutable part handling

**Missing:**
- Token count updates after user message addition
- Interaction between pruning and full recalculation
- `max_tokens` initialization
- UI display with actual config values

---

## Recommendations

### Priority 1: Initialize `max_tokens` from Config
Add to `StateManager._load_user_configuration()`:
```python
settings = self._session.user_config.get("settings", {})
self._session.max_tokens = settings.get("context_window_size", 200000)
```

### Priority 2: Update Tokens After User Messages
Modify `create_user_message()` in `agent_helpers.py`:
```python
state_manager.session.messages.append(message)
state_manager.session.update_token_count()
return message
```

### Priority 3: Remove UI Fallback After Fix
Once `max_tokens` is initialized, update `app.py:283`:
```python
max_tokens=session.max_tokens,  # Remove `or 200000`
```

### Priority 4: Clarify `files_in_context` Status
Either:
- Remove the field if obsolete
- Or re-add to token estimation with documentation

---

## References

### TunaCode Files
- `src/tunacode/core/state.py:66-102` → Token tracking fields and methods
- `src/tunacode/core/compaction.py` → Pruning implementation
- `src/tunacode/core/agents/main.py:367-372` → Compaction integration
- `src/tunacode/core/agents/agent_components/node_processor.py:22-79` → API usage tracking
- `src/tunacode/utils/messaging/token_counter.py` → tiktoken estimation
- `src/tunacode/ui/widgets/resource_bar.py` → Token display widget
- `src/tunacode/ui/app.py:273-283` → UI integration

### Test Files
- `tests/test_compaction.py` → 27 tests, all passing

### Previous Research
- `memory-bank/research/2025-12-04_token-management-context-compaction.md` → Initial design research
