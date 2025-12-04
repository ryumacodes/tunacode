# Research – Tools Test Suite Design
**Date:** 2025-12-04
**Owner:** claude
**Phase:** Research

## Goal
Understand the tools architecture to design a minimal, solid test suite with two tests:
1. Base harness test (decorator behavior)
2. Pattern conformance test (all tools follow the pattern)

## Findings

### Core Architecture

**Decorator System (`decorators.py`)**
- `@base_tool` - Wraps async tools with:
  - Logging via `logger.info(f"{func.__name__}({args}, {kwargs})")`
  - Error handling: passes through `ModelRetry`, `ToolExecutionError`, `FileOperationError`
  - Wraps other exceptions in `ToolExecutionError`
  - Auto-loads XML prompts via `load_prompt_from_xml(func.__name__)`

- `@file_tool` - Extends `@base_tool` with file-specific handling:
  - `FileNotFoundError` → `ModelRetry` (allows LLM retry)
  - `PermissionError` → `FileOperationError`
  - `UnicodeDecodeError` → `FileOperationError`
  - `IOError/OSError` → `FileOperationError`

### Tool Categories

| Tool | Decorator | First Param | Returns |
|------|-----------|-------------|---------|
| `read_file` | `@file_tool` | `filepath: str` | `str` |
| `write_file` | `@file_tool` | `filepath: str` | `str` |
| `update_file` | `@file_tool` | `filepath: str` | `str` |
| `bash` | `@base_tool` | `command: str` | `str` |
| `glob` | `@base_tool` | `pattern: str` | `str` |
| `grep` | `@base_tool` | `pattern: str` | `str \| List[str]` |
| `list_dir` | `@base_tool` | `directory: str` | `str` |
| `react` | factory func | N/A | `str` |

### Pattern Requirements for Valid Tools

1. **Async function** - All tools must be `async def`
2. **Decorated** - Must use `@base_tool` or `@file_tool`
3. **Docstring** - Must have docstring (or XML prompt loads into `__doc__`)
4. **Return type** - Must return `str` or `Union[str, List[str]]`
5. **Error handling** - Use `ModelRetry` for recoverable errors, exceptions for fatal

### XML Prompt System (`xml_helper.py`)
- Prompts in `tools/prompts/{tool_name}_prompt.xml`
- Structure: `<tool><description>...</description><parameters>...</parameters></tool>`
- Auto-loaded and assigned to `wrapper.__doc__` by `@base_tool`

### Exception Hierarchy
```
TunaCodeError (base)
├── ToolExecutionError (tool failures)
│   └── TooBroadPatternError (grep timeout)
├── FileOperationError (file ops)
└── ModelRetry (pydantic-ai, recoverable)
```

## Key Patterns / Solutions Found

1. **Decorator Composition**: `@file_tool` wraps inner function then calls `base_tool(wrapper)`
2. **XML Prompt Override**: Decorators check for XML prompts and override `__doc__`
3. **Error Escalation**: File errors → ModelRetry (recoverable) or FileOperationError (fatal)
4. **Async Threading**: Heavy I/O uses `asyncio.to_thread()` or `run_in_executor()`

## Test Design

### Test 1: Base Harness (`test_tool_decorators.py`)
Validates decorator behavior:
- `@base_tool` wraps function correctly
- Logging occurs on invocation
- `ModelRetry` passes through unchanged
- `ToolExecutionError` passes through unchanged
- Other exceptions wrapped in `ToolExecutionError`
- XML prompt loading works

### Test 2: Pattern Conformance (`test_tool_conformance.py`)
Validates all tools follow the pattern:
- All exported tools are async callables
- All use appropriate decorator (`@base_tool` or `@file_tool`)
- All have docstrings (from XML or inline)
- Return types are valid (`str` or `Union[str, List]`)
- File tools have `filepath` as first param

## References
- `src/tunacode/tools/decorators.py` → decorator implementation
- `src/tunacode/tools/xml_helper.py` → XML prompt loading
- `src/tunacode/exceptions.py` → exception hierarchy
- `src/tunacode/tools/prompts/*.xml` → tool prompts
