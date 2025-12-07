# Research – CodeIndex File Analysis

**Date:** 2025-12-06
**Owner:** Claude Agent
**Phase:** Research

## Goal

Understand what `src/tunacode/indexing/code_index.py` is, its purpose, and map out its architecture and integration points.

---

## What Is This File?

**`src/tunacode/indexing/code_index.py`** is a **531-line singleton-based in-memory file indexer** that provides fast repository lookups without relying on grep searches that can timeout in large repositories.

### Core Purpose

> "This index provides efficient file discovery without relying on grep searches that can timeout in large repositories."

The file solves the **performance problem** of expensive filesystem traversal. Instead of scanning directories on every query, it pre-builds searchable data structures for:
- File paths by basename
- Python class definitions
- Python function definitions
- Import relationships
- Directory contents (cached with 5s TTL)

---

## Architecture Map

```
┌─────────────────────────────────────────────────────────────────────┐
│                         CodeIndex (Singleton)                        │
├─────────────────────────────────────────────────────────────────────┤
│  Class Constants                                                     │
│  ├── IGNORE_DIRS (35+ dirs: .git, node_modules, __pycache__, etc.) │
│  └── INDEXED_EXTENSIONS (40+ extensions: .py, .js, .ts, etc.)      │
├─────────────────────────────────────────────────────────────────────┤
│  Primary Indices                                                     │
│  ├── _basename_to_paths: dict[str, list[Path]]  ← filename lookup   │
│  ├── _all_files: set[Path]                      ← complete file set │
│  └── _path_to_imports: dict[Path, set[str]]     ← Python imports    │
├─────────────────────────────────────────────────────────────────────┤
│  Symbol Indices (Python-specific)                                    │
│  ├── _class_definitions: dict[str, list[Path]]                      │
│  └── _function_definitions: dict[str, list[Path]]                   │
├─────────────────────────────────────────────────────────────────────┤
│  Cache Layer                                                         │
│  ├── _dir_cache: dict[Path, list[Path]]                             │
│  ├── _cache_timestamps: dict[Path, float]                           │
│  └── _cache_ttl = 5.0 seconds                                       │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Public API

| Method | Line | Purpose | Used By |
|--------|------|---------|---------|
| `get_instance(root_dir)` | 136 | Singleton accessor | glob.py:121 |
| `reset_instance()` | 152 | Clear singleton (testing) | None |
| `build_index(force)` | 206 | Build/rebuild file index | glob.py:122 |
| `lookup(query, file_type)` | 356 | Multi-strategy file search | **UNUSED** |
| `get_all_files(file_type)` | 414 | Get all indexed files | glob.py:197 |
| `find_imports(module_name)` | 434 | Find files importing module | **UNUSED** |
| `refresh(path)` | 454 | Refresh index for path | **UNUSED** |
| `get_stats()` | 516 | Get index statistics | **UNUSED** |
| `get_directory_contents(path)` | 157 | Get cached dir contents | **UNUSED** |

**Key Finding:** Only 3 methods are actually used (`get_instance`, `build_index`, `get_all_files`).

---

## Data Flow

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  User Query  │────▶│  Glob Tool   │────▶│  CodeIndex   │
└──────────────┘     └──────────────┘     └──────────────┘
                            │                    │
                            │  1. get_instance() │
                            │◀───────────────────│
                            │                    │
                            │  2. build_index()  │
                            │───────────────────▶│
                            │                    │ (lazy, once)
                            │  3. get_all_files()│
                            │───────────────────▶│
                            │                    │
                            │  4. list[Path]     │
                            │◀───────────────────│
                            │                    │
                     ┌──────▼──────┐             │
                     │ Apply glob  │             │
                     │  patterns   │             │
                     └─────────────┘             │
```

---

## Integration Points

### Active Integration

**Glob Tool** (`src/tunacode/tools/glob.py`)
- **Line 10:** `from tunacode.indexing import CodeIndex`
- **Line 92:** Conditional activation (only for project root)
- **Line 121:** `index = CodeIndex.get_instance()`
- **Line 197:** `all_files = code_index.get_all_files()`

### Missing Integrations

| Tool | Current Behavior | Opportunity |
|------|-----------------|-------------|
| **Grep** | Uses `FileFilter.fast_glob()` with 3s timeout | Could use CodeIndex to eliminate timeout |
| **List_dir** | Uses `os.walk()` directly | Could benefit from cached directory contents |

---

## Code Review Issues (from user's review)

### Magic Numbers (CLAUDE.md violation)

| Line | Current | Should Be |
|------|---------|-----------|
| 131 | `self._cache_ttl = 5.0` | `CACHE_TTL_SECONDS = 5.0` |
| 297 | `10 * 1024 * 1024` | `MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024` |
| 288 | `f.read(2)` | `SHEBANG_LENGTH = 2` |

### Silent Exception Swallowing (CLAUDE.md violation)

```python
# Lines 291-292, 299-300
except Exception:
    pass  # Should at minimum log at debug level
```

### Nested Conditional with noqa (Lines 334-336)

```python
if len(parts) >= 2:  # noqa: SIM102
    if parts[0] == "import" or parts[0] == "from" and len(parts) >= 3:
```

**Issue:** Operator precedence confusion (`and` binds tighter than `or`). Should be:
```python
if parts[0] == "import" or (parts[0] == "from" and len(parts) >= 3):
```

### Low Cohesion Methods

| Method | Lines | Responsibilities | Recommendation |
|--------|-------|-----------------|----------------|
| `lookup()` | 356-412 | 6 distinct operations | Extract `_match_basename`, `_match_partial`, `_match_path`, `_match_symbol`, `_filter_by_type`, `_sort_by_relevance` |
| `_index_python_file()` | 319-354 | Parse imports, classes, functions | Extract `_extract_imports()`, `_extract_class_definitions()`, `_extract_function_definitions()` |

---

## Coupling Issues

### Singleton Pattern (Lines 135-155)

```python
@classmethod
def get_instance(cls, root_dir: str | None = None) -> "CodeIndex":
```

**Problems:**
- Creates global state (hard to test)
- `root_dir` only used on first call (confusing API)
- Tests must call `reset_instance()` to avoid pollution

### Direct Filesystem Access (Lines 255-273)

```python
entries = list(directory.iterdir())
```

**Problem:** Impossible to unit test without real filesystem or complex mocking.

### Duplicated Logic

Four separate implementations of directory filtering:
1. `CodeIndex.IGNORE_DIRS` (code_index.py:26-61)
2. `EXCLUDE_DIRS` (glob.py:14-30)
3. `EXCLUDE_DIRS` (grep_components/file_filter.py:13-25)
4. `IGNORE_PATTERNS` (list_dir.py:12-41)

---

## Historical Context

| Date | Commit | Change |
|------|--------|--------|
| Aug 12, 2025 | `4eacbd9` | Created as part of major performance optimizations |
| Later | `066074e` | Moved to `indexing/` module for better organization |

**Design Documentation:** `.claude/development/directory-caching-optimization.md` (196 lines)

**Performance Benchmarks:** 50-500x speedup for cached operations

---

## Test Coverage

**None.** No dedicated tests exist for `code_index.py`.

Per CLAUDE.md:
> "Currently we only have two tests: one that tests the tool decorators and one that tests the tool conformance."

---

## Refactoring Priority

### High Priority (CLAUDE.md Violations)

1. **Extract magic numbers to class constants**
   - `CACHE_TTL_SECONDS`, `MAX_FILE_SIZE_BYTES`, `SHEBANG_LENGTH`

2. **Fix silent exception handling**
   - Add `logger.debug()` calls in `_should_index_file()`

3. **Fix operator precedence in line 335**
   - Add explicit parentheses

### Medium Priority (Cohesion)

4. **Split `lookup()` method** into 6 focused helpers

5. **Split `_index_python_file()`** into 3 pure functions

### Low Priority (Coupling)

6. **Abstract filesystem access** for testability

7. **Consolidate IGNORE_DIRS** across tools

---

## Knowledge Gaps

- Why are `lookup()`, `find_imports()`, `refresh()`, `get_stats()` unused?
- Was there a plan to use these in other tools?
- Should unused methods be removed per CLAUDE.md ("delete dead code")?

---

## References

- `src/tunacode/indexing/code_index.py` - Main implementation
- `src/tunacode/indexing/__init__.py` - Module exports
- `src/tunacode/tools/glob.py` - Primary consumer
- `.claude/development/directory-caching-optimization.md` - Design documentation
- `memory-bank/research/2025-12-05_sparse_directories_cleanup_map.md` - Architecture review
