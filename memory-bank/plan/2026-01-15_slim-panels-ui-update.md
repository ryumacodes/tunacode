# Plan – Slim Panels UI Update (Option B)

**Date:** 2026-01-15
**Owner:** user + agent
**Phase:** Ready for Implementation
**Status:** APPROVED

## Goal

Transform tool panels from heavy boxed layouts to slim, line-based headers with minimal chrome. Target ~33% vertical space reduction while maintaining readability.

## Visual Target

```
— read_file ——————————————————————————————— 120 lines · 0.1s —
  ↳ src/tunacode/core/prompting/engine.py

  1 │ """Core Prompting Engine"""
  2 │ from typing import Protocol, Callable
  3 │ from dataclasses import dataclass
  [3/120]
```

## Design Principles

1. **Line headers, not box borders** - `— tool_name ——— stats —`
2. **Stats in header** - Move timing/counts to right side of header
3. **Arrow subtitle** - `↳ filepath` for context
4. **Minimal separators** - No internal zone dividers
5. **Compact truncation** - `[5/120]` not `[5/120 displayed] total: 120 lines`
6. **Zero vertical padding** - Content flows directly

## Before / After

```
BEFORE (12 lines):                 AFTER (6 lines):
┌─────── read_file ───────┐        — read_file ——— 120 lines · 0.1s —
│                         │          ↳ engine.py
│  src/.../engine.py      │
│  ─────────────────────  │          1 │ """Core Prompting..."""
│                         │          2 │ from typing import...
│  1 """Core Prompting""" │          [2/120]
│  2 from typing import   │
│  ─────────────────────  │
│  [2/120 displayed]      │
│  120 lines  0.1s        │
│                20:46:02 │
└─────────────────────────┘
```

## Implementation Tasks

### Phase 1: Core Infrastructure

- [ ] **1.1** Create `SlimRenderer` base class in `renderers/tools/slim_base.py`
  - Line header builder: `— {name} ——————— {stats} —`
  - Arrow subtitle builder: `  ↳ {context}`
  - Compact truncation: `[{shown}/{total}]`
  - No Panel(), just Text/Group composition

- [ ] **1.2** Create header line utility function
  ```python
  def slim_header(name: str, stats: str, width: int = 70) -> Text:
      """Build: — name ——————————————————————— stats —"""
  ```

- [ ] **1.3** Update constants in `constants.py`
  ```python
  SLIM_PANEL_WIDTH = 70
  SLIM_VIEWPORT_LINES = 5  # Reduced from 8
  ```

### Phase 2: Renderer Migration

Migrate each renderer to slim format:

- [ ] **2.1** `read_file.py` → SlimReadFileRenderer
  - Header: `— read_file ——— {lines} lines · {time}s —`
  - Subtitle: `↳ {filepath}`
  - Content: Line-numbered code
  - Footer: `[{shown}/{total}]`

- [ ] **2.2** `glob.py` → SlimGlobRenderer
  - Header: `— glob ——— {count} files · {time}s —`
  - Subtitle: `↳ {pattern}`
  - Content: File list
  - Footer: `[{shown}/{total}]`

- [ ] **2.3** `grep.py` → SlimGrepRenderer
  - Header: `— grep ——— {matches} matches · {files} files · {time}s —`
  - Subtitle: `↳ pattern: "{pattern}"`
  - Content: Match lines with file:line prefix
  - Footer: `[{shown}/{total}]`

- [ ] **2.4** `bash.py` → SlimBashRenderer
  - Header: `— bash ——— {ok|exit N} · {time}s —`
  - Subtitle: `↳ $ {command}`
  - Content: stdout/stderr
  - Footer: `[{shown}/{total}]`

- [ ] **2.5** `update_file.py` → SlimUpdateFileRenderer
  - Header: `— update_file ——— +{added} -{removed} · {time}s —`
  - Subtitle: `↳ {filepath}`
  - Content: Diff with line numbers, red/green highlighting
  - Footer: `[{shown}/{total}]`

- [ ] **2.6** `list_dir.py` → SlimListDirRenderer
  - Header: `— list_dir ——— {files} files · {dirs} dirs · {time}s —`
  - Subtitle: `↳ {directory}`
  - Content: Tree view
  - Footer: `[{shown}/{total}]`

- [ ] **2.7** `write_file.py` → SlimWriteFileRenderer
  - Header: `— write_file ——— {lines} lines · {time}s —`
  - Subtitle: `↳ {filepath}`
  - Content: Preview of written content
  - Footer: `[{shown}/{total}]`

- [ ] **2.8** `web_fetch.py` → SlimWebFetchRenderer
  - Header: `— web_fetch ——— {status} · {time}s —`
  - Subtitle: `↳ {url}`
  - Content: Response preview
  - Footer: `[{shown}/{total}]`

### Phase 3: Generic Fallback

- [ ] **3.1** Update `tool_panel()` in `panels.py` to use slim format
  - Fallback for tools without custom renderers
  - Same line-header pattern

- [ ] **3.2** Update `tool_panel_smart()` routing to use new renderers

### Phase 4: Styling

- [ ] **4.1** Update `panels.tcss` - remove box-related styles
- [ ] **4.2** Add slim panel styles if needed
- [ ] **4.3** Verify NeXTSTEP theme compatibility

### Phase 5: Polish

- [ ] **5.1** Color coding for header line based on status
  - Success: green `—`
  - Error: red `—`
  - Running: cyan `—`

- [ ] **5.2** Add subtle background tint option (future)
- [ ] **5.3** Test with various terminal widths

## Files to Modify

| File | Change |
|------|--------|
| `src/tunacode/ui/renderers/tools/base.py` | Add `SlimRenderer` base or utilities |
| `src/tunacode/ui/renderers/tools/read_file.py` | Migrate to slim |
| `src/tunacode/ui/renderers/tools/glob.py` | Migrate to slim |
| `src/tunacode/ui/renderers/tools/grep.py` | Migrate to slim |
| `src/tunacode/ui/renderers/tools/bash.py` | Migrate to slim |
| `src/tunacode/ui/renderers/tools/update_file.py` | Migrate to slim |
| `src/tunacode/ui/renderers/tools/list_dir.py` | Migrate to slim |
| `src/tunacode/ui/renderers/tools/write_file.py` | Migrate to slim |
| `src/tunacode/ui/renderers/tools/web_fetch.py` | Migrate to slim |
| `src/tunacode/ui/renderers/panels.py` | Update fallback |
| `src/tunacode/ui/styles/panels.tcss` | Update styles |
| `src/tunacode/constants.py` | Add slim constants |

## Header Format Reference

```
— {tool_name} ————————————————————————————— {stats} —
  ↳ {context_line}

  {content_line_1}
  {content_line_2}
  {content_line_3}
  [{shown}/{total}]
```

### Stats by Tool Type

| Tool | Stats Format |
|------|-------------|
| read_file | `{lines} lines · {time}s` |
| glob | `{count} files · {time}s` |
| grep | `{matches} matches · {files} files · {time}s` |
| bash | `{ok\|exit N} · {time}s` |
| update_file | `+{added} -{removed} · {time}s` |
| list_dir | `{files} files · {dirs} dirs · {time}s` |
| write_file | `{lines} lines · {time}s` |
| web_fetch | `{status} · {time}s` |

## Success Criteria

1. All tool panels use slim format
2. ~33% vertical space reduction achieved
3. Stats visible in header at a glance
4. No regression in information shown
5. Consistent look across all tool types
6. Works with both default and NeXTSTEP themes

## Future Enhancements (Not This PR)

- LSP diagnostics section (from mockup)
- Activity line with fish animation
- Grouped sections (Tools / LSP / Agent)
- Expand/collapse drawer

## References

- Research: `memory-bank/research/2026-01-15_tool-panel-redesign-options.md`
- Mockup: `tunacode-cli-lsp.webp`
- Current base: `src/tunacode/ui/renderers/tools/base.py`
