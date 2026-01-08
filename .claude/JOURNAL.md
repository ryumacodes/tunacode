# Claude Journal

## 2026-01-07: Renderer Unification

Unifying the 8 tool renderers in `src/tunacode/ui/renderers/tools/` to eliminate duplication via a shared base class and registry pattern.

### Completed:
- T2: Created `base.py` with `BaseToolRenderer[T]` ABC and `ToolRendererProtocol`
- T3: Extracted shared helpers: `truncate_line`, `truncate_content`, `pad_lines`
- T4: Added registry pattern: `@tool_renderer`, `get_renderer`, `list_renderers`
- Migrated `list_dir.py` to use `BaseToolRenderer` (199 -> 149 lines)
- Created documentation at `docs/ui/tool_renderers.md`
- All 182 tests passing

### Next Action:
Migrate remaining 7 renderers to use `BaseToolRenderer`:
- `bash.py` (has conditional border color based on exit code - good test of override pattern)
- `read_file.py`
- `update_file.py`
- `glob.py`
- `grep.py`
- `web_fetch.py`
- `research.py`

### Architecture Decisions Made:
- Module-level singleton renderer instances (not created per-call)
- Render functions remain the public API (backward compatible)
- `@tool_renderer` decorator for self-registration
- Helpers are standalone functions, not methods (easier to use without instantiation)

---

## 2026-01-07: Local Mode Context Optimization

### Task: Reduce context usage for local models with small context windows (10k)

### Problem:
- System prompt + tool schemas used ~3.5k tokens before any conversation
- Each file read could use 2000 lines (~20k tokens)
- With 10k context, only ~6.5k left for conversation
- LLM APIs are stateless - system prompt sent every turn

### Completed:

**1. Minimal System Prompt**
- Created `CLAUDE_LOCAL.md` - condensed project instructions (~400 tokens)
- Added `LOCAL_TEMPLATE` in `templates.py` - only 3 sections: AGENT_ROLE, TOOL_USE, USER_INSTRUCTIONS
- `local_mode: true` setting triggers minimal template

**2. Minimal Tool Schemas**
- Reduced from 11 tools to 6 (bash, read_file, update_file, write_file, glob, list_dir)
- Removed: grep, web_fetch, research_codebase, todo tools
- 1-word descriptions ("Shell", "Read", "Edit", etc.) - saves ~1k tokens

**3. Aggressive Pruning**
- LOCAL_PRUNE_PROTECT_TOKENS: 2,000 (vs 40,000)
- LOCAL_PRUNE_MINIMUM_THRESHOLD: 500 (vs 20,000)
- Messages pruned much faster to save context

**4. Tool Output Limits**
- LOCAL_DEFAULT_READ_LIMIT: 200 lines (vs 2,000)
- LOCAL_MAX_LINE_LENGTH: 500 chars (vs 2,000)
- LOCAL_MAX_COMMAND_OUTPUT: 1,500 chars (vs 5,000)

**5. Response Limit**
- local_max_tokens: 1000 - caps model output per turn

### Token Budget (Local Mode):
| Component | Tokens |
|-----------|--------|
| System prompt | ~1,117 |
| Guide file | ~527 |
| 6 tools (minimal) | ~575 |
| **Total base** | **~2,200** |

With 10k context: ~7.8k available for conversation

### Key Insight:
LLM APIs are stateless. Every request sends: system prompt + tool schemas + full conversation history. Model has no memory - re-reads everything each turn.

---

## 2026-01-06: Local Model Support

### Task: Add local model support to tunacode

### Completed:
- Created condensed system prompt at `src/tunacode/prompts/local_model_prompt.txt` (~500 bytes vs 34KB full prompt)
- Added `local_model: true/false` setting in config defaults
- Modified `load_system_prompt()` to use condensed prompt when `local_model=true`
- Added cache invalidation for `local_model` setting in `_compute_agent_version()`
- Skip AGENTS.md loading for local models to save tokens
- Created `fallback_executor.py` for models that output tool calls in text (e.g., `<tool_call>` tags)
- Updated `node_processor.py` to detect and execute fallback tool calls
- Passed `agent_ctx` through the call chain for result injection
- Tested with multiple local models via LM Studio/vLLM

### Notes:
- Qwen2.5-Coder-14B supports native OpenAI tool calling format
- Smaller models (0.6B-1.7B) output `<tool_call>` tags in content - fallback parser handles this
- llama.cpp uses KV cache efficiently (LCP similarity) so repeated prompt not re-computed
