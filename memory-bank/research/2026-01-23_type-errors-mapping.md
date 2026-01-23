# Research - Type Errors Mapping (43 errors in 14 files)

**Date:** 2026-01-23
**Owner:** agent
**Phase:** Research

## Goal

Map all 43 type errors in `/src` and document proper fixes without using `Any`, `cast()`, or `type: ignore` hacks.

## Error Categories

| Category | Count | Complexity |
|----------|-------|------------|
| Missing type annotations | ~25 | Simple |
| Type mismatches | ~8 | Medium |
| Protocol/interface mismatches | ~10 | Complex |

---

## Category 1: Missing Type Annotations (22 functions)

### File: `src/tunacode/tools/__init__.py`
| Line | Function | Fix |
|------|----------|-----|
| 6 | `__getattr__(name)` | `-> types.ModuleType` (add `import types`) |

### File: `src/tunacode/utils/parsing/retry.py`
| Line | Function | Fix |
|------|----------|-----|
| 118 | `def _parse():` | `-> Any` |
| 150 | `async def _parse():` | `-> Any` |

### File: `src/tunacode/tools/utils/ripgrep.py`
| Line | Function | Fix |
|------|----------|-----|
| 312 | `def __init__(self):` | `-> None` |
| 317 | `def record_search(...)` | `-> None` |

### File: `src/tunacode/utils/system/gitignore.py`
| Line | Function | Fix |
|------|----------|-----|
| 16 | `def _load_gitignore_patterns(filepath=...)` | `(filepath: str = ".gitignore") -> set[str] \| None` |
| 34 | `def list_cwd(max_depth=...)` | `(max_depth: int = 3) -> list[str]` |

### File: `src/tunacode/configuration/settings.py`
| Line | Function | Fix |
|------|----------|-----|
| 15 | `def __init__(self):` (PathConfig) | `-> None` |
| 21 | `def __init__(self):` (ApplicationSettings) | `-> None` |

### File: `src/tunacode/utils/system/paths.py`
| Line | Function | Fix |
|------|----------|-----|
| 17 | `def get_tunacode_home():` | `-> Path` |
| 30 | `def get_session_dir(state_manager):` | `-> Path` |
| 45 | `def get_cwd():` | `-> str` |
| 85 | `def get_device_id():` | `-> str` |
| 111 | `def cleanup_session(state_manager):` | `-> bool` |
| 161 | `def check_for_updates():` | `-> tuple[bool, str]` |

### File: `src/tunacode/tools/grep.py`
| Line | Function | Fix |
|------|----------|-----|
| 40 | `def __init__(self):` | `-> None` |
| 307 | `async def search_with_monitoring(file_path):` | `-> list[SearchResult]` |
| 324 | `async def check_deadline():` | `-> None` |
| 413 | `def search_file_sync():` | `-> list[SearchResult]` |

### File: `src/tunacode/tools/glob.py`
| Line | Function | Fix |
|------|----------|-----|
| 239 | `def search_sync():` | `-> list[str]` |
| 321 | `def sort_sync():` | `-> list[str]` |

### File: `src/tunacode/tools/bash.py`
| Line | Function | Fix |
|------|----------|-----|
| 182 | `async def _cleanup_process(process)` | Add param type: `process: asyncio.subprocess.Process` |

### File: `src/tunacode/core/state.py`
| Line | Function | Fix |
|------|----------|-----|
| 138 | `def __init__(self):` | `-> None` |

---

## Category 2: Type Mismatch Errors (5 issues)

### Error 2.1: MatchLike vs SimpleMatch
**File:** `src/tunacode/tools/grep_components/pattern_matcher.py:71`
**Problem:** `matches: list[MatchLike]` assigned from `regex_pattern.finditer()`, then `SimpleMatch` appended
**Fix:** Initialize as empty list, let type inference handle both branches:
```python
matches: list[MatchLike] = []
if regex_pattern:
    matches.extend(regex_pattern.finditer(line))
else:
    # SimpleMatch branch...
```

### Error 2.2: None Handling for IgnoreCacheEntry
**File:** `src/tunacode/tools/ignore.py:162, 164`
**Problem:** `has_cache_entry` boolean doesn't enable type narrowing
**Fix:** Use direct `is not None` check:
```python
cache_entry = IGNORE_MANAGER_CACHE.get(resolved_root)
if cache_entry is not None and cache_entry.gitignore_mtime == gitignore_mtime:
    return cache_entry.manager
```

### Error 2.3: Literal Type Issues
**File:** `src/tunacode/tools/authorization/notifier.py:35, 38`
**Problem:** Constants typed as `str`, pydantic-ai expects `Literal`
**Fix:** Change lines 7-8:
```python
from typing import Literal
MODEL_REQUEST_KIND: Literal["request"] = "request"
USER_PROMPT_PART_KIND: Literal["user-prompt"] = "user-prompt"
```

### Error 2.4: Coroutine vs Task
**File:** `src/tunacode/tools/grep.py:330, 331`
**Problem:** Coroutines don't have `.done()` or `.cancel()` methods
**Fix:** Wrap with `asyncio.create_task()` at lines 318-321:
```python
search_tasks = [
    asyncio.create_task(search_with_monitoring(file_path))
    for file_path in candidates
]
```

### Error 2.5: CodeIndex | None
**File:** `src/tunacode/tools/glob.py:74`
**Problem:** `has_code_index` boolean doesn't enable type narrowing
**Fix:** Use direct `is not None` check at lines 70-76:
```python
if code_index is not None and not include_hidden and recursive:
    matches = await _glob_with_index(code_index, ...)
```

---

## Category 3: Protocol/Interface Mismatches (4 issues in app.py)

### Error 3.1: ShellRunnerHost.notify() Signature
**File:** `src/tunacode/ui/app.py:112`
**Protocol:** `src/tunacode/ui/shell_runner.py:69`
**Problem:** Protocol has positional `severity`, Textual requires keyword-only
**Fix:** Change protocol:
```python
class ShellRunnerHost(Protocol):
    def notify(self, message: str, *, severity: str = "information") -> None: ...
```

### Error 3.2: push_screen Callback Type
**File:** `src/tunacode/ui/app.py:160`
**Problem:** `_on_setup_complete(completed: bool)` but screens can dismiss with `None`
**Fix:** Change line 175:
```python
def _on_setup_complete(self, completed: bool | None) -> None:
```

### Error 3.3: run_worker Type
**File:** `src/tunacode/ui/app.py:191`
**Problem:** Passing callable instead of coroutine
**Fix:** Call the method:
```python
self.run_worker(self._request_worker(), exclusive=False)
```

### Error 3.4: AppForCallbacks Protocol Mismatch
**File:** `src/tunacode/ui/app.py:222, 231, 232`
**Protocol:** `src/tunacode/ui/repl_support.py:125-128`
**Problem:** Protocol doesn't match Textual's actual signatures
**Fix:** Update protocol:
```python
from textual.message import Message
from tunacode.ui.widgets import StatusBar

class AppForCallbacks(ConfirmationRequester, Protocol):
    status_bar: StatusBar  # Use concrete type
    def post_message(self, message: Message) -> bool: ...  # Match Textual
```

---

## Implementation Order

1. **Simple annotations first** (Category 1) - Low risk, high count reduction
2. **Type mismatches** (Category 2) - Medium complexity, surgical fixes
3. **Protocol fixes** (Category 3) - Highest risk, affects interfaces

## Key Patterns Discovered

1. **Type Narrowing**: Mypy doesn't track boolean variables. Use direct `is not None` checks.
2. **Literal Types**: External libraries use `Literal` for string constants. Match them.
3. **Async Tasks**: Coroutines != Tasks. Use `asyncio.create_task()` for `.done()/.cancel()`.
4. **Protocol Design**: Protocols should match framework signatures, not idealized interfaces.

## References

- mypy output: 43 errors in 14 files
- Files analyzed: 14 source files
- Sub-agents used: codebase-analyzer (3 parallel)
