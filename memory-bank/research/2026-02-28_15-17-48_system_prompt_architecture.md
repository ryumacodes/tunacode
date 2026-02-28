# Research – System Prompt Architecture
**Date:** 2026-02-28
**Time:** 15:17:48
**Owner:** claude
**Phase:** Research
**Last Updated:** 2026-02-28
**Last Updated By:** claude
**Git Commit:** 56a05fc710fb8be960993f290f07ff01bb283de5
**Git Branch:** master
**Tags:** system-prompt, architecture, tinyagent, tools, prompts

## Goal
Map out the system prompt architecture in tunacode - where it lives, how it's constructed, what components it includes, and how it flows through the agent loop.

## Additional Search
- `grep -ri "system.prompt" .claude/` - No matches in .claude/ directory
- `grep -ri "system_prompt" src/` - Found matches in agent_config.py, canonical.py, adapters

## Findings

### Relevant files & why they matter:

**Core Prompt Definition:**
- `src/tunacode/prompts/system_prompt.md` - Main system prompt template with XML-style tagged sections (role, context, tools, instructions, examples, completion, user_context)

**Prompt Construction & Loading:**
- `src/tunacode/core/agents/agent_components/agent_config.py:144-174` - `load_system_prompt()` and `load_tunacode_context()` functions
- `src/tunacode/core/agents/agent_components/agent_config.py:380-443` - `get_or_create_agent()` assembles final prompt
- `src/tunacode/core/agents/agent_components/agent_config.py:216-226` - `_build_tools()` creates tool set

**Tool Prompt Integration:**
- `src/tunacode/tools/decorators.py:72-74` - XML prompt injection into tool docstrings
- `src/tunacode/tools/decorators.py:134-206` - `to_tinyagent_tool()` adapter with schema generation
- `src/tunacode/tools/xml_helper.py:13-46` - `load_prompt_from_xml()` loads tool-specific prompts
- `src/tunacode/tools/prompts/` - XML prompt files for bash, discover, hashline_edit, read_file, write_file, web_fetch

**Context Caching:**
- `src/tunacode/infrastructure/cache/caches/tunacode_context.py` - Mtime-aware cache for AGENTS.md
- `src/tunacode/tools/cache_accessors/xml_prompts_cache.py` - Mtime-aware cache for XML prompts

**Type Definitions:**
- `src/tunacode/types/canonical.py:60` - `SystemPromptPart` class definition
- `src/tunacode/utils/messaging/adapter.py:218` - Message conversion handling

**Entry Point:**
- `src/tunacode/core/agents/main.py:182` - Agent retrieval during request processing

**Configuration:**
- `src/tunacode/configuration/settings.py` - Configurable `guide_file` setting
- `src/tunacode/configuration/defaults.py` - Default guide file setting
- `src/tunacode/constants.py` - `GUIDE_FILE_NAME = "AGENTS.md"`

## Key Patterns / Solutions Found

### 1. Two-Stage Prompt Composition
```
Final System Prompt = Static MD + Dynamic Context
├── Static: src/tunacode/prompts/system_prompt.md
│   └── XML-tagged sections (role, context, tools, instructions, examples, completion, user_context)
└── Dynamic: load_tunacode_context()
    └── AGENTS.md (or custom guide_file from config)
```

### 2. Separate Tool Schema Configuration
- Tools are NOT included in the text system prompt
- Tools configured via `agent.set_tools()` with JSON Schema
- Tool descriptions loaded from XML prompts or Python docstrings
- tinyagent handles tool serialization to OpenAI function-calling format

### 3. Three-Level Caching
- **Agent instances:** Cached by model name + configuration hash (`_compute_agent_version`)
- **File content:** Mtime-aware caches for AGENTS.md and XML prompts
- **Settings:** Configuration fingerprinting for cache invalidation

### 4. Decorator-Based Tool Integration
- `@base_tool` and `@file_tool` decorators wrap functions
- XML prompts automatically loaded and injected into `__doc__`
- Type annotations converted to JSON Schema via `_build_openai_parameters_schema()`

### 5. Concurrency Limiting
- `MAX_PARALLEL_TOOL_CALLS = 3` default
- Tools wrapped with `asyncio.Semaphore` for execution limits

## System Prompt Structure

The `system_prompt.md` file contains these tagged sections:

| Tag | Content |
|-----|---------|
| `<role>` | "TunaCode, Staff-level software developer" |
| `<context>` | Behavioral guidelines (step-by-step, fail fast) |
| `<tools>` | High-level descriptions of 6 tools (discover, read_file, hashline_edit, write_file, bash, web_fetch) |
| `<instructions>` | Workflow rules (Discover -> Inspect -> Act) |
| `<examples>` | Example workflows |
| `<completion>` | "DONE:" task completion signal |
| `<user_context>` | Placeholder for dynamic content (AGENTS.md appended after) |

## Data Flow

```
1. User Request (UI/CLI)
   ↓
2. main.py:process_request()
   ↓
3. get_or_create_agent(model, state_manager)
   ↓
4. Load System Prompt
   ├── load_system_prompt() → system_prompt.md
   └── load_tunacode_context() → AGENTS.md
   ↓
5. Build Tools
   ├── to_tinyagent_tool() for each tool
   ├── _build_openai_parameters_schema() → JSON Schema
   └── _apply_tool_concurrency_limit()
   ↓
6. Create tinyagent Agent
   ├── agent.set_system_prompt(combined_prompt)
   ├── agent.set_model(model_config)
   └── agent.set_tools(tools_list)
   ↓
7. agent.stream(message)
   ↓
8. tinyagent constructs API payload
   ├── System message
   ├── Tools (JSON Schema)
   └── Conversation history
```

## Configuration Affecting System Prompt

| Setting | Location | Default | Effect |
|---------|----------|---------|--------|
| `guide_file` | `~/.config/tunacode.json` | "AGENTS.md" | Dynamic context source |
| `max_tokens` | Settings file | 4096 | Response length limit |
| `request_delay` | Settings file | 0.0 | Pre-request throttle |
| `global_request_timeout` | Settings file | 90.0 | Request timeout |
| `tool_strict_validation` | Settings file | false | Tool parameter validation |
| `MAX_PARALLEL_TOOL_CALLS` | constants.py | 3 | Concurrent tool execution |

## Tool-Specific Prompts

Located in `src/tunacode/tools/prompts/`:
- `bash_prompt.xml` - Bash command execution
- `discover_prompt.xml` - File discovery patterns
- `hashline_edit_prompt.xml` - Line-based editing
- `read_file_prompt.xml` - File reading
- `write_file_prompt.xml` - File writing
- `web_fetch_prompt.xml` - Web content fetching

Each XML file contains a `<description>` element that replaces the tool's docstring when loaded.

## Knowledge Gaps

1. **Model-specific prompts:** The `model` parameter exists in `load_system_prompt()` but is currently unused (line 147 of agent_config.py). There may be plans for model-specific prompt variations.

2. **UI prompt manipulation:** Current UI does not modify the system prompt directly. Future requirements may include user-editable prompt sections.

3. **Prompt versioning:** No explicit version tracking for prompt changes beyond agent configuration hash.

## References

### GitHub Permalinks (as of commit 56a05fc7)

- [system_prompt.md](https://github.com/alchemiststudiosDOTai/tunacode/blob/56a05fc710fb8be960993f290f07ff01bb283de5/src/tunacode/prompts/system_prompt.md)
- [agent_config.py](https://github.com/alchemiststudiosDOTai/tunacode/blob/56a05fc710fb8be960993f290f07ff01bb283de5/src/tunacode/core/agents/agent_components/agent_config.py)
- [decorators.py](https://github.com/alchemiststudiosDOTai/tunacode/blob/56a05fc710fb8be960993f290f07ff01bb283de5/src/tunacode/tools/decorators.py)
- [main.py](https://github.com/alchemiststudiosDOTai/tunacode/blob/56a05fc710fb8be960993f290f07ff01bb283de5/src/tunacode/core/agents/main.py)

### Local Files

- `src/tunacode/prompts/` - System prompt directory
- `src/tunacode/tools/prompts/` - Tool XML prompts directory
- `src/tunacode/infrastructure/cache/caches/` - Caching implementations
- `src/tunacode/configuration/models_registry.json` - Model configuration

## Historical Context

### Migration (2026-01-26)
The system was migrated from a complex multi-section XML system (11 section files + 3 template modules) to the current single Markdown file approach. Tool prompts remain as separate XML files for modularity.
