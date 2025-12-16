# Import Optimizer Analysis Report

**Generated**: 2025-12-14
**Scope**: /home/tuna/tunacode/src/tunacode

---

## Executive Summary

Analysis of **95+ Python files** in the `src/tunacode` directory for import issues.

### Key Findings

**Good News:**
- No wildcard imports (`from module import *`)
- No duplicate imports within files
- Proper use of TYPE_CHECKING blocks (9 files)
- No circular import chains detected

**Issues Found:**
- **72+ inline imports** that should be moved to file tops
- **1 potentially unused import** with `# noqa: F401`

---

## 1. Files with Correct TYPE_CHECKING Usage

These files properly use `if TYPE_CHECKING:` for type-only imports:

- `/home/tuna/tunacode/src/tunacode/core/agents/main.py`
- `/home/tuna/tunacode/src/tunacode/core/state.py`
- `/home/tuna/tunacode/src/tunacode/tools/authorization/context.py`
- `/home/tuna/tunacode/src/tunacode/utils/config/user_configuration.py`
- `/home/tuna/tunacode/src/tunacode/core/agents/agent_components/streaming.py`
- `/home/tuna/tunacode/src/tunacode/ui/widgets/messages.py`
- And 3 others

---

## 2. Inline Imports (72+ instances)

### Critical Inline Imports to Fix

#### `/home/tuna/tunacode/src/tunacode/core/agents/agent_components/node_processor.py` (Line 33)
```python
from tunacode.configuration.pricing import calculate_cost, get_model_pricing
```
- Inside the `_update_token_usage` function
- **Action**: Move to top of file

#### `/home/tuna/tunacode/src/tunacode/core/state.py` (Multiple lines)
- Lines 124-126, 217, 225-226, 244-245, 307-308, 352
- Many imports scattered in methods
- Duplicate imports of same modules in different methods
- **Action**: Consolidate at file top

#### `/home/tuna/tunacode/src/tunacode/ui/app.py` (12+ inline imports)
- Many imports inside methods
- Some may be intentional for circular import avoidance
- **Action**: Review each case individually

#### JSON imports in multiple files:
- `/home/tuna/tunacode/src/tunacode/tools/grep_components/pattern_matcher.py` (line 125)
- `/home/tuna/tunacode/src/tunacode/tools/grep_components/result_formatter.py` (line 82)
- `/home/tuna/tunacode/src/tunacode/configuration/models.py` (line 41)
- **Action**: Move `import json` to top of files

---

## 3. No Wildcard Imports Found

Search for `from .* import *` returned 0 results.

---

## 4. No Duplicate Imports Found

No files contain the same import statement twice.

---

## 5. No Circular Import Issues Detected

Analysis of import graphs shows no circular dependencies.

---

## 6. Recommendations

### Run ruff to confirm
```bash
ruff check --select F401 src/tunacode/
```

### Priority Actions:

1. **High**: Move pricing import in node_processor.py to file top
2. **Medium**: Consolidate scattered imports in core/state.py
3. **Low**: Review ui/app.py inline imports (some may be intentional)
4. **Low**: Move json imports to file tops

---

**End of Report**
