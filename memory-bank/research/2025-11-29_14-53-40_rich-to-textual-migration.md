# Research - Rich to Textual Migration Mapping

**Date:** 2025-11-29
**Owner:** claude
**Phase:** Research
**Git Commit:** dfe97b4

## Goal

Map all Rich library imports and usage patterns across the codebase to prepare for migration to Textual.

## Findings

### Files with Rich Imports (7 active source files)

| File | Rich Components Used |
|------|---------------------|
| `src/tunacode/ui/panels.py` | Markdown, Padding, Pretty, Table, Text, ROUNDED, Live, Panel |
| `src/tunacode/ui/tool_ui.py` | ROUNDED, Markdown, Padding, Panel |
| `src/tunacode/ui/output.py` | Padding, Console |
| `src/tunacode/ui/console.py` | Console, Markdown |
| `src/tunacode/ui/utils.py` | Console |
| `src/tunacode/core/logging/handlers.py` | Console, Text |
| `src/tunacode/utils/diff_utils.py` | Text |

### Rich Component Usage Summary

| Component | File Count | Primary Usage |
|-----------|------------|---------------|
| Console | 4 | Core output, lazy-loaded proxy pattern |
| Text | 4 | Styled text, diff rendering, logging |
| Panel | 2 | Content containers with borders |
| Padding | 3 | Spacing around content |
| Markdown | 3 | Rendering markdown content |
| Table | 1 | Help commands display |
| Live | 1 | Streaming updates |
| Pretty | 1 | Object inspection |
| ROUNDED | 2 | Box style constant |

### Current Dependency Versions

From `pyproject.toml`:
- Rich: `>=14.2.0,<15.0.0` (line 34)
- Textual: `textual` (line 37, no version constraint)
- Textual Dev: `textual-dev` (line 51, dev dependency)

## Key Patterns / Solutions Found

### 1. Lazy Loading Pattern
- `ui/console.py:89-96` - `_LazyConsole` proxy defers Rich import until first access
- `ui/panels.py:52-78` - `get_rich_components()` caches imports on demand
- **Relevance:** Can retain this pattern during migration

### 2. Console Abstraction Layer
- `ui/console.py` - Centralized `get_console()` function
- `ui/output.py` - Duplicate `_LazyConsole` wrapper
- **Relevance:** Natural migration point - swap implementation behind interface

### 3. Async/Sync Wrapper Pattern
- `ui/decorators.py:14-59` - `@create_sync_wrapper` decorator
- Applied to `print()`, `panel()` functions
- **Relevance:** May need rethinking with Textual's message-based architecture

### 4. Prompt Toolkit Integration (NOT Rich)
- `ui/input.py` - Uses prompt_toolkit, NOT Rich for input
- `ui/output.py:70` - Wraps Rich prints in `run_in_terminal()`
- **Relevance:** Input already separate from Rich - migration only affects output

### 5. Centralized Color Management
- `UI_COLORS` dictionary accessed via `DotDict(UI_COLORS)`
- Used in: `output.py`, `panels.py`
- **Relevance:** Convert to Textual CSS themes

### 6. Streaming Panel Architecture
- `ui/panels.py:131-432` - `StreamingAgentPanel` class
- Uses `Rich.Live` with `refresh_per_second=4`
- Animated dots, async content updates, lock-based thread safety
- **Relevance:** Most complex migration - needs Textual reactive equivalent

## Migration Complexity by File

### High Complexity (require significant redesign)
| File | Reason |
|------|--------|
| `panels.py` | StreamingAgentPanel with Live updates, animation tasks |

### Medium Complexity (component swaps)
| File | Reason |
|------|--------|
| `tool_ui.py` | Panel/Markdown rendering - Textual has equivalents |
| `output.py` | Console abstraction - can swap implementation |
| `console.py` | Console wrapper - needs Textual console equivalent |

### Low Complexity (simple replacements)
| File | Reason |
|------|--------|
| `handlers.py` | Logging - can use Textual Log widget |
| `diff_utils.py` | Text styling - Textual supports Rich Text |
| `utils.py` | Simple Console usage |

## Knowledge Gaps

1. **Performance comparison**: No benchmarks for Rich.Live vs Textual reactive updates
2. **Spinner equivalents**: Need to identify Textual LoadingIndicator patterns
3. **Test coverage**: No UI tests exist - need to establish baseline before migration

## Recommended Migration Strategy

### Phase 1 - Foundation
- Create Textual console abstraction matching existing interface
- Implement Textual equivalents for Panel, Table components
- Keep Rich as fallback during transition

### Phase 2 - Output Layer
- Migrate `output.py` and `console.py` to use Textual
- Convert `tool_ui.py` panel rendering
- Update color system to Textual CSS

### Phase 3 - Complex Components
- Convert `StreamingAgentPanel` to Textual widget with reactive updates
- Replace `Rich.Live` with Textual's built-in refresh

### Phase 4 - Cleanup
- Remove Rich dependency
- Delete lazy-loading workarounds
- Consolidate duplicate abstractions

## References

- `src/tunacode/ui/panels.py` - StreamingAgentPanel implementation
- `src/tunacode/ui/console.py` - Console abstraction layer
- `src/tunacode/ui/output.py` - Output functions and spinner
- `pyproject.toml:34-37` - Dependency versions
