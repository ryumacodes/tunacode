# Research - Messages and Pruning: Local vs API Mode

**Date:** 2026-01-08
**Owner:** agent
**Phase:** Research

## Goal

Map the message handling and pruning mechanisms between local mode and API mode in tunacode, understanding how context window constraints are managed differently for each mode.

## Executive Summary

Local mode and API mode **share 100% of the same provider and message handling code**. There are no separate providers, adapters, or message transformers. The difference is purely in **token optimization** applied at multiple layers before messages reach the provider. Local mode is a binary switch (`local_mode: true`) that cascades through 6 optimization layers to reduce token consumption by ~70%.

## Findings

### Key Architecture Discovery

**No Separate Providers Exist**

Both modes use identical provider classes at `src/tunacode/core/agents/agent_components/agent_config.py:308-359`:
- Anthropic models -> `AnthropicProvider`
- Other models -> `OpenAIProvider`

The same HTTP client, retry logic, and provider instances are used regardless of mode.

### Relevant Files & Why They Matter

| File | Purpose |
|------|---------|
| `src/tunacode/core/limits.py` | Central mode detection and limit calculations |
| `src/tunacode/core/compaction.py` | Message pruning algorithm |
| `src/tunacode/core/agents/main.py:367-372` | Pruning trigger point |
| `src/tunacode/core/agents/agent_components/agent_config.py` | Agent creation with mode-aware tooling |
| `src/tunacode/core/prompting/templates.py` | System prompt templates |
| `src/tunacode/core/prompting/local_prompt.md` | Condensed guide for local mode |
| `src/tunacode/constants.py:29-35` | Limit constants for both modes |
| `src/tunacode/utils/messaging/token_counter.py` | Token estimation |

### 6 Optimization Layers

#### Layer 1: System Prompt Selection
**Location:** `agent_config.py:236-245`

| Mode | Template | Sections |
|------|----------|----------|
| API | `MAIN_TEMPLATE` | 11 sections (~3,500 tokens) |
| Local | `LOCAL_TEMPLATE` | 3 sections (~1,100 tokens) |

**Savings:** ~2,400 tokens

#### Layer 2: Guide File Context
**Location:** `agent_config.py:248-291`

| Mode | File | Size |
|------|------|------|
| API | User's `AGENTS.md` | Variable (~2k+ tokens) |
| Local | `local_prompt.md` | ~500 tokens |

#### Layer 3: Tool Set Reduction
**Location:** `agent_config.py:406-444`

| Mode | Tools | Description Style |
|------|-------|-------------------|
| API | 11 tools | Full descriptions |
| Local | 6 tools | 1-word descriptions |

**Local tools:** bash, read_file, update_file, write_file, glob, list_dir
**Omitted in local:** grep, web_fetch, research_codebase, todo tools

**Savings:** ~1,000 tokens from schemas

#### Layer 4: Tool Output Limits
**Location:** `limits.py:42-56`, `constants.py:24-34`

| Setting | API Mode | Local Mode |
|---------|----------|------------|
| `read_limit` | 2000 lines | 200 lines |
| `max_line_length` | 2000 chars | 500 chars |
| `max_command_output` | 5000 chars | 1500 chars |
| `max_files_in_dir` | 50 files | 20 files |

#### Layer 5: Response Token Cap
**Location:** `limits.py:84-96`

| Mode | max_tokens |
|------|------------|
| API | unlimited |
| Local | 1000 (default) |

#### Layer 6: Message Pruning Thresholds
**Location:** `compaction.py:14-32`

| Threshold | API Mode | Local Mode |
|-----------|----------|------------|
| Protection window | 40,000 tokens | 2,000 tokens |
| Minimum threshold | 20,000 tokens | 500 tokens |

**Local mode prunes 20x more aggressively**

### Pruning Algorithm Deep Dive

**Location:** `compaction.py:160-238`

**Trigger:** Start of each request at `main.py:369`:
```python
session_messages = self.state_manager.session.messages
_, tokens_reclaimed = prune_old_tool_outputs(session_messages, self.model)
```

**Algorithm Phases:**

1. **Backward Scanning** (lines 187-204)
   - Iterates messages newest-to-oldest
   - Identifies tool return parts (`part_kind == "tool-return"`)
   - Estimates token count for each

2. **Protection Boundary** (lines 209-221)
   - Accumulates tokens from newest
   - Marks boundary when protection threshold exceeded
   - Recent outputs within window remain untouched

3. **Threshold Check** (lines 223-229)
   - Calculates potential savings
   - Only proceeds if savings > minimum threshold

4. **Content Replacement** (lines 231-236)
   - Replaces old content with `"[Old tool result content cleared]"`
   - In-place mutation of message parts

**Safety Guards:**
- Requires 2+ user turns before pruning (`PRUNE_MIN_USER_TURNS = 2`)
- Handles immutable parts gracefully
- Skips already-pruned parts

### Message Structure

**Type System:** Uses pydantic-ai's standard types (`types/pydantic_ai.py`):
- `ModelRequest` - requests sent to model
- `ToolReturnPart` - tool execution results
- `SystemPromptPart` - system messages

**Identical in both modes** - no transformation occurs. Only content size differs.

### Configuration Precedence

**Three-tier system at `limits.py:42-56`:**
```
explicit setting > local_mode default > standard default
```

**Config location:** `~/.config/tunacode.json`

```json
{
  "settings": {
    "local_mode": true,
    "local_max_tokens": 1000,
    "read_limit": 200
  }
}
```

### Token Budget Comparison

| Component | API Mode | Local Mode |
|-----------|----------|------------|
| System prompt | ~3,500 tokens | ~1,100 tokens |
| Guide file | ~2,000+ tokens | ~500 tokens |
| Tool schemas | ~1,800 tokens | ~575 tokens |
| **Total base** | **~7,300+** | **~2,200** |

**With 10k context window:**
- API mode: ~2,700 tokens for conversation
- Local mode: ~7,800 tokens for conversation

## Key Patterns / Solutions Found

| Pattern | Description | Relevance |
|---------|-------------|-----------|
| Binary Switch | `is_local_mode()` single check cascades 6 optimizations | Central control point |
| Cascading Defaults | `explicit > local > standard` precedence | Flexible configuration |
| Provider Agnostic | All optimization at message prep layer | Same providers for both |
| In-Place Mutation | Prunes by modifying existing messages | Memory efficient |
| Backward Scanning | Newest-to-oldest preserves recent context | User experience |

## Data Flow Diagram

```
User Message
     |
     v
RequestOrchestrator._run_impl() [main.py:527]
     |
     v
get_or_create_agent() [agent_config.py]
     |   - Selects template (LOCAL_TEMPLATE vs MAIN_TEMPLATE)
     |   - Selects tools (6 vs 11)
     |   - Applies max_tokens
     v
prune_old_tool_outputs() [compaction.py]
     |   - Backward scan
     |   - Protect recent outputs
     |   - Replace old with placeholder
     v
agent.iter() -> Provider HTTP Request
     |
     v
(Same pydantic-ai message format for both modes)
```

## Knowledge Gaps

- Token estimation uses simple 4-char heuristic, not model-specific tokenizer
- `tokens_reclaimed` from pruning is currently discarded (stored in `_` at main.py:369)
- No runtime mode switching - requires restart to change modes

## References

- `src/tunacode/core/compaction.py` - Pruning implementation
- `src/tunacode/core/limits.py` - Mode detection and limits
- `src/tunacode/core/agents/main.py:367-372` - Pruning trigger
- `src/tunacode/core/agents/agent_components/agent_config.py` - Agent creation
- `src/tunacode/core/prompting/templates.py` - Template definitions
- `src/tunacode/constants.py` - Limit constants
- `docs/configuration/README.md` - Configuration documentation
- `docs/codebase-map/modules/core-compaction.md` - Compaction docs
- `docs/codebase-map/modules/core-limits.md` - Limits docs
- `tests/test_compaction.py` - Test coverage
