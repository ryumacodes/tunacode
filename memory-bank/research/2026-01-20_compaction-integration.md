# Research - Compaction System Integration
**Date:** 2026-01-20
**Owner:** agent
**Phase:** Research

## Goal
Document how the compaction system integrates with tunacode's agent loop, message history, configuration, and UI presentation before any modifications.

## Findings

### Core Implementation
- **File:** `/home/fabian/tunacode/src/tunacode/core/compaction.py`
  - Implements backward-scanning algorithm to replace old tool outputs with placeholders
  - Main function: `prune_old_tool_outputs(messages, model_name)` returns `(messages, tokens_reclaimed)`
  - Mutates message list in-place by replacing tool return content with `PRUNE_PLACEHOLDER = "[Old tool result content cleared]"`

### Integration Point: Agent Loop
- **File:** `/home/fabian/tunacode/src/tunacode/core/agents/main.py`
  - Import: Line 22 - `from tunacode.core.compaction import prune_old_tool_outputs`
  - Call site: Lines 339-344 in `RequestOrchestrator._run_impl()`
  ```python
  # Prune old tool outputs directly in session (persisted)
  session_messages = self.state_manager.session.messages
  tool_call_args_by_id = self.state_manager.session.tool_call_args_by_id
  _, tokens_reclaimed = prune_old_tool_outputs(session_messages, self.model)
  pruned_message = f"History pruned (reclaimed_tokens={tokens_reclaimed})"
  logger.lifecycle(pruned_message, request_id=request_id)
  ```
  - Timing: Called at the START of each request, BEFORE the agent iteration loop begins
  - Operates on `state_manager.session.messages` (the persisted message history)
  - Happens after request context initialization, before message history snapshot

### Message History Interaction
- **Read:** Scans `session_messages` backward to collect tool return parts
- **Write:** Mutates tool return parts in-place, replacing `.content` with placeholder
- **No structural changes:** Message count and structure remain identical
- **State updates:** Token count reclaimed is logged but does NOT automatically update `session.total_tokens`
  - Session token count is updated via `session.update_token_count()` which is called AFTER message persistence

### Configuration: Two Modes
Configuration is controlled by `src/tunacode/core/limits.py`:

#### Standard Mode (Cloud Models)
- `PRUNE_PROTECT_TOKENS = 40_000` - Protect last 40k tokens from pruning
- `PRUNE_MINIMUM_THRESHOLD = 20_000` - Only prune if savings exceed 20k tokens

#### Local Mode (Small Context Windows)
- `LOCAL_PRUNE_PROTECT_TOKENS = 2_000` - Protect last 2k tokens (aggressive)
- `LOCAL_PRUNE_MINIMUM_THRESHOLD = 500` - Lower threshold for small models

Mode selection:
```python
def is_local_mode() -> bool:
    """Check if local_mode is enabled."""
    return _load_settings().get("local_mode", False)
```

User sets `"local_mode": true` in their configuration file to enable aggressive compaction.

### Additional Constraints
- **Minimum user turns:** `PRUNE_MIN_USER_TURNS = 2` - Requires at least 2 user turns before pruning
- **Backward scan:** Protects recent content first, then prunes older content
- **Token estimation:** Uses `estimate_tokens(content, model_name)` heuristic from `tunacode.utils.messaging`

### UI Presentation
Compaction status is NOT directly visible to users in normal operation:

1. **Lifecycle logging only:** Line 344 logs `"History pruned (reclaimed_tokens={tokens_reclaimed})"`
2. **Debug mode required:** Lifecycle logs are emitted via `logger.lifecycle()` which checks `debug_mode`:
   ```python
   def lifecycle(self, message: str, **kwargs: Any) -> None:
       """Emit lifecycle debug logs only when debug_mode is enabled."""
       if not self.debug_mode:
           return
   ```
   - File: `/home/fabian/tunacode/src/tunacode/core/logging/manager.py` Lines 121-126
3. **TUI Handler:** When debug_mode=True, lifecycle logs are routed to TUI and log file
4. **Log file:** Always written to file regardless of debug mode

Result: Users only see compaction activity if they enable debug mode. No visual indicator in normal operation.

### File Structure
```
src/tunacode/core/
├── compaction.py           # Core pruning logic
├── limits.py              # Mode detection and thresholds
├── agents/
│   └── main.py            # Integration point (RequestOrchestrator)
└── logging/
    └── manager.py         # Lifecycle logging (debug_mode gated)

tests/unit/core/
└── test_compaction.py     # Comprehensive unit tests
```

### Dependencies
Compaction imports from:
- `tunacode.core.limits.is_local_mode()` - Mode detection
- `tunacode.utils.messaging.estimate_tokens()` - Token estimation

Compaction is imported by:
- `tunacode.core.agents.main` - Agent loop integration

### Key Patterns / Solutions Found

1. **In-place mutation:** Compaction mutates existing message objects rather than creating new ones
   - Preserves object identity and references
   - No need to reassign or swap message lists

2. **Binary mode switch:** Not a sliding scale, just local_mode=True/False
   - Users with big models can set explicit thresholds without enabling local_mode
   - Precedence: explicit setting > local_mode default > standard default

3. **Protection-first algorithm:** Backward scan accumulates recent tokens to protect before identifying what to prune
   - Ensures recent context is always preserved
   - Older content is pruned only if savings justify the operation

4. **Lifecycle pattern:** Uses `logger.lifecycle()` for internal state changes
   - Only visible when debugging
   - Keeps normal UI clean while providing detailed logs when needed

5. **Test coverage:** Comprehensive tests in `/home/fabian/tunacode/tests/unit/core/test_compaction.py`
   - Part type detection
   - Token estimation
   - Protection windows
   - Threshold enforcement
   - Edge cases (empty messages, insufficient history, immutable parts)

## Knowledge Gaps

1. **Token count synchronization:** When/how does `session.total_tokens` get updated after compaction?
   - Compaction returns `tokens_reclaimed` but doesn't call `session.adjust_token_count()`
   - Is this intentional or a potential bug?

2. **User awareness:** Should users be notified when compaction occurs?
   - Current: Silent unless debug_mode=True
   - Could this cause confusion when old tool outputs suddenly show placeholder?

3. **Compaction frequency:** How often does compaction actually trigger?
   - Need to analyze real-world session logs to see effectiveness
   - Are thresholds well-calibrated?

4. **Anthropic's built-in compaction:** There's a file in venv: `.venv/lib/python3.12/site-packages/anthropic/lib/tools/_beta_compaction_control.py`
   - Is this related? Are we duplicating functionality?
   - Should we be using Anthropic's compaction instead?

## References

### Primary Files
- `/home/fabian/tunacode/src/tunacode/core/compaction.py` - Core implementation (238 lines)
- `/home/fabian/tunacode/src/tunacode/core/agents/main.py` - Integration point (583 lines)
- `/home/fabian/tunacode/src/tunacode/core/limits.py` - Configuration (97 lines)
- `/home/fabian/tunacode/tests/unit/core/test_compaction.py` - Tests

### Related Files
- `/home/fabian/tunacode/src/tunacode/core/logging/manager.py` - Lifecycle logging
- `/home/fabian/tunacode/src/tunacode/core/state.py` - Session state management
- `/home/fabian/tunacode/src/tunacode/utils/messaging.py` - Token estimation

### Search Commands
```bash
# Find all compaction references
grep -ri "compact" src/ tests/ --include="*.py"

# Find all prune_old_tool_outputs calls
grep -rn "prune_old_tool_outputs" src/

# Find lifecycle logging
grep -rn "lifecycle" src/tunacode/core/agents/
```
