# Research - Sparse Directory Cleanup Map
**Date:** 2025-12-05
**Owner:** agent
**Phase:** Research

## Goal
Map all directories in tunacode that contain only a single file or just `__init__.py`, identifying consolidation candidates before cleanup.

## Findings

### Tier 1: Single-File Directories (HIGH consolidation potential)

| Directory | Files | Lines | Importers | Recommendation |
|-----------|-------|-------|-----------|----------------|
| `src/tunacode/templates/` | `loader.py` (17 lines) + `__init__.py` | 22 | 1 (authorization/handler.py) | **MERGE into types.py** |
| `src/tunacode/indexing/` | `code_index.py` (533 lines) + `__init__.py` | 538 | 1 (tools/glob.py) | Keep - complex singleton |
| `src/tunacode/utils/config/` | `user_configuration.py` (120 lines) + `__init__.py` | 137 | 2 | **FLATTEN to utils/config.py** |
| `src/tunacode/utils/security/` | `command.py` (155 lines) + `__init__.py` | 174 | 1 | **FLATTEN to utils/security.py** |

### Tier 2: Two-File Directories (MEDIUM consolidation potential)

| Directory | Files | Total Lines | Importers | Recommendation |
|-----------|-------|-------------|-----------|----------------|
| `src/tunacode/tools/utils/` | `ripgrep.py`, `text_match.py` | 678 | 2 | **MERGE into parent tools/** |
| `src/tunacode/utils/system/` | `gitignore.py`, `paths.py` | 289 | 2 | Keep - cohesive system utils |
| `src/tunacode/utils/ui/` | `helpers.py` (24), `file_filter.py` (135) | 168 | 5 | Keep - actively used |
| `src/tunacode/utils/messaging/` | `message_utils.py`, `token_counter.py` | 112 | 3 | Keep - logical grouping |

### Tier 3: Empty Namespace Packages

| Directory | Status | Recommendation |
|-----------|--------|----------------|
| `src/tunacode/utils/__init__.py` | Empty (0 lines) | Keep - namespace for submodules |

### Tier 4: Well-Structured (Keep As-Is)

| Directory | Files | Purpose |
|-----------|-------|---------|
| `tools/grep_components/` | 4 files | Modular grep decomposition |
| `tools/authorization/` | 8 files | Authorization subsystem |
| `core/agents/agent_components/` | 12 files | Agent orchestration |
| `ui/widgets/` | 5 files | Textual widgets |
| `ui/renderers/` | 3 files | Rendering logic |
| `ui/screens/` | 3 files | Textual screens |

## Key Patterns / Solutions Found

### Import Frequency Analysis
```
constants.py:     20+ imports  (DO NOT TOUCH)
types.py:         17 imports   (DO NOT TOUCH)
core/state.py:    10+ imports  (DO NOT TOUCH)
exceptions.py:    8 imports    (DO NOT TOUCH)
templates/:       1 import     (CONSOLIDATION CANDIDATE)
indexing/:        1 import     (KEEP - complex code)
tools/utils/:     2 imports    (CONSOLIDATION CANDIDATE)
```

### Recommended Cleanup Actions

**Action 1: Flatten `templates/` into `types.py`**
```
FROM: src/tunacode/templates/loader.py -> Template dataclass (17 lines)
TO:   src/tunacode/types.py
UPDATE: src/tunacode/tools/authorization/handler.py:6
DELETE: src/tunacode/templates/ (entire directory)
```

**Action 2: Flatten `utils/config/` to module**
```
FROM: src/tunacode/utils/config/user_configuration.py
TO:   src/tunacode/utils/config.py (single file)
UPDATE: 2 import sites
DELETE: src/tunacode/utils/config/ directory
```

**Action 3: Flatten `utils/security/` to module**
```
FROM: src/tunacode/utils/security/command.py
TO:   src/tunacode/utils/security.py (single file)
UPDATE: 1 import site
DELETE: src/tunacode/utils/security/ directory
```

**Action 4: Merge `tools/utils/` into parent**
```
FROM: src/tunacode/tools/utils/ripgrep.py
TO:   src/tunacode/tools/ripgrep.py
FROM: src/tunacode/tools/utils/text_match.py
TO:   src/tunacode/tools/text_match.py
UPDATE: 2 import sites (grep.py, update_file.py)
DELETE: src/tunacode/tools/utils/ directory
```

## Knowledge Gaps
- Need to verify no dynamic imports reference these paths
- Should check if any external tools depend on current structure
- `indexing/` has complex singleton - needs careful review if touched

## Directory Tree Summary

```
src/tunacode/
├── __init__.py
├── constants.py          # CRITICAL - 20+ imports
├── types.py              # CRITICAL - 17 imports
├── exceptions.py         # CRITICAL - 8 imports
├── configuration/        # 5 files - KEEP
├── core/
│   ├── state.py          # CRITICAL - 10+ imports
│   ├── compaction.py     # 1 import (could merge into agents/main.py)
│   ├── logging/          # 3 files - KEEP
│   └── agents/           # 4 files + agent_components/ - KEEP
├── tools/
│   ├── *.py              # 8 tool files - KEEP
│   ├── authorization/    # 8 files - KEEP
│   ├── grep_components/  # 4 files - KEEP
│   └── utils/            # 2 files - CONSOLIDATE
├── ui/
│   ├── app.py, main.py, styles.py
│   ├── commands/         # Could split __init__.py (250 lines)
│   ├── components/       # 3 files - KEEP
│   ├── renderers/        # 3 files - KEEP
│   ├── screens/          # 3 files - KEEP
│   └── widgets/          # 5 files - KEEP
├── utils/
│   ├── __init__.py       # Empty namespace
│   ├── config/           # 1 file - FLATTEN
│   ├── messaging/        # 2 files - KEEP
│   ├── parsing/          # 3 files - KEEP
│   ├── security/         # 1 file - FLATTEN
│   ├── system/           # 2 files - KEEP
│   └── ui/               # 2 files - KEEP
├── indexing/             # 1 file (533 lines) - KEEP (complex)
└── templates/            # 1 file (17 lines) - FLATTEN
```

## References
- `src/tunacode/templates/loader.py:7-16` - Template dataclass definition
- `src/tunacode/utils/config/user_configuration.py` - Configuration persistence
- `src/tunacode/utils/security/command.py` - Command validation
- `src/tunacode/tools/utils/ripgrep.py` - Ripgrep wrapper
- `src/tunacode/tools/utils/text_match.py` - Text matching utilities
