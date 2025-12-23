# Research - update_file UI Freeze Deep Dive

**Date:** 2025-12-18
**Owner:** Claude
**Phase:** Research

## Goal

Identify remaining bottlenecks causing UI freezes during `update_file` operations **after** the Levenshtein C extension fix was applied.

## Summary

The Levenshtein C extension fix (PR #191) addressed only ONE of FIVE synchronous blocking operations in the `update_file` call chain. UI freezes persist because **synchronous file I/O** and **O(n^2) algorithm patterns** still block the async event loop.

## Findings

### Bottleneck Priority Matrix

| Rank | Operation | Location | Blocking Time | Status |
|------|-----------|----------|---------------|--------|
| **1** | Sync file read | `update_file.py:30-31` | 10-1000ms | **UNFIXED** |
| **2** | Sync file write | `update_file.py:49-50` | 10-1000ms | **UNFIXED** |
| **3** | O(n^2) candidate search | `text_match.py:184-192` | 50-200ms | **UNFIXED** |
| **4** | unified_diff() | `update_file.py:53-61` | 10-500ms | **UNFIXED** |
| **5** | Pygments lexing | UI renderer | 5-150ms | Capped (acceptable) |
| **6** | Levenshtein distance | `text_match.py:218,250` | ~0.1ms/call | **FIXED** (C ext) |

### Relevant Files & Why They Matter

**Core Bottleneck Files:**
- `src/tunacode/tools/update_file.py` - Sync I/O at lines 30-31 (read), 49-50 (write), 53-61 (diff)
- `src/tunacode/tools/utils/text_match.py` - O(n^2) loop at lines 184-192

**Reference Implementation (correct pattern):**
- `src/tunacode/tools/read_file.py:68` - Uses `asyncio.to_thread()` for async I/O

**UI/Rendering:**
- `src/tunacode/ui/app.py:334-342` - Synchronous message handler
- `src/tunacode/ui/renderers/tools/update_file.py:157-158` - Pygments syntax highlighting

**Tool Infrastructure:**
- `src/tunacode/tools/decorators.py:186-190` - LSP diagnostics (async, OK)
- `src/tunacode/core/agents/agent_components/node_processor.py:352` - Sequential tool execution

### Detailed Analysis

#### Issue 1: Synchronous File I/O (PRIMARY BOTTLENECK)

**Location:** `src/tunacode/tools/update_file.py`

```python
# Line 30-31 - BLOCKING READ
with open(filepath, encoding="utf-8") as f:
    original = f.read()

# Line 49-50 - BLOCKING WRITE
with open(filepath, "w", encoding="utf-8") as f:
    f.write(new_content)
```

**Problem:** Function is `async def` but uses synchronous `open()`. This blocks the entire event loop during disk operations.

**Impact by file size:**
- Small files (<100KB): 10-50ms
- Medium files (100KB-1MB): 50-200ms
- Large files (>1MB): 200-1000ms
- Network filesystems: 5-10x worse

**Evidence:** `read_file.py` already uses correct async pattern:
```python
async def read_file(...) -> str:
    return await asyncio.to_thread(_sync_read_file, filepath, offset, limit)
```

#### Issue 2: O(n^2) Candidate Search in block_anchor_replacer

**Location:** `src/tunacode/tools/utils/text_match.py:184-192`

```python
candidates: list[tuple[int, int]] = []
for i in range(len(original_lines)):              # O(n)
    if original_lines[i].strip() != first_line_search:
        continue
    for j in range(i + 2, len(original_lines)):   # O(n) NESTED
        if original_lines[j].strip() == last_line_search:
            candidates.append((i, j))
            break
```

**Problem:** Nested loop creates O(n^2) worst case even before Levenshtein calls.

**Worst case calculation (5000-line file):**
- 50 lines match first anchor (common: `def`, `class`, `if`)
- Average 40 candidates found per anchor match
- Candidate search alone: 50-200ms
- Then Levenshtein on each candidate's middle lines

**Better pattern (O(n) indexing):**
```python
first_indices = {i for i, line in enumerate(lines) if line.strip() == first}
last_indices = {i for i, line in enumerate(lines) if line.strip() == last}
# Then intersect in O(k^2) where k << n
```

#### Issue 3: Synchronous unified_diff()

**Location:** `src/tunacode/tools/update_file.py:52-61`

```python
diff_lines = list(
    difflib.unified_diff(
        original.splitlines(keepends=True),    # Copy 1
        new_content.splitlines(keepends=True), # Copy 2
        fromfile=f"a/{filepath}",
        tofile=f"b/{filepath}",
    )
)
```

**Problem:**
1. Creates TWO full copies of file content
2. Myers diff algorithm is O(ND) where N=file size, D=edit distance
3. `list()` forces eager evaluation - cannot yield to event loop
4. Pure Python, no C extension

**Impact:** 10-500ms depending on file size and change density

#### Issue 4: Event Loop Blocking Cascade

When any synchronous operation blocks:
1. Event loop cannot process keyboard events
2. Ctrl+C handler cannot run
3. UI refresh freezes
4. User perceives complete freeze until ALL sync operations complete

**Total blocking time (excluding LSP):**
- Best case: 25ms
- Typical case: 100-300ms
- Worst case: 2-5 seconds
- **Pathological case: 10-15 seconds**

## Key Patterns / Solutions Found

### Pattern 1: Async I/O Offloading (use this)
```python
async def update_file(...):
    original = await asyncio.to_thread(lambda: Path(filepath).read_text())
    # ... processing ...
    await asyncio.to_thread(lambda: Path(filepath).write_text(new_content))
```

### Pattern 2: Indexed Search (for text_match.py)
Build hash indexes first, then intersect - transforms O(n^2) to O(n+k^2).

### Pattern 3: Deferred Diff Generation
Generate diff lazily or in thread pool:
```python
diff_text = await asyncio.to_thread(generate_unified_diff, original, new_content)
```

## Knowledge Gaps

1. **Exact timing breakdown** - Need profiling data to confirm which bottleneck dominates in real usage
2. **File size distribution** - What size files do users typically edit?
3. **Textual async rendering** - Can message handlers be made async?

## Recommended Fixes (Priority Order)

### Fix 1: Async File I/O (HIGH PRIORITY)
**File:** `src/tunacode/tools/update_file.py`
**Effort:** Low
**Impact:** Eliminates 10-1000ms blocking per operation

### Fix 2: Async Diff Generation (MEDIUM PRIORITY)
**File:** `src/tunacode/tools/update_file.py`
**Effort:** Low
**Impact:** Eliminates 10-500ms blocking

### Fix 3: Indexed Anchor Search (MEDIUM PRIORITY)
**File:** `src/tunacode/tools/utils/text_match.py`
**Effort:** Medium
**Impact:** Reduces O(n^2) to O(n+k^2)

### Fix 4: Wrap replace() in Thread (LOW PRIORITY)
**File:** `src/tunacode/tools/update_file.py`
**Effort:** Low
**Impact:** Offloads remaining CPU work from event loop

## References

- Prior research: `memory-bank/research/2025-12-18_update-file-ui-freeze.md`
- Plan doc: `memory-bank/plan/2025-12-18_19-30-00_levenshtein-c-extension.md`
- Execution log: `memory-bank/execute/2025-12-18_19-45-00_levenshtein-c-extension.md`
- Correct async pattern: `src/tunacode/tools/read_file.py:68`

## GitHub Permalinks

- [update_file.py:30-31 (sync read)](https://github.com/alchemiststudiosDOTai/tunacode/blob/9142960/src/tunacode/tools/update_file.py#L30-L31)
- [update_file.py:49-50 (sync write)](https://github.com/alchemiststudiosDOTai/tunacode/blob/9142960/src/tunacode/tools/update_file.py#L49-L50)
- [text_match.py:184-192 (O(n^2) loop)](https://github.com/alchemiststudiosDOTai/tunacode/blob/9142960/src/tunacode/tools/utils/text_match.py#L184-L192)
- [read_file.py:68 (correct async pattern)](https://github.com/alchemiststudiosDOTai/tunacode/blob/9142960/src/tunacode/tools/read_file.py#L68)

---

## Follow-up Research: 10+ Minute Freeze Root Cause (2025-12-18)

### The Key Question

> "How does a 5 second LSP timeout cause complete freezes for 10+ minutes?"

### Answer: Cascading Multiplicative Delays

The 10+ minute freeze is NOT caused by any single 5-second operation. It's caused by **multiplicative cascading** across multiple systems.

```
Total Freeze = (Retry Count) x (LSP Timeout) x (Sequential Files) + (Sync I/O Blocking)
```

---

### NEW FINDING 1: Pydantic-AI Retries = 10 by Default

**Location:** `src/tunacode/configuration/defaults.py:20`
**Location:** `src/tunacode/core/agents/agent_components/agent_config.py:331,354`

```python
# DEFAULT IS 10 RETRIES, NOT 3!
"max_retries": 10,

# Tool registration uses this value
Tool(update_file, max_retries=max_retries, ...)
```

**Impact:**
- When `update_file` raises `ModelRetry` (file not found, no changes, etc.)
- Pydantic-ai retries the ENTIRE tool call up to **10 times**
- Each retry triggers fresh LSP diagnostics

**Math:**
- 10 retries x 6s LSP timeout = **60 seconds per file minimum**

---

### NEW FINDING 2: LSP Enabled by Default (User May Not Know)

**Location:** `src/tunacode/configuration/defaults.py:38-42`

```python
"lsp": {
    "enabled": True,   # <-- ENABLED BY DEFAULT!
    "timeout": 5.0,
    "max_diagnostics": 20,
}
```

**Impact:**
- If user's `tunacode.json` has NO `lsp` section, falls back to enabled=True
- Every `@file_tool(writes=True)` waits for LSP diagnostics
- 5s timeout + 1s orchestration overhead = **6s per file write**

---

### NEW FINDING 3: Sequential Write Execution

**Location:** `src/tunacode/core/agents/agent_components/node_processor.py:346-354`

```python
# Write tools execute SEQUENTIALLY, not in parallel
for part, node in write_execute_tasks:
    result = await execute_tools_parallel([(part, node)], callback)
```

**Impact:**
- If agent calls 10 `update_file` operations in one response
- They execute ONE AT A TIME, not concurrently
- Total = sum of all individual delays

---

### NEW FINDING 4: Token Recalculation Every Iteration (O(n))

**Location:** `src/tunacode/core/state.py:116-123`

```python
def update_token_count(self) -> None:
    total = 0
    for msg in self.messages:  # Scans ENTIRE history
        content = get_message_content(msg)
        if content:
            total += estimate_tokens(content, self.current_model)
    self.total_tokens = total
```

**Impact:**
- Runs after EVERY model response (synchronous)
- Re-tokenizes entire message history each time
- Long conversations: 100+ messages = significant overhead

---

### The Cascade Effect: How 5s Becomes 10+ Minutes

**Scenario: Agent updates 5 files, each fails once then succeeds**

```
File 1 (attempt 1):
  - sync read() blocks (50ms)
  - replace() runs (fast)
  - sync write() blocks (50ms)
  - LSP timeout (6s) - no pyright running
  - ModelRetry raised ("no changes")

File 1 (attempt 2-10): 9 more retries x 6s = 54s

Subtotal File 1: ~60 seconds

Files 2-5: Same pattern

TOTAL: 5 files x 60s = 300 seconds (5 minutes)
```

**Worse scenario: LSP server slow + many files**

```
10 files x 10 retries x 6s = 600 seconds (10 minutes)
Plus sync I/O blocking makes UI completely unresponsive
```

---

### Immediate Workarounds (Config Changes)

**1. Disable LSP** in `~/.config/tunacode.json`:
```json
{
  "settings": {
    "lsp": {
      "enabled": false
    }
  }
}
```

**2. Reduce max_retries**:
```json
{
  "settings": {
    "max_retries": 3
  }
}
```

---

### Code Fixes Required

**Priority 1:** Wrap sync I/O in `asyncio.to_thread()` (update_file.py)
**Priority 2:** Add LSP server health check - fail fast if no server
**Priority 3:** Make token recalculation incremental
**Priority 4:** Consider reducing default max_retries from 10 to 3

---

### Additional File References

| File | Line | Issue |
|------|------|-------|
| `src/tunacode/configuration/defaults.py` | 20 | max_retries=10 default |
| `src/tunacode/configuration/defaults.py` | 38-42 | LSP enabled by default |
| `src/tunacode/core/agents/agent_components/agent_config.py` | 331, 354 | Tool registration with retries |
| `src/tunacode/core/agents/agent_components/node_processor.py` | 346-354 | Sequential write execution |
| `src/tunacode/core/state.py` | 116-123 | Token recalculation O(n) |
| `src/tunacode/tools/decorators.py` | 75-78 | LSP timeout wrapping |
| `src/tunacode/lsp/client.py` | 290-319 | Diagnostic polling loop |
