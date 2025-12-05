# Research - @ Search Depth Limitation in Large Projects

**Date:** 2025-12-05
**Owner:** agent
**Phase:** Research

## Goal

Investigate why the `@` file autocomplete search does not go deep enough for large projects and identify the root cause and potential solutions.

## Findings

### Core Implementation Files

| File | Purpose |
|------|---------|
| `src/tunacode/ui/widgets/file_autocomplete.py` | Main FileAutoComplete widget (47 lines) |
| `src/tunacode/utils/ui/file_filter.py` | FileFilter class with path completion (80 lines) |
| `src/tunacode/ui/app.py:99` | Integration point in TextualReplApp |

### Root Cause: Two Critical Limitations

**1. Hardcoded 20-File Result Limit**

Location: `src/tunacode/utils/ui/file_filter.py:49`
```python
def complete(self, prefix: str = "", limit: int = 20) -> list[str]:
```

**2. Zero Recursion Depth - Single Directory Only**

Location: `src/tunacode/utils/ui/file_filter.py:67-78`
```python
for entry in sorted(search_path.iterdir()):  # <-- Only immediate directory
    if self.is_ignored(entry):
        continue
    if name_prefix and not entry.name.startswith(name_prefix):
        continue

    rel = entry.relative_to(self.root)
    display = f"{rel}/" if entry.is_dir() else str(rel)
    results.append(display)

    if len(results) >= limit:  # <-- Stops at 20
        break
```

The `iterdir()` call only scans the immediate directory contents. There is no recursive walking (`os.walk()`, `rglob()`, or similar).

### Current Behavior

| User Types | Result |
|------------|--------|
| `@` | Shows only root-level files/directories (max 20) |
| `@src/` | Shows only immediate children of `src/` (max 20) |
| `@src/tunacode/` | Shows only immediate children of `src/tunacode/` (max 20) |

**Problem:** Cannot find `src/tunacode/core/agents/base.py` without typing the full path level by level.

### Constraint Summary Table

| Constraint | Value | Location |
|------------|-------|----------|
| Result Limit | **20 files** | `file_filter.py:49` |
| Recursion Depth | **0 (none)** | `file_filter.py:67` |
| Directory Scope | Single directory only | Architectural |

### Existing Infrastructure NOT Being Used

**1. CodeIndex Caching System**
- Location: `src/tunacode/indexing/code_index.py`
- Has full recursive scanning capability
- Pre-warming with 5-second TTL
- ~500x speedup documented in `.claude/development/directory-caching-optimization.md`
- **Not integrated with FileFilter**

**2. Glob Tool**
- Location: `src/tunacode/tools/glob.py`
- Supports recursive search with 5000-file limit
- Uses `os.scandir()` with stack-based traversal
- **Not integrated with @ autocomplete**

### Comparison: Autocomplete vs Other Tools

| Feature | @ Autocomplete | `list_dir` tool | `glob` tool | CodeIndex |
|---------|----------------|-----------------|-------------|-----------|
| Recursion | None | Full | Full | Full |
| Max Results | 20 | 100 | 5000 | Unlimited |
| Performance | Fast (single dir) | Medium | Medium-Slow | Fast (indexed) |

## Key Patterns / Solutions Found

### Pattern: Progressive Navigation (Current)
- User must navigate one directory at a time
- Designed for interactive entry, not discovery
- Works for small projects, fails for large ones

### Potential Solutions

**Option A: Add Recursive Search with Depth Limit**
```python
def complete(self, prefix: str = "", limit: int = 50, max_depth: int = 3) -> list[str]:
    # Use os.walk() or rglob() with depth tracking
```

**Option B: Integrate CodeIndex**
- Leverage pre-indexed file list from CodeIndex singleton
- Fast lookups via cached directory structure
- No re-scanning needed

**Option C: Add Fuzzy Matching**
- Allow `@base.py` to find `src/tunacode/core/agents/base.py`
- Rank results by path depth (prefer shallower)

**Option D: Increase Limit + Add Configurable Depth**
- Make limit configurable (20 -> 100)
- Add `max_depth` parameter (default 3)
- Store in user settings

## Knowledge Gaps

- No documentation explaining why single-directory design was chosen
- No performance benchmarks for recursive vs single-level search
- Unknown impact on memory for very large projects (>10k files)

## References

- `src/tunacode/utils/ui/file_filter.py` - Core filtering logic
- `src/tunacode/ui/widgets/file_autocomplete.py` - Widget implementation
- `memory-bank/research/2025-12-04_14-50-38_at_file_picker_autocomplete.md` - Original design doc
- `.claude/development/directory-caching-optimization.md` - CodeIndex caching docs

## Recommended Fix Priority

1. **Quick Win:** Increase `limit` from 20 to 50-100 in `file_filter.py:49`
2. **Medium Effort:** Add `max_depth` parameter with recursive `os.walk()`
3. **Best Solution:** Integrate with CodeIndex for pre-indexed file discovery
