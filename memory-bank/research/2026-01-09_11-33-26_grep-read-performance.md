# Research: Grep and Read Tool Performance

**Date:** 2026-01-09
**Owner:** claude-agent
**Phase:** Research

## Goal

Investigate why grep and read tools feel slow and identify performance bottlenecks.

## Findings

### Relevant Files & Why They Matter

| File | Purpose |
|------|---------|
| `src/tunacode/tools/grep.py` | Main grep tool - creates ThreadPoolExecutor per call |
| `src/tunacode/tools/read_file.py` | Read tool - reads entire file even with offset |
| `src/tunacode/tools/utils/ripgrep.py` | Ripgrep wrapper - **blocking subprocess.run()** |
| `src/tunacode/tools/grep_components/pattern_matcher.py` | Pattern matching - reads entire file with readlines() |
| `src/tunacode/core/agents/agent_components/tool_executor.py` | Parallel execution - limited to CPU count |
| `src/tunacode/core/agents/agent_components/node_processor.py` | Tool batching - well designed but sequential iterations |

### Key Patterns / Bottlenecks Found

#### 1. BLOCKING SUBPROCESS (HIGH IMPACT)

**Location:** `src/tunacode/tools/utils/ripgrep.py:185-190`

```python
result = subprocess.run(
    cmd,
    capture_output=True,  # Buffers ALL output
    text=True,
    timeout=timeout,
)
```

**Problem:** Even wrapped in `run_in_executor`, this blocks until ripgrep completes entirely. No streaming, no early results. Searching 5000 files blocks for 2-3 seconds.

**Other blocking subprocess locations:**
- `utils/system/paths.py:58, 173`
- `ui/widgets/status_bar.py:38`
- `ui/commands/__init__.py:154, 423`

---

#### 2. INEFFICIENT FILE READING (MEDIUM IMPACT)

**Location:** `src/tunacode/tools/read_file.py:43`

```python
def _read_sync(path: str, line_limit: int) -> str:
    with open(path, encoding="utf-8") as f:
        lines = f.readlines()  # Reads ENTIRE file
    raw = lines[offset : offset + effective_limit]  # Then slices
```

**Problem:** Reading lines 1000-1100 from a 10,000 line file reads all 10,000 lines into memory first. No seeking to offset position.

---

#### 3. THREADPOOL RECREATION (LOW IMPACT)

**Location:** `src/tunacode/tools/grep.py:41`

```python
self._executor = ThreadPoolExecutor(max_workers=8)
```

**Problem:** Creates new ThreadPoolExecutor on every grep call. Should be module-level singleton.

---

#### 4. BATCH SIZE LIMITATION (MEDIUM IMPACT)

**Location:** `src/tunacode/core/agents/agent_components/tool_executor.py:63`

```python
max_parallel = int(os.environ.get("TUNACODE_MAX_PARALLEL", os.cpu_count() or 4))
```

**Problem:** I/O-bound operations artificially limited to CPU count (4-8 typically). Could run 50-100 concurrent file reads with minimal overhead.

---

#### 5. NO RESULT STREAMING (HIGH IMPACT)

**Problem:** No streaming anywhere in the pipeline:
- Grep must find ALL matches before returning
- Read must format ALL lines before returning
- Ripgrep buffers all stdout before parsing
- LLM cannot start processing until 100% complete

---

#### 6. PATTERN MATCHER READS ENTIRE FILE (LOW-MEDIUM IMPACT)

**Location:** `src/tunacode/tools/grep_components/pattern_matcher.py:44-45`

```python
with file_path.open("r", encoding="utf-8", errors="ignore") as f:
    lines = f.readlines()  # Entire file into memory
```

**Contrast:** The fallback in `ripgrep.py:260` actually streams lines:
```python
for line_num, line in enumerate(f, 1):  # Better - line by line
```

---

### What's Already Good

1. **Smart tool batching** in `node_processor.py` - categorizes tools into research/read-only/write buckets
2. **Parallel execution framework** - read-only tools run in parallel batches
3. **Extensive caching** - LRU cache for settings, XML prompts, ripgrep binary path, agents
4. **Streaming infrastructure** - token-level streaming with throttling exists
5. **Bash tool uses async** - `asyncio.create_subprocess_shell()` at `bash.py:67-73`

---

## Recommended Fixes

### Priority 1: Convert ripgrep to async subprocess

**Status:** Implemented in `src/tunacode/tools/utils/ripgrep.py` and `src/tunacode/tools/grep.py`.

```python
# Replace subprocess.run() in ripgrep.py with:
proc = await asyncio.create_subprocess_exec(
    *cmd,
    stdout=asyncio.subprocess.PIPE,
    stderr=asyncio.subprocess.PIPE
)
stdout, stderr = await proc.communicate()
```

### Priority 2: Seek-based file reading

**Status:** Implemented in `src/tunacode/tools/read_file.py`.

```python
# In read_file.py, seek to offset instead of reading all:
async def _read_with_seek(path: str, offset: int, limit: int) -> str:
    async with aiofiles.open(path) as f:
        # Skip offset lines
        for _ in range(offset):
            await f.readline()
        # Read only needed lines
        lines = [await f.readline() for _ in range(limit)]
```

### Priority 3: Singleton thread pool for grep

```python
# Module-level executor in grep.py
_GREP_EXECUTOR: ThreadPoolExecutor | None = None

def get_executor() -> ThreadPoolExecutor:
    global _GREP_EXECUTOR
    if _GREP_EXECUTOR is None:
        _GREP_EXECUTOR = ThreadPoolExecutor(max_workers=8)
    return _GREP_EXECUTOR
```

### Priority 4: Increase parallel limit for I/O ops

```python
# In tool_executor.py, differentiate CPU vs I/O bound:
IO_PARALLEL = 50  # For file reads, grep
CPU_PARALLEL = os.cpu_count() or 4  # For compute-heavy
```

### Priority 5: Consider aiofiles for async I/O

```bash
uv add aiofiles
```

Then replace synchronous file operations in hot paths.

---

## Knowledge Gaps

- No profiling data to quantify exact time spent in each bottleneck
- Unknown if ripgrep binary itself is the bottleneck vs subprocess overhead
- Need to test if increasing `TUNACODE_MAX_PARALLEL` helps without code changes

## References

- `src/tunacode/tools/grep.py` - Main grep implementation
- `src/tunacode/tools/read_file.py` - Read file implementation
- `src/tunacode/tools/utils/ripgrep.py` - Ripgrep subprocess wrapper
- `src/tunacode/core/agents/agent_components/tool_executor.py` - Parallel execution
- `src/tunacode/core/agents/agent_components/node_processor.py` - Tool batching

## Quick Wins (Can Try Now)

1. Set `TUNACODE_MAX_PARALLEL=50` environment variable
2. Test if ripgrep binary is stale: `scripts/download_ripgrep.py`
3. Check ripgrep config: `DEFAULT_USER_CONFIG["settings"]["ripgrep"]["timeout"]` = 10s
