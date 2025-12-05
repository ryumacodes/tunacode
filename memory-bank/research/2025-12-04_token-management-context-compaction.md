# Research – Token Management & Context Compaction

**Date:** 2025-12-04
**Owner:** Claude Agent
**Phase:** Research

## Goal

Investigate the current token management problem in tunacode (50k tokens after 5 turns due to unbounded message/tool output storage) and research OpenCode's solution for context compaction as inspiration for implementation.

---

## Problem Statement

Every message and tool output is currently saved in tunacode, leading to massive token consumption:

- ~50k tokens after just 5 turns
- No pruning, compaction, or summarization
- Full tool outputs stored (UI only truncates display to 200 chars)
- Cost hardcoded to $0.00 despite having pricing data

---

## Findings

### Current TunaCode Architecture

#### Message Storage (Unbounded Growth)

- **Location:** `src/tunacode/core/state.py:38`
- **Structure:** `messages: MessageHistory = field(default_factory=list)` (List[Any])
- **Problem:** Messages accumulate indefinitely without any cleanup

#### Message Accumulation Points

| File                                             | Line | What Gets Added                                         |
| ------------------------------------------------ | ---- | ------------------------------------------------------- |
| `core/agents/agent_components/node_processor.py` | 69   | `node.request` - Full API request                       |
| `core/agents/agent_components/node_processor.py` | 72   | `node.thought` - Model thinking                         |
| `core/agents/agent_components/node_processor.py` | 75   | `node.model_response` - Full response with tool results |

#### Token Tracking (Exists but Not Enforced)

- **Token Counter:** `src/tunacode/utils/messaging/token_counter.py:58` - Uses tiktoken
- **Estimation:** `src/tunacode/core/state.py:91-96` - `update_token_count()` method
- **API Usage:** `src/tunacode/core/agents/agent_components/node_processor.py:22-37` - Tracks prompt/completion tokens
- **Display:** `src/tunacode/ui/widgets/resource_bar.py` - Shows usage percentage

**Critical Gap:** Token counting exists but is **never used for context management**.

#### UI Display Truncation (Cosmetic Only)

- **Tool Panel:** `src/tunacode/ui/renderers/panels.py:287` - `_truncate_value()` at 200 chars
- **Args Display:** Truncated to 60 chars per argument
- **Problem:** This is **display-only** - full output still stored in session.messages

#### Missing Features

1. `/compact` command - Shows "not yet implemented" (`ui/commands/__init__.py:133`)
2. No message pruning logic anywhere
3. No context window enforcement against 200k limit
4. Cost calculation hardcoded to 0.0 (`node_processor.py:33`)

---

### OpenCode's Two-Layer Strategy

#### Layer 1: Old Tool Output Pruning ("Garbage Collection")

**Location:** `packages/opencode/src/session/compaction.ts`

**Constants:**

```typescript
export const PRUNE_MINIMUM = 20_000; // Only prune if savings > 20k tokens
export const PRUNE_PROTECT = 40_000; // Protect last 40k tokens of tool outputs
```

**Algorithm:**

1. Scan message history **backwards** (newest to oldest)
2. Accumulate token estimates for tool completion parts
3. Once accumulated tokens exceed `PRUNE_PROTECT` (40k), mark older parts for compaction
4. Only apply changes if total prunable > `PRUNE_MINIMUM` (20k)
5. Requires at least 2 user turns before activating

**Placeholder Replacement (`packages/opencode/src/session/message-v2.ts`):**

```typescript
output: part.state.time.compacted
  ? "[Old tool result content cleared]"
  : part.state.output;
```

**Key Insight:** Preserves conversation structure (tool was called, result existed) while freeing token budget.

#### Layer 2: Emergency Summarization (Context Overflow)

**Trigger:** `isOverflow()` returns true when:

```
(input + cache_read + output) > (context_limit - output_limit)
```

- Auto-compaction at **92% context window usage**
- OUTPUT_TOKEN_MAX: 32,000 tokens

**Summarization Process:**

1. Create new assistant message marked as "summary"
2. Apply compaction system prompt
3. Stream summary generation to user
4. Append "Continue if you have next steps" for auto-compaction

**Summary Content:**

- Completed work and finished tasks
- Current state and modified files
- In-progress work
- Next steps and clear actions
- Constraints (user preferences, project requirements)
- Critical context essential for continuing

#### Layer 3: UI Summaries (Separate)

**Location:** `packages/opencode/src/session/summary.ts`

**Purpose:** Display-only summaries for UI, separate from context compaction

- **Title:** ~20 tokens using small models (haiku, flash, nano)
- **Body:** Up to 100 tokens of conversation context
- **Diffs:** Structured file change data

---

## Key Patterns / Solutions Found

### Pattern 1: Backward-Scanning Token Budget

```
Protect last N tokens → Only prune what exceeds budget → Apply minimum threshold
```

- **OpenCode values:** Protect 40k, minimum prune 20k
- **Rationale:** Recent tool outputs are more likely to be referenced

### Pattern 2: Placeholder Replacement

```
Replace content with "[Old tool result content cleared]"
```

- Preserves conversation structure
- LLM knows a tool was called and returned something
- Frees token budget without losing history

### Pattern 3: Tiered Summarization

```
Layer 1: Prune tool outputs (cheap, automatic)
Layer 2: Full conversation summary (expensive, emergency)
```

- Pruning happens first, frequently
- Summarization only when pruning isn't enough

### Pattern 4: Control Knobs

```
OPENCODE_DISABLE_PRUNE=true
OPENCODE_DISABLE_AUTOCOMPACT=true
```

- Environment variables for debugging/control
- User can disable if causing issues

---

## Implementation Recommendations for TunaCode

### Phase 1: Tool Output Pruning (Low Effort, High Impact)

**New File:** `src/tunacode/core/compaction.py`

```python
PRUNE_PROTECT = 40_000  # Protect last 40k tokens of tool outputs
PRUNE_MINIMUM = 20_000  # Only prune if savings > 20k tokens
PLACEHOLDER = "[Old tool result content cleared]"

def prune_old_tool_outputs(messages: list, model: str) -> list:
    """Replace old tool output content with placeholder."""
    # Scan backwards, accumulate tool output tokens
    # Mark for compaction once exceeding PRUNE_PROTECT
    # Return modified message list
```

**Integration Point:** Call before `agent.iter()` in `main.py:367`

### Phase 2: Context Overflow Detection

**Add to:** `src/tunacode/core/state.py`

```python
def is_context_overflow(self) -> bool:
    """Check if approaching context limit (92% threshold)."""
    return self.total_tokens > (self.max_tokens * 0.92)
```

### Phase 3: Emergency Summarization

**Implement:** `/compact` command in `ui/commands/__init__.py`

```python
async def compact_command(app):
    """Summarize conversation to free context."""
    summary = await generate_summary(app.state_manager.session.messages)
    app.state_manager.session.messages = [summary_message]
```

### Phase 4: Auto-Compaction

**Add to agent loop:** Check `is_context_overflow()` before each request, trigger compaction if true.

---

## Knowledge Gaps

1. **pydantic-ai message structure:** Need to understand exact format of tool result messages to implement pruning
2. **Cache token handling:** OpenCode tracks cache hits separately - need to verify if pydantic-ai provides this
3. **Summary generation prompt:** Need to design effective compaction prompt for tunacode's use case

---

## References

### TunaCode Files

- `src/tunacode/core/state.py` → Session state and message storage
- `src/tunacode/core/agents/main.py` → Agent loop and message history passing
- `src/tunacode/core/agents/agent_components/node_processor.py` → Message accumulation
- `src/tunacode/utils/messaging/token_counter.py` → Token estimation
- `src/tunacode/ui/renderers/panels.py` → Display truncation (cosmetic only)

### OpenCode References (External)

- `packages/opencode/src/session/compaction.ts` → Pruning logic
- `packages/opencode/src/session/message-v2.ts` → Placeholder replacement
- `packages/opencode/src/session/summary.ts` → UI summaries
- [GitHub: sst/opencode](https://github.com/sst/opencode)
- [DeepWiki: OpenCode Session Management](https://deepwiki.com/sst/opencode/2.1-session-lifecycle-and-state)

### Related Issues

- [OpenCode #3325: Disable Auto-Compact Feature Request](https://github.com/sst/opencode/issues/3325)
- [OpenCode #3917: Document Pruning Functionality](https://github.com/sst/opencode/issues/3917)
- [OpenCode #4113: Compaction Token Debug Issue](https://github.com/sst/opencode/issues/4113)

---
