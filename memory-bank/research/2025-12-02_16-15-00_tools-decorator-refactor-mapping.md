# Research – Tools Directory Post-Refactor Architecture Mapping

**Date:** 2025-12-02
**Owner:** Claude Agent
**Phase:** Research
**Git Commit:** 42e2aa9

## Goal

Document the new tools directory architecture after the decorator pattern refactoring (commit 42e2aa9). Map out file structure, decorator patterns, dependencies, and tool registration flow.

## Background

The tools directory was refactored from a class-based hierarchy to a decorator-based functional pattern:
- **Before:** Tools inherited from `BaseTool`/`FileBasedTool` classes
- **After:** Tools are decorated async functions using `@base_tool` or `@file_tool`
- **Impact:** ~35% code reduction (2500 lines -> 1617 lines)

## Current Directory Structure

```
src/tunacode/tools/
├── __init__.py           # Lazy loading via __getattr__
├── decorators.py         # @base_tool and @file_tool decorators (89 lines)
├── bash.py               # Shell command execution
├── glob.py               # File pattern matching
├── grep.py               # Parallel content search (retains ParallelGrep class)
├── list_dir.py           # Directory listing
├── read_file.py          # File reading
├── run_command.py        # Command execution (security-focused)
├── update_file.py        # File modification (fuzzy matching)
├── write_file.py         # File creation
├── react.py              # ReAct scratchpad (wrapper class retained)
├── xml_helper.py         # XML prompt/schema loader (UNUSED)
├── grep_components/      # Modular grep implementation
│   ├── __init__.py
│   ├── file_filter.py    # Fast glob prefiltering (MAX_GLOB=5000)
│   ├── pattern_matcher.py # Search and relevance scoring
│   ├── result_formatter.py # Output formatting (content/files/count/json)
│   └── search_result.py  # SearchResult, SearchConfig DTOs
├── utils/
│   ├── __init__.py
│   ├── text_match.py     # Fuzzy text replacement (4-strategy cascade)
│   └── ripgrep.py        # Ripgrep binary management with fallback
└── prompts/              # XML tool definitions (9 files)
    ├── bash_prompt.xml
    ├── glob_prompt.xml
    ├── grep_prompt.xml
    ├── list_dir_prompt.xml
    ├── react_prompt.xml
    ├── read_file_prompt.xml
    ├── run_command_prompt.xml
    ├── update_file_prompt.xml
    └── write_file_prompt.xml
```

## Findings

### Decorator Pattern Implementation

**decorators.py** provides two decorators:

#### `@base_tool` (lines 21-51)
- Wraps async tool functions with error handling and logging
- Exception strategy:
  - `ModelRetry` → preserved (allows LLM to retry)
  - `ToolExecutionError` → preserved (already formatted)
  - `FileOperationError` → preserved
  - All others → wrapped in `ToolExecutionError`

#### `@file_tool` (lines 54-89)
- Specialized for file operations with path-specific error handling
- `FileNotFoundError` → `ModelRetry` (LLM can correct path)
- `PermissionError`, `IOError`, `OSError` → `FileOperationError`
- Composition: `@file_tool` wraps result with `@base_tool`

### Tool Function Signatures

| Tool | Decorator | Signature |
|------|-----------|-----------|
| `bash` | `@base_tool` | `async def bash(command, cwd=None, env=None, timeout=30, capture_output=True) -> str` |
| `glob` | `@base_tool` | `async def glob(pattern, directory=".", recursive=True, include_hidden=False, ...) -> str` |
| `grep` | `@base_tool` | `async def grep(pattern, directory=".", path=None, case_sensitive=False, ...) -> Union[str, List[str]]` |
| `list_dir` | `@base_tool` | `async def list_dir(directory=".", max_entries=200, show_hidden=False) -> str` |
| `run_command` | `@base_tool` | `async def run_command(command: str) -> str` |
| `read_file` | `@file_tool` | `async def read_file(filepath: str) -> str` |
| `write_file` | `@file_tool` | `async def write_file(filepath: str, content: str) -> str` |
| `update_file` | `@file_tool` | `async def update_file(filepath: str, target: str, patch: str) -> str` |

### Tool Registration Flow

```
Tool Definition (bash.py, grep.py, etc.)
    │
    └─► Decorated async function
            │
            ▼
Tool Import (agent_config.py:339-354)
    │
    └─► from tunacode.tools.bash import bash
        from tunacode.tools.grep import grep
        ...
            │
            ▼
Pydantic-AI Wrapping
    │
    └─► Tool(bash, max_retries=N, strict=bool)
        Tool(grep, max_retries=N, strict=bool)
        ...
            │
            ▼
Agent Constructor
    │
    └─► Agent(model, system_prompt, tools=tools_list)
```

**Registration Locations:**
- `src/tunacode/core/agents/agent_components/agent_config.py:339-354` → Main agent (8 tools + research_codebase)
- `src/tunacode/core/agents/research_agent.py:104-110` → Research agent (read-only subset: grep, glob, list_dir, limited_read_file)

### Special Cases

#### ParallelGrep Class (grep.py)
- **Retained** despite decorator refactor due to implementation complexity
- Composes: FileFilter, PatternMatcher, ResultFormatter, RipgrepExecutor
- Four search strategies: Python (≤50 files), Ripgrep (≤1000 files), Hybrid (>1000 files)
- Public interface: decorated `grep()` function wraps `ParallelGrep.execute()`

#### ReactTool Class (react.py)
- **Retained** for backward compatibility
- Factory function: `create_react_tool(state_manager)` returns async function
- Wrapper class: `ReactTool` delegates to factory-created function
- Actions: think, observe, get, clear

### Dependency Graph

```
Internal Dependencies:
─────────────────────
decorators.py
├─► bash.py, glob.py, grep.py, list_dir.py, run_command.py (@base_tool)
└─► read_file.py, write_file.py, update_file.py (@file_tool)

grep.py
├─► grep_components/ (FileFilter, PatternMatcher, ResultFormatter, SearchResult, SearchConfig)
└─► utils/ripgrep.py (RipgrepExecutor, metrics)

update_file.py
└─► utils/text_match.py (replace function)

External Dependencies:
──────────────────────
tunacode.constants
├─► MAX_COMMAND_OUTPUT (bash.py, run_command.py)
├─► MAX_FILE_SIZE (read_file.py)
└─► CMD_OUTPUT_FORMAT (run_command.py)

tunacode.exceptions
├─► ToolExecutionError (decorators.py, grep.py, read_file.py)
├─► FileOperationError (decorators.py)
└─► TooBroadPatternError (grep.py)

tunacode.core.code_index.CodeIndex
├─► glob.py (cache-accelerated search)
└─► list_dir.py (directory caching)

pydantic_ai.exceptions.ModelRetry
└─► decorators.py, bash.py, react.py, update_file.py, write_file.py
```

### Helper Modules

| Module | Purpose | Used By |
|--------|---------|---------|
| `decorators.py` | Error handling + logging | All tools |
| `xml_helper.py` | XML prompt loading | decorators.py (loads alignment prompts) |
| `utils/text_match.py` | Fuzzy replacement (4 strategies) | update_file.py |
| `utils/ripgrep.py` | Binary resolution + fallback | grep.py |
| `grep_components/` | Modular grep (SRP) | grep.py |

### Text Match Strategies (utils/text_match.py)

Ordered from strict to fuzzy:
1. `simple_replacer` → Exact substring match
2. `line_trimmed_replacer` → Trim whitespace per line
3. `indentation_flexible_replacer` → Normalize indentation
4. `block_anchor_replacer` → Fuzzy with first/last line anchors + Levenshtein

### Ripgrep Resolution (utils/ripgrep.py)

1. Environment: `TUNACODE_RIPGREP_PATH`
2. System: `shutil.which("rg")` if version ≥13.0.0
3. Bundled: `vendor/ripgrep/{platform}/rg`
4. Fallback: Python `Path.glob()` + regex search

## Key Patterns / Solutions Found

| Pattern | Implementation | Location |
|---------|---------------|----------|
| Decorator Composition | `@file_tool` wraps with `@base_tool` | decorators.py:89 |
| Async Executor | `asyncio.to_thread()` for blocking I/O | read_file.py:35, list_dir.py:42 |
| Fail-Fast Validation | `ModelRetry` for correctable errors | All tools |
| CodeIndex Integration | Try cache first, fallback to filesystem | glob.py:78-83, list_dir.py:37-39 |
| Composition over Inheritance | ParallelGrep composes components | grep.py:38-46 |
| Strategy Selection | Size-based: Python/Ripgrep/Hybrid | grep.py:121-131 |
| Graceful Degradation | Ripgrep → Python fallback | ripgrep.py |

## Knowledge Gaps / Regressions

1. ~~**xml_helper.py DISCONNECTED**~~ → **FIXED** - `@base_tool` decorator now loads XML prompts and sets as `wrapper.__doc__`. Pydantic-ai uses this for tool descriptions sent to LLM.
2. **ReactTool wrapper** → Retained for backward compatibility. Which call sites need migration?
3. **bash.py vs run_command.py** → Overlapping functionality. Consolidation planned?
4. **Parameter naming** → Inconsistent: `filepath` vs `directory` vs `path`

## Refactoring Impact Summary

### Removed
- `base.py` → `BaseTool`, `FileBasedTool` classes deleted
- `schema_assembler.py` → `ToolSchemaAssembler` deleted
- Class-based tool implementations in all tool files

### Added
- `decorators.py` → Lightweight decorator pattern
- Decorated async functions in all tool files

### Retained
- `ParallelGrep` class in grep.py (complexity)
- `ReactTool` wrapper class in react.py (compatibility)
- All utility modules (xml_helper, text_match, ripgrep, grep_components)

### Metrics
- **Lines removed:** ~1500
- **Lines added:** ~600
- **Net reduction:** ~35%

## References

- `src/tunacode/tools/decorators.py` → Core decorator implementation
- `src/tunacode/tools/grep.py` → Most complex tool (composition example)
- `src/tunacode/core/agents/agent_components/agent_config.py:339-354` → Tool registration
- `src/tunacode/tools/grep_components/` → Modular grep architecture
- `src/tunacode/tools/utils/text_match.py` → Fuzzy matching strategies
- `memory-bank/research/2025-12-02_14-30-00_tools-directory-mapping.md` → Pre-refactor mapping
