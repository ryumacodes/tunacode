---
title: "Viewport Standardization - Plan"
phase: Plan
date: "2025-12-18T19:00:00"
owner: "claude-agent"
parent_research: "memory-bank/research/2025-12-18_18-05-00_issue184_viewport_standardization.md"
git_commit_at_plan: "8bce32f"
tags: [plan, viewport, ui, coding]
---

## Goal

- Standardize tool panel viewport sizing across all 8 renderers using a single shared constant `TOOL_VIEWPORT_LINES = 26`.

### Non-goals

- Deployment/ops overhead
- Extensive test suites beyond validation
- UI redesign or new features
- BOX_HORIZONTAL/SEPARATOR_WIDTH consolidation (separate issue)

## Scope & Assumptions

### In Scope

- Add `LINES_RESERVED_FOR_HEADER_FOOTER` and `TOOL_VIEWPORT_LINES` to `constants.py`
- Update 8 tool renderers to use shared constant
- Fix `list_dir.py` truncation bug (produces 203 chars instead of 200)
- Fix `glob.py` dead code (line 207)

### Out of Scope

- Consolidating `BOX_HORIZONTAL`/`SEPARATOR_WIDTH` duplicates (low priority cleanup)
- Adding new renderers (e.g., `write_file.py`)
- Test infrastructure overhaul

### Assumptions

- All renderers import from `tunacode.constants`
- Standard reserve of 4 lines accommodates header, params, separators, status
- `research.py` is the gold standard pattern

## Deliverables

1. Updated `src/tunacode/constants.py` with new viewport constants
2. 8 updated tool renderers using `TOOL_VIEWPORT_LINES`
3. Fixed truncation bug in `list_dir.py`
4. Removed dead code in `glob.py`

## Readiness

- [x] Research complete with exact line numbers
- [x] All files identified and verified
- [x] No blocking dependencies
- [x] Git state clean (only untracked research docs)

## Milestones

- **M1**: Add constants to `constants.py`
- **M2**: Update renderers using correct reserve (web_fetch, update_file, research)
- **M3**: Fix renderers with incorrect reserve (bash, grep, read_file, glob, list_dir)
- **M4**: Fix bugs (list_dir truncation, glob dead code) + validate

## Work Breakdown (Tasks)

### Task 1: Add viewport constants to constants.py
- **Summary**: Add `LINES_RESERVED_FOR_HEADER_FOOTER = 4` and `TOOL_VIEWPORT_LINES = MAX_PANEL_LINES - LINES_RESERVED_FOR_HEADER_FOOTER`
- **Owner**: agent
- **Milestone**: M1
- **Dependencies**: None
- **Files**: `src/tunacode/constants.py:31-34`
- **Acceptance**: Constants defined, `TOOL_VIEWPORT_LINES == 26`

### Task 2: Update web_fetch.py to use shared constant
- **Summary**: Replace `MAX_PANEL_LINES - 4` with `TOOL_VIEWPORT_LINES`
- **Owner**: agent
- **Milestone**: M2
- **Dependencies**: Task 1
- **Files**: `src/tunacode/ui/renderers/tools/web_fetch.py:81`
- **Acceptance**: Import added, magic number replaced

### Task 3: Update update_file.py to use shared constant
- **Summary**: Replace `MAX_PANEL_LINES - 4` with `TOOL_VIEWPORT_LINES`
- **Owner**: agent
- **Milestone**: M2
- **Dependencies**: Task 1
- **Files**: `src/tunacode/ui/renderers/tools/update_file.py:108`
- **Acceptance**: Import added, magic number replaced

### Task 4: Update research.py to import from constants
- **Summary**: Remove local `LINES_RESERVED_FOR_HEADER_FOOTER`, import from constants
- **Owner**: agent
- **Milestone**: M2
- **Dependencies**: Task 1
- **Files**: `src/tunacode/ui/renderers/tools/research.py:27,167`
- **Acceptance**: Local constant removed, import from constants

### Task 5: Update bash.py viewport (6 -> 4 reserve)
- **Summary**: Replace `MAX_PANEL_LINES - 6` with `TOOL_VIEWPORT_LINES`
- **Owner**: agent
- **Milestone**: M3
- **Dependencies**: Task 1
- **Files**: `src/tunacode/ui/renderers/tools/bash.py:103`
- **Acceptance**: Import added, viewport = 26

### Task 6: Update grep.py viewport (2 -> 4 reserve)
- **Summary**: Replace `MAX_PANEL_LINES - 2` with `TOOL_VIEWPORT_LINES`
- **Owner**: agent
- **Milestone**: M3
- **Dependencies**: Task 1
- **Files**: `src/tunacode/ui/renderers/tools/grep.py:165`
- **Acceptance**: Import added, viewport = 26

### Task 7: Update read_file.py viewport (2 -> 4 reserve)
- **Summary**: Replace `MAX_PANEL_LINES - 2` with `TOOL_VIEWPORT_LINES`
- **Owner**: agent
- **Milestone**: M3
- **Dependencies**: Task 1
- **Files**: `src/tunacode/ui/renderers/tools/read_file.py:163`
- **Acceptance**: Import added, viewport = 26

### Task 8: Update glob.py viewport (2 -> 4 reserve)
- **Summary**: Replace `MAX_PANEL_LINES - 2` with `TOOL_VIEWPORT_LINES`
- **Owner**: agent
- **Milestone**: M3
- **Dependencies**: Task 1
- **Files**: `src/tunacode/ui/renderers/tools/glob.py:162`
- **Acceptance**: Import added, viewport = 26

### Task 9: Fix list_dir.py viewport (0 -> 4 reserve)
- **Summary**: Replace `MAX_PANEL_LINES` with `TOOL_VIEWPORT_LINES` at lines 100, 103
- **Owner**: agent
- **Milestone**: M3
- **Dependencies**: Task 1
- **Files**: `src/tunacode/ui/renderers/tools/list_dir.py:100,103`
- **Acceptance**: Import added, viewport = 26

### Task 10: Fix list_dir.py truncation bug
- **Summary**: Change `line[:MAX_PANEL_LINE_WIDTH] + "..."` to `line[:MAX_PANEL_LINE_WIDTH - 3] + "..."`
- **Owner**: agent
- **Milestone**: M4
- **Dependencies**: None
- **Files**: `src/tunacode/ui/renderers/tools/list_dir.py:91`
- **Acceptance**: Truncated lines are exactly 200 chars

### Task 11: Fix glob.py dead code
- **Summary**: Remove pointless conditional `if data.source == "index" else UI_COLORS["success"]` (both branches identical)
- **Owner**: agent
- **Milestone**: M4
- **Dependencies**: None
- **Files**: `src/tunacode/ui/renderers/tools/glob.py:207`
- **Acceptance**: Conditional removed, single assignment

### Task 12: Run ruff check and validate
- **Summary**: Run `ruff check --fix .` and verify all imports/changes are valid
- **Owner**: agent
- **Milestone**: M4
- **Dependencies**: Tasks 1-11
- **Files**: All modified files
- **Acceptance**: `ruff check` passes, app runs

## Risks & Mitigations

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Import cycle from constants.py | Low | Constants module has no internal deps |
| Visual regression from viewport changes | Medium | Manual visual check of each panel |
| Missed renderer location | Low | Research doc has exact line numbers |

## Test Strategy

- **Task 12 acceptance test**: `ruff check .` passes
- **Manual validation**: Launch app, trigger each tool, verify panel renders without overflow

## References

### Research Document
- `memory-bank/research/2025-12-18_18-05-00_issue184_viewport_standardization.md`
- Key sections: "Updated Summary Table", "Files Requiring Updates"

### Code References
- `src/tunacode/ui/renderers/tools/research.py:21-29` - Gold standard pattern
- `src/tunacode/constants.py:31-32` - Existing panel constants

### GitHub
- Issue: https://github.com/alchemiststudiosDOTai/tunacode/issues/184

---

## Final Gate

- **Plan path**: `memory-bank/plan/2025-12-18_19-00-00_viewport_standardization.md`
- **Milestone count**: 4
- **Task count**: 12
- **Ready for coding**: YES

**Next command**: `/context-engineer:execute "memory-bank/plan/2025-12-18_19-00-00_viewport_standardization.md"`
