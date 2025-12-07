---
title: "Startup Index Build – Plan"
phase: Plan
date: "2025-12-06T15:30:00"
owner: "Claude Agent"
parent_research: "memory-bank/research/2025-12-06_code_index_analysis.md"
git_commit_at_plan: "36afabe"
tags: [plan, performance, startup, codeindex, progressive]
---

## Goal

**Build CodeIndex at TUI startup with dynamic sizing - full index for small repos, progressive index for large repos.**

Single deliverable: Fast startup with visual feedback, regardless of repo size.

```
TUI starts
    ↓
Quick scan: count files
    ↓
If <1000 files → full index ("Mapped 847 files ✓")
If ≥1000 files → priority dirs only ("Mapped 847/12000 files, expanding...")
                 background worker continues
    ↓
Session ready - index usable immediately
```

**Non-goals:**
- File watchers / live refresh (future work)
- Integrating grep.py with CodeIndex (separate task)
- Refactoring CodeIndex internals (separate task per research doc)

## Scope & Assumptions

**In scope:**
- Quick file count scan at startup
- Dynamic decision: full vs progressive index
- Priority directories: `src/`, `lib/`, `app/`, `packages/`, top-level files
- Background expansion for large repos
- Visual feedback with file counts

**Out of scope:**
- grep.py integration (uses FileFilter, different architecture)
- CodeIndex refactoring (magic numbers, exception handling, etc.)
- New tests beyond minimal smoke test

**Assumptions:**
- Quick scan (<100ms) can count files without full indexing
- Priority dirs cover 80%+ of typical searches
- Background expansion completes before user needs deep files

**Constants:**
```python
QUICK_INDEX_THRESHOLD = 1000  # Files - full index if below
PRIORITY_DIRS = ["src", "lib", "app", "packages", "core", "internal"]
```

## Deliverables (DoD)

| Deliverable | Acceptance Criteria |
|-------------|---------------------|
| Quick file count | `_quick_count()` returns file count in <100ms |
| Dynamic decision | Full index if <1000 files, progressive otherwise |
| Priority indexing | Index PRIORITY_DIRS + top-level first |
| Background expansion | Large repos expand index after startup |
| Visual feedback | User sees progress ("Mapped X files ✓" or "X/Y files") |

## Readiness (DoR)

- [x] Research doc exists with architecture analysis
- [x] TUI initialization flow documented
- [x] CodeIndex API documented
- [x] LoadingIndicator pattern identified

## Milestones

| ID | Milestone | Description |
|----|-----------|-------------|
| M1 | Quick count | Add fast file counting without full index |
| M2 | Dynamic build | Choose full vs progressive based on count |
| M3 | Background expand | Continue indexing large repos in background |

## Work Breakdown (Tasks)

### Task 1: Add quick file count method

**Summary:** Fast `os.scandir` walk to count indexable files without building full index

**Target:** M1

**Dependencies:** None

**Files/Interfaces:**
- `src/tunacode/indexing/code_index.py` - add `quick_count()` method

**Implementation:**
```python
QUICK_INDEX_THRESHOLD = 1000

def quick_count(self) -> int:
    """Fast file count without full indexing."""
    count = 0
    stack = [self.root_dir]

    while stack and count < QUICK_INDEX_THRESHOLD + 1:
        current = stack.pop()
        try:
            for entry in os.scandir(current):
                if entry.is_dir() and entry.name not in self.IGNORE_DIRS:
                    stack.append(entry.path)
                elif entry.is_file():
                    ext = Path(entry.name).suffix.lower()
                    if ext in self.INDEXED_EXTENSIONS:
                        count += 1
        except (PermissionError, OSError):
            continue

    return count
```

**Acceptance Tests:**
- [ ] Returns count in <100ms for typical repos
- [ ] Stops counting at threshold + 1 (early exit)
- [ ] Respects IGNORE_DIRS

---

### Task 2: Add priority-first indexing

**Summary:** Index priority directories first, mark as partially indexed

**Target:** M2

**Dependencies:** Task 1

**Files/Interfaces:**
- `src/tunacode/indexing/code_index.py` - add `build_priority_index()` method
- Add `_partial_indexed: bool` flag

**Implementation:**
```python
PRIORITY_DIRS = {"src", "lib", "app", "packages", "core", "internal"}

def build_priority_index(self) -> int:
    """Build index for priority directories only."""
    with self._lock:
        self._clear_indices()

        # Index top-level files
        self._scan_directory(self.root_dir, max_depth=1)

        # Index priority subdirectories fully
        for name in PRIORITY_DIRS:
            priority_path = self.root_dir / name
            if priority_path.is_dir():
                self._scan_directory(priority_path)

        self._partial_indexed = True
        return len(self._all_files)
```

**Acceptance Tests:**
- [ ] Indexes src/, lib/, etc. fully
- [ ] Indexes top-level files only (depth=1)
- [ ] Sets `_partial_indexed = True`

---

### Task 3: Startup integration with dynamic choice

**Summary:** Hook into `_start_repl()` with dynamic full/progressive decision

**Target:** M2

**Dependencies:** Task 1, Task 2

**Files/Interfaces:**
- `src/tunacode/ui/app.py` - modify `_start_repl()`

**Implementation:**
```python
async def _build_index_async(self) -> tuple[int, int | None]:
    """Build index with dynamic sizing. Returns (indexed, total_or_none)."""
    def do_build():
        index = CodeIndex.get_instance()
        total = index.quick_count()

        if total < QUICK_INDEX_THRESHOLD:
            index.build_index()
            return len(index._all_files), None
        else:
            count = index.build_priority_index()
            return count, total

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, do_build)

def _start_repl(self) -> None:
    self.set_focus(self.editor)
    self.run_worker(self._request_worker, exclusive=False)

    # Show building status
    self.write_to_viewport("[dim]Building system map...[/dim]")

    # Build index async
    self.run_worker(self._do_startup_index)
```

**Acceptance Tests:**
- [ ] Small repos get full index
- [ ] Large repos get priority index
- [ ] UI shows appropriate message

---

### Task 4: Background expansion for large repos

**Summary:** Continue indexing remaining directories in background

**Target:** M3

**Dependencies:** Task 3

**Files/Interfaces:**
- `src/tunacode/indexing/code_index.py` - add `expand_index()` method
- `src/tunacode/ui/app.py` - spawn background worker

**Implementation:**
```python
def expand_index(self) -> None:
    """Expand partial index to full index in background."""
    if not self._partial_indexed:
        return

    with self._lock:
        # Scan remaining directories
        for entry in os.scandir(self.root_dir):
            if entry.is_dir() and entry.name not in self.IGNORE_DIRS:
                if entry.name not in PRIORITY_DIRS:
                    self._scan_directory(Path(entry.path))

        self._partial_indexed = False
        self._indexed = True
```

**Acceptance Tests:**
- [ ] Only runs if `_partial_indexed = True`
- [ ] Indexes remaining directories
- [ ] Sets `_indexed = True` when complete

---

## Risks & Mitigations

| Risk | Impact | Likelihood | Mitigation | Trigger |
|------|--------|------------|------------|---------|
| Quick count still slow | Medium | Low | Add time limit (100ms) with early exit | Count >100ms |
| Priority dirs miss files | Medium | Medium | Fallback to full index on first miss | glob returns 0 results |
| Background conflicts | Low | Low | RLock already in place | Concurrent access |

## Test Strategy

**ONE test only (per CLAUDE.md):**

```python
def test_dynamic_index_threshold():
    """Verify dynamic indexing respects threshold."""
    from tunacode.indexing import CodeIndex
    CodeIndex.reset_instance()

    index = CodeIndex.get_instance()
    count = index.quick_count()

    if count < 1000:
        index.build_index()
        assert index._indexed is True
        assert index._partial_indexed is False
    else:
        index.build_priority_index()
        assert index._partial_indexed is True
```

## References

- Research: `memory-bank/research/2025-12-06_code_index_analysis.md`
- TUI entry: `src/tunacode/ui/app.py:132` (`_start_repl()`)
- CodeIndex: `src/tunacode/indexing/code_index.py:206` (`build_index()`)
- LoadingIndicator pattern: `src/tunacode/ui/app.py:168-169`

---

## Final Gate

| Item | Value |
|------|-------|
| Plan path | `memory-bank/plan/2025-12-06_15-30-00_startup_index_build.md` |
| Milestones | 3 |
| Tasks | 4 |
| Gates | Acceptance tests per task |
| Risk items | 3 |

**Next command:** `/context-engineer:execute "memory-bank/plan/2025-12-06_15-30-00_startup_index_build.md"`
