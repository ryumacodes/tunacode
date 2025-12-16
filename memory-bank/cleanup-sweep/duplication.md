# Duplication and Pattern Detector Report

**Generated**: 2025-12-14
**Scope**: /home/tuna/tunacode/src/tunacode

---

## Executive Summary

This report identifies duplicated logic, deprecated patterns, and multiple implementations of the same utility across the tunacode codebase. **All findings below suggest DELETION of duplicates, not creation of new abstractions.**

---

## 1. Duplicated `_truncate_line` Function

**Issue**: The same `_truncate_line` function is copy-pasted across 5 tool renderer files.

**Evidence**:
- `/home/tuna/tunacode/src/tunacode/ui/renderers/tools/bash.py:91`
- `/home/tuna/tunacode/src/tunacode/ui/renderers/tools/grep.py:114`
- `/home/tuna/tunacode/src/tunacode/ui/renderers/tools/list_dir.py:88`
- `/home/tuna/tunacode/src/tunacode/ui/renderers/tools/read_file.py:121`
- `/home/tuna/tunacode/src/tunacode/ui/renderers/tools/web_fetch.py:69`

**Implementation** (identical across all files):
```python
def _truncate_line(line: str) -> str:
    """Truncate a single line if too wide."""
    if len(line) > MAX_PANEL_LINE_WIDTH:
        return line[: MAX_PANEL_LINE_WIDTH - 3] + "..."
    return line
```

**Suggested Action**:
- **DELETE** 4 instances (keep one as canonical in a shared module)
- Keep the implementation in one central location
- Remove from: bash.py, grep.py, list_dir.py, read_file.py (DELETE 4 duplicates)

---

## 2. Duplicated `BOX_HORIZONTAL` and `SEPARATOR_WIDTH` Constants

**Issue**: These rendering constants are duplicated across 7 tool renderer files.

**Evidence**:
- `/home/tuna/tunacode/src/tunacode/ui/renderers/tools/bash.py:17-18`
- `/home/tuna/tunacode/src/tunacode/ui/renderers/tools/grep.py:17-18`
- `/home/tuna/tunacode/src/tunacode/ui/renderers/tools/glob.py:18-19`
- `/home/tuna/tunacode/src/tunacode/ui/renderers/tools/list_dir.py:18-19`
- `/home/tuna/tunacode/src/tunacode/ui/renderers/tools/read_file.py:18-19`
- `/home/tuna/tunacode/src/tunacode/ui/renderers/tools/update_file.py:19-20`
- `/home/tuna/tunacode/src/tunacode/ui/renderers/tools/web_fetch.py:17-18`

**Implementation**:
```python
BOX_HORIZONTAL = "\u2500"  # or "─" in list_dir.py
SEPARATOR_WIDTH = 52
```

**Note**: list_dir.py uses "─" directly instead of "\u2500" (though they're the same character).

**Suggested Action**:
- **DELETE** 6 duplicate constant definitions
- Keep these in `/home/tuna/tunacode/src/tunacode/constants.py` or a shared renderer module
- Remove from all tool renderer files except the canonical location

---

## 3. Duplicated `EXCLUDE_DIRS` Pattern

**Issue**: Similar directory exclusion lists defined in multiple places.

**Evidence**:
- `/home/tuna/tunacode/src/tunacode/tools/grep_components/file_filter.py:13-25` (EXCLUDE_DIRS)
- `/home/tuna/tunacode/src/tunacode/tools/glob.py:14-30` (EXCLUDE_DIRS)
- `/home/tuna/tunacode/src/tunacode/utils/ui/file_filter.py:10-28` (DEFAULT_IGNORES)

**Comparison**:

**grep_components/file_filter.py** (set):
```python
EXCLUDE_DIRS = {
    "node_modules", ".git", "__pycache__", ".venv", "venv",
    "dist", "build", ".pytest_cache", ".mypy_cache", ".tox", "target"
}
```

**tools/glob.py** (set, extends grep's version):
```python
EXCLUDE_DIRS = {
    "node_modules", ".git", "__pycache__", ".venv", "venv",
    "dist", "build", ".pytest_cache", ".mypy_cache", ".tox",
    "target", ".next", ".nuxt", "coverage", ".coverage"
}
```

**utils/ui/file_filter.py** (list, more comprehensive):
```python
DEFAULT_IGNORES = [
    ".git/", ".venv/", "venv/", "env/", "node_modules/",
    "__pycache__/", "*.pyc", "*.pyo", "*.egg-info/",
    ".DS_Store", "Thumbs.db", ".idea/", ".vscode/",
    "build/", "dist/", "target/", ".env",
]
```

**Suggested Action**:
- **DELETE** the smaller, less comprehensive versions
- Keep the most comprehensive one in `/home/tuna/tunacode/src/tunacode/utils/ui/file_filter.py`
- **DELETE** EXCLUDE_DIRS from grep_components/file_filter.py and tools/glob.py
- Import from the canonical location instead

---

## 4. Two `FileFilter` Classes with Different Purposes

**Issue**: Two classes named `FileFilter` with completely different implementations and purposes.

**Evidence**:
- `/home/tuna/tunacode/src/tunacode/utils/ui/file_filter.py:31-136` - Gitignore-aware autocomplete filter
- `/home/tuna/tunacode/src/tunacode/tools/grep_components/file_filter.py:28-94` - Fast glob for grep tool

**Analysis**:
While both are named `FileFilter`, they serve different purposes:
1. **utils/ui/file_filter.py**: Used for UI autocomplete, gitignore-aware, depth-limited traversal
2. **grep_components/file_filter.py**: Used for grep tool, fast glob with pattern matching

**Suggested Action**:
- **RENAME** one of these classes to be more specific
- Rename `tools/grep_components/file_filter.py::FileFilter` to `GrepFileFilter` or `FastGlobber`
- Keep `utils/ui/file_filter.py::FileFilter` as is (it's gitignore-aware and more general-purpose)
- This is not a duplication but a naming collision that creates confusion

---

## 5. Duplicated Unified Diff Generation

**Issue**: Identical unified diff generation logic in two files.

**Evidence**:
- `/home/tuna/tunacode/src/tunacode/tools/update_file.py:53-61`
- `/home/tuna/tunacode/src/tunacode/tools/authorization/requests.py:56-63`

**Implementation**:
Both files use:
```python
diff_lines = list(
    difflib.unified_diff(
        original.splitlines(keepends=True),
        new_content.splitlines(keepends=True),
        fromfile=f"a/{filepath}",
        tofile=f"b/{filepath}",
    )
)
diff_text = "".join(diff_lines)
```

**Suggested Action**:
- **DELETE** one copy of this diff generation logic
- Extract to a shared utility in `/home/tuna/tunacode/src/tunacode/tools/utils/text_match.py`
- Keep the implementation there, remove from both update_file.py and authorization/requests.py
- Both files already import from text_match, so this is a natural location

---

## 6. Duplicated `parse_result` Pattern

**Issue**: All 7 tool renderers have a `parse_result` function with nearly identical signature and structure.

**Evidence**:
- `/home/tuna/tunacode/src/tunacode/ui/renderers/tools/bash.py:33`
- `/home/tuna/tunacode/src/tunacode/ui/renderers/tools/glob.py:36`
- `/home/tuna/tunacode/src/tunacode/ui/renderers/tools/grep.py:36`
- `/home/tuna/tunacode/src/tunacode/ui/renderers/tools/list_dir.py:36`
- `/home/tuna/tunacode/src/tunacode/ui/renderers/tools/read_file.py:35`
- `/home/tuna/tunacode/src/tunacode/ui/renderers/tools/update_file.py:36`
- `/home/tuna/tunacode/src/tunacode/ui/renderers/tools/web_fetch.py:33`

**Signature**:
```python
def parse_result(args: dict[str, Any] | None, result: str) -> ToolData | None:
```

**Analysis**:
While the parsing logic differs per tool, the pattern and structure is identical. This suggests a protocol/interface pattern that could be formalized.

**Suggested Action**:
- **NO DELETION** - This is actually a good pattern (polymorphism via function naming)
- The duplication is intentional and follows a consistent interface
- Consider documenting this as a protocol in `/home/tuna/tunacode/.claude/patterns/`

---

## 7. Multiple Model String Parsing Implementations

**Issue**: Two separate implementations of model string parsing.

**Evidence**:
- `/home/tuna/tunacode/src/tunacode/configuration/models.py:14-32` - `parse_model_string()`
- `/home/tuna/tunacode/src/tunacode/core/agents/agent_components/agent_config.py:272` - inline `split(":")`

**Implementation**:

**configuration/models.py** (robust):
```python
def parse_model_string(model_string: str) -> tuple[str, str]:
    """Parse 'provider:model' format."""
    parts = model_string.split(":", 1)
    if len(parts) != 2:
        raise ValueError(...)
    return parts[0], parts[1]
```

**agent_components/agent_config.py** (inline):
```python
provider_name, model_name = model_string.split(":", 1)
```

**Suggested Action**:
- **DELETE** the inline split in agent_config.py:272
- Import and use `parse_model_string` from configuration/models.py instead
- This avoids potential errors if the model string format is invalid

---

## 8. Duplicated `parse_patterns` Logic

**Issue**: Pattern parsing from comma-separated strings.

**Evidence**:
- `/home/tuna/tunacode/src/tunacode/tools/grep_components/file_filter.py:91-93`

**Implementation**:
```python
@staticmethod
def parse_patterns(patterns: str) -> list[str]:
    """Parse comma-separated file patterns."""
    return [p.strip() for p in patterns.split(",") if p.strip()]
```

**Analysis**:
This is a simple utility that's only used in one place currently. However, the pattern `[p.strip() for p in x.split(",") if p.strip()]` appears throughout the codebase for similar parsing tasks.

**Suggested Action**:
- **NO ACTION** - Single use case, not worth creating a shared utility
- Document this pattern in `/home/tuna/tunacode/.claude/patterns/parsing_patterns.md`

---

## 9. TODO/FIXME Comments

**Issue**: Outstanding TODO comments that may indicate incomplete work.

**Evidence**:
- `/home/tuna/tunacode/src/tunacode/prompts/sections/examples.xml:119` - `# TODO: Implement authentication`

**Analysis**:
Only 1 TODO found, and it's in an example XML file (not actual code).

**Suggested Action**:
- **NO ACTION** - This is example code in documentation, not actual code debt

---

## 10. Dead Code: Empty Exception Handlers

**Issue**: Empty pass statements in exception handlers that could be removed.

**Evidence**:
- `/home/tuna/tunacode/src/tunacode/utils/parsing/json_utils.py:74-79`

**Implementation**:
```python
try:
    parsed = json.loads(potential_json)
    if isinstance(parsed, dict):
        objects.append(parsed)
    else:
        pass  # Dead code
except json.JSONDecodeError:
    if strict_mode:
        pass  # Dead code
    else:
        pass  # Dead code
    continue
```

**Suggested Action**:
- **DELETE** the unnecessary else branches with pass statements
- Simplify to:
```python
try:
    parsed = json.loads(potential_json)
    if isinstance(parsed, dict):
        objects.append(parsed)
except json.JSONDecodeError:
    continue
```

---

## 11. Deprecated Pattern: Callback-Heavy Architecture

**Issue**: Heavy use of callbacks throughout the agent system instead of modern async patterns.

**Evidence**:
- `/home/tuna/tunacode/src/tunacode/types.py:59-60, 90-91, 134`
- `/home/tuna/tunacode/src/tunacode/core/agents/main.py:278-289`
- Multiple callback parameters: `tool_callback`, `streaming_callback`, `tool_result_callback`, `tool_start_callback`

**Analysis**:
The codebase uses a callback-based architecture with multiple callback types:
- `ToolCallback`
- `ToolStartCallback`
- `UICallback`
- `UIInputCallback`
- `ProcessRequestCallback`

While this works, it's a pre-async pattern. Modern Python async would use async generators or event streams.

**Suggested Action**:
- **NO DELETION** - This is a large architectural change
- Document as "legacy pattern to modernize" in `/home/tuna/tunacode/.claude/delta/`
- Consider migrating to async generators in a future refactor
- Not a quick fix suitable for cleanup sweep

---

## 12. Unused Constants in Exception Classes

**Issue**: Multiple pass statements after raising exceptions.

**Evidence**:
- `/home/tuna/tunacode/src/tunacode/utils/parsing/json_utils.py:111`

**Implementation**:
```python
if tool_name and tool_name in READ_ONLY_TOOLS:
    return True

# For write/execute tools, multiple objects are potentially dangerous
if tool_name:
    pass  # Unnecessary
    raise ConcatenatedJSONError(...)
```

**Suggested Action**:
- **DELETE** the `pass` statement on line 111
- It serves no purpose before a raise statement

---

## Summary Table

| # | Issue | Files Affected | Suggested Deletion | Priority |
|---|-------|---------------|-------------------|----------|
| 1 | `_truncate_line` duplication | 5 renderer files | Delete 4 copies | HIGH |
| 2 | `BOX_HORIZONTAL` constants | 7 renderer files | Delete 6 copies | HIGH |
| 3 | `EXCLUDE_DIRS` duplication | 3 files | Delete 2 copies | MEDIUM |
| 4 | `FileFilter` naming collision | 2 files | Rename (not delete) | LOW |
| 5 | Unified diff generation | 2 files | Delete 1 copy | MEDIUM |
| 6 | `parse_result` pattern | 7 files | No action (intentional) | N/A |
| 7 | Model string parsing | 2 implementations | Delete inline version | MEDIUM |
| 8 | `parse_patterns` | 1 file | No action | N/A |
| 9 | TODO comments | 1 file (example) | No action | N/A |
| 10 | Empty exception handlers | 1 file | Delete pass statements | LOW |
| 11 | Callback architecture | Multiple files | Document, don't delete | N/A |
| 12 | Unnecessary pass | 1 file | Delete 1 line | LOW |

---

## Recommended Deletion Order

1. **High Priority** (Same-day cleanup):
   - Delete 4 duplicates of `_truncate_line` (keep one)
   - Delete 6 duplicates of `BOX_HORIZONTAL` and `SEPARATOR_WIDTH`

2. **Medium Priority** (This week):
   - Delete 2 duplicates of `EXCLUDE_DIRS` (keep ui/file_filter.py version)
   - Delete duplicate diff generation (extract to text_match.py)
   - Delete inline model string parsing (use parse_model_string)

3. **Low Priority** (When convenient):
   - Delete unnecessary pass statements
   - Rename FileFilter classes to avoid collision

---

## Files Requiring Git Blame Analysis

To check age of code patterns (not included in this analysis):
- Use `git blame` on the files listed in findings #1, #2, #3
- Determine which version is oldest/most maintained
- Keep the most battle-tested version

---

**End of Report**
