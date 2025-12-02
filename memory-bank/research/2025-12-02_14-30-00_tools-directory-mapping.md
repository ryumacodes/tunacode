# Research – Tools Directory Mapping for Refactoring

**Date:** 2025-12-02
**Owner:** Claude Agent
**Phase:** Research
**Git Commit:** 4d691cf

## Goal

Map out the complete structure, dependencies, and patterns in `/home/fabian/tunacode/src/tunacode/tools/` to understand the architecture before refactoring.

## Directory Structure

```
src/tunacode/tools/
├── __init__.py           # Lazy loading of submodules
├── base.py               # BaseTool, FileBasedTool abstract classes (375 lines)
├── bash.py               # BashTool - shell command execution (362 lines)
├── glob.py               # GlobTool - file pattern matching (587 lines)
├── grep.py               # ParallelGrep - content search (552 lines)
├── list_dir.py           # ListDirTool - directory listing (321 lines)
├── read_file.py          # ReadFileTool - file reading (192 lines)
├── run_command.py        # RunCommandTool - command execution (238 lines)
├── update_file.py        # UpdateFileTool - file modification (207 lines)
├── write_file.py         # WriteFileTool - file creation (168 lines)
├── react.py              # ReactTool - ReAct scratchpad (154 lines)
├── schema_assembler.py   # ToolSchemaAssembler helper (168 lines)
├── xml_helper.py         # XML prompt/schema loading (84 lines)
├── grep_components/      # Modular grep implementation
│   ├── __init__.py
│   ├── file_filter.py    # Fast glob prefiltering
│   ├── pattern_matcher.py # Search and relevance scoring
│   ├── result_formatter.py # Output formatting
│   └── search_result.py  # SearchResult, SearchConfig DTOs
├── utils/                # General utilities
│   ├── __init__.py
│   ├── text_match.py     # Fuzzy text replacement
│   └── ripgrep.py        # Ripgrep binary wrapper
└── prompts/              # XML tool definitions
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

### Core Architecture

#### Base Classes (`base.py`)
- `BaseTool` (line 18): Abstract base for all tools
  - Template method pattern: `execute()` wraps `_execute()`
  - Resource management with automatic cleanup
  - Prompt generation with caching
  - Context manager support (`__aenter__`, `__aexit__`)

- `FileBasedTool` (line 305): Extends `BaseTool` for file operations
  - Enhanced error handling for `IOError`, `OSError`, `PermissionError`
  - Path-specific error context

#### Dual Implementation Pattern
Each tool has TWO implementations:
1. **Class** (inherits `BaseTool`/`FileBasedTool`) - for full functionality
2. **Async function** (standalone) - for pydantic-ai compatibility

| Tool | Class | Async Function |
|------|-------|----------------|
| bash.py | `BashTool` (line 28) | `bash()` (line 334) |
| grep.py | `ParallelGrep` (line 40) | `grep()` (line 500) |
| glob.py | `GlobTool` (line 52) | `glob()` (line 537) |
| list_dir.py | `ListDirTool` (line 24) | `list_dir()` (line 300) |
| read_file.py | `ReadFileTool` (line 32) | `read_file()` (line 176) |
| write_file.py | `WriteFileTool` (line 24) | `write_file()` (line 150) |
| update_file.py | `UpdateFileTool` (line 25) | `update_file()` (line 188) |
| run_command.py | `RunCommandTool` (line 35) | `run_command()` (line 222) |

### Tool Registration Flow

```
Tool Definition (bash.py, grep.py, etc.)
    ├─ Tool Class extends BaseTool
    └─ Async Function for pydantic-ai

Tool Registration (agent_config.py:340-353)
    ├─ Imports tool functions
    ├─ Wraps with pydantic_ai.Tool(func, max_retries=N)
    └─ Passes to Agent constructor

Tool Execution (node_processor.py)
    ├─ Categorizes (READ_ONLY vs others)
    ├─ tool_executor.py runs (parallel for safe tools)
    └─ BaseTool.execute() handles cleanup
```

### Subdirectory Analysis

#### `utils/` - General Utilities
- **text_match.py**: Fuzzy string replacement with ordered strategies
  - `simple_replacer` → `line_trimmed_replacer` → `indentation_flexible_replacer` → `block_anchor_replacer`
  - Used by: `update_file.py:19`

- **ripgrep.py**: Ripgrep binary management with Python fallback
  - Resolution: ENV var → system rg → bundled binary → Python fallback
  - Used by: `grep.py:33-34`

#### `grep_components/` - Modular Grep Implementation
- **file_filter.py**: Fast `os.scandir` based globbing (MAX_GLOB=5000)
- **pattern_matcher.py**: Search with relevance scoring
- **result_formatter.py**: Multiple output modes (content/files/count/json)
- **search_result.py**: `SearchResult` and `SearchConfig` DTOs

#### `prompts/` - XML Tool Definitions
- Loaded via `xml_helper.py` with LRU caching
- Contains description, parameters schema, examples for each tool

### Key Dependencies

**Internal:**
- `tunacode.exceptions` (ToolExecutionError, FileOperationError)
- `tunacode.types` (ToolResult, FilePath, UILogger)
- `tunacode.constants` (READ_ONLY_TOOLS, MAX_FILE_SIZE, etc.)
- `tunacode.core.code_index.CodeIndex` (optional caching)

**External:**
- `pydantic_ai` - Tool execution framework
- `asyncio` - Async execution (8/11 tools)
- `defusedxml.ElementTree` - Safe XML parsing (9/11 tools)

### Complexity Assessment

**High Complexity (refactor candidates):**
- `glob.py` (587 lines, CC ~20)
- `grep.py` (552 lines, CC ~25)
- `bash.py` (362 lines, CC ~15)

**Moderate Complexity:**
- `list_dir.py` (321 lines, CC ~12)
- `run_command.py` (238 lines, CC ~8)

**Low Complexity:**
- `read_file.py`, `write_file.py`, `update_file.py`, `react.py`

## Key Patterns / Solutions Found

### 1. Template Method Pattern
`BaseTool.execute()` wraps `_execute()` with error handling, logging, cleanup

### 2. Strategy Pattern
- Text matching: ordered replacer list (text_match.py:266)
- Search: smart/ripgrep/python/hybrid selection (grep.py:198-208)

### 3. Composition Over Inheritance
`ParallelGrep` composes: FileFilter, PatternMatcher, ResultFormatter, RipgrepExecutor

### 4. Graceful Degradation
- Ripgrep → Python fallback
- XML loading → hardcoded defaults

### 5. Resource Management
Automatic cleanup via `finally` blocks and `register_resource()`

## Knowledge Gaps

1. **Why dual implementation?** Classes AND async functions - maintenance burden
2. **Why two command tools?** `BashTool` vs `RunCommandTool` overlap significantly
3. **MCP integration status**: References in docs but file doesn't exist
4. **Unused constants**: `WRITE_TOOLS`, `EXECUTE_TOOLS` defined but never imported

## Issues for Refactoring

### Critical
1. **Duplicate command execution tools** - `bash.py` and `run_command.py` have overlapping functionality with different security approaches. Consider consolidation.

2. **Inconsistent XML loading** - Most tools implement their own `_get_base_prompt()`/`_get_parameters_schema()`. Should leverage `xml_helper.py` consistently.

3. **Parameter naming inconsistency** - `filepath` vs `directory` vs `path` across tools

### Moderate
4. **Thread pool patterns vary** - `grep.py` creates own ThreadPoolExecutor, others use `asyncio.to_thread()`

5. **Duplicate tool categorization** - `schema_assembler.py:131` hardcodes safe tools list, duplicating `READ_ONLY_TOOLS` constant

6. **Coupling violation** - `json_utils.py` imports `READ_ONLY_TOOLS` (parsing utility importing app constants)

### Minor
7. **Missing type hints** in some tool wrapper functions
8. **Stale MCP references** in documentation

## Refactoring Recommendations

### Phase 1: Consolidation
- [ ] Merge `bash.py` and `run_command.py` into unified command execution tool
- [ ] Standardize parameter naming (`filepath` everywhere)
- [ ] Extract XML loading to base class, remove duplication

### Phase 2: Simplification
- [ ] Consider removing class implementations if async functions sufficient
- [ ] Centralize thread pool management in base class
- [ ] Remove unused constants (`WRITE_TOOLS`, `EXECUTE_TOOLS`)

### Phase 3: Decoupling
- [ ] Move `READ_ONLY_TOOLS` check out of `json_utils.py`
- [ ] Consolidate tool categorization (remove `schema_assembler.py` duplication)

## References

- `src/tunacode/tools/base.py` → Core abstractions
- `src/tunacode/tools/grep.py` → Most complex tool (example of composition)
- `src/tunacode/core/agents/agent_components/agent_config.py:340-353` → Tool registration
- `src/tunacode/constants.py:63-72` → Tool categorization constants
- `src/tunacode/core/tool_authorization.py:337` → Authorization logic
