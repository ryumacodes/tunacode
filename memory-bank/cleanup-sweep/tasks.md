# Cleanup Sweep: Parallel Task List

**Generated**: 2025-12-14
**Total Tasks**: 15 parallel-safe cleanup opportunities

---

## Hard Guards Check
- [x] Each task deletes or simplifies (no additions)
- [x] Each task is independent (no dependencies)
- [x] Each task is <5 minutes to execute
- [x] Tasks can run in parallel safely

---

## Task 1: Remove unused TOOL_* constants
**Type:** dead-code
**Files:** /home/tuna/tunacode/src/tunacode/constants.py
**Actions:**
  - DELETE lines 61-68 (TOOL_READ_FILE through TOOL_GLOB)
**Estimated Time:** 1 minute
**Risk:** low
**Verification:** Run `ruff check src/tunacode/constants.py` and `grep -r "TOOL_READ_FILE\|TOOL_WRITE_FILE\|TOOL_UPDATE_FILE\|TOOL_BASH\|TOOL_GREP\|TOOL_LIST_DIR\|TOOL_GLOB" src/` should return only the definition

---

## Task 2: Remove unused CMD_* and DESC_* constants
**Type:** dead-code
**Files:** /home/tuna/tunacode/src/tunacode/constants.py
**Actions:**
  - DELETE lines 84-99 (CMD_HELP through COMMAND_PREFIX)
**Estimated Time:** 1 minute
**Risk:** low
**Verification:** Run `grep -r "CMD_HELP\|CMD_CLEAR\|CMD_YOLO\|CMD_MODEL\|CMD_EXIT\|CMD_QUIT\|DESC_HELP\|DESC_CLEAR" src/` should return only definitions

---

## Task 3: Remove unused UI_* constants
**Type:** dead-code
**Files:** /home/tuna/tunacode/src/tunacode/constants.py
**Actions:**
  - DELETE lines 150, 152-157 (keep UI_THINKING_MESSAGE on line 151)
**Estimated Time:** 1 minute
**Risk:** low
**Verification:** Build passes, tests pass

---

## Task 4: Remove unused PANEL_* constants
**Type:** dead-code
**Files:** /home/tuna/tunacode/src/tunacode/constants.py
**Actions:**
  - DELETE lines 160-163 (PANEL_ERROR through PANEL_AVAILABLE_COMMANDS)
**Estimated Time:** 1 minute
**Risk:** low
**Verification:** Build passes, tests pass

---

## Task 5: Remove unused ERROR_* constants (keep ERROR_FILE_TOO_LARGE)
**Type:** dead-code
**Files:** /home/tuna/tunacode/src/tunacode/constants.py
**Actions:**
  - DELETE lines 166-168, 170-182 (keep line 169 ERROR_FILE_TOO_LARGE)
**Estimated Time:** 2 minutes
**Risk:** low
**Verification:** Grep for ERROR_ constants shows only used ones remain

---

## Task 6: Remove unused CMD_OUTPUT_* constants (keep CMD_OUTPUT_TRUNCATED)
**Type:** dead-code
**Files:** /home/tuna/tunacode/src/tunacode/constants.py
**Actions:**
  - DELETE lines 185-187 (keep line 188 CMD_OUTPUT_TRUNCATED)
**Estimated Time:** 1 minute
**Risk:** low
**Verification:** Build passes

---

## Task 7: Remove unused MSG_* constants (keep MSG_FILE_SIZE_LIMIT)
**Type:** dead-code
**Files:** /home/tuna/tunacode/src/tunacode/constants.py
**Actions:**
  - DELETE lines 192-194 (keep line 195 MSG_FILE_SIZE_LIMIT)
**Estimated Time:** 1 minute
**Risk:** low
**Verification:** Build passes

---

## Task 8: Remove unused GUIDE_FILE_PATTERN constant
**Type:** dead-code
**Files:** /home/tuna/tunacode/src/tunacode/constants.py
**Actions:**
  - DELETE line 16 (GUIDE_FILE_PATTERN)
**Estimated Time:** 1 minute
**Risk:** low
**Verification:** Grep shows no references

---

## Task 9: Remove unused type aliases from types.py
**Type:** dead-code
**Files:** /home/tuna/tunacode/src/tunacode/types.py
**Actions:**
  - DELETE EnvConfig (line 27)
  - DELETE ModelRegistry (line 51)
  - DELETE ToolStartCallback (line 60)
  - DELETE UICallback, UIInputCallback (lines 90-91)
  - DELETE AgentConfig, AgentName (lines 97-98)
  - DELETE CommandArgs, CommandResult (lines 132-133)
  - DELETE FileContent through LineNumber (lines 146-150)
  - DELETE ErrorContext (line 152)
  - DELETE AsyncFunc, AsyncToolFunc, AsyncVoidFunc (lines 156-158)
  - DELETE UpdateOperation through DiffHunk (lines 160-162)
  - DELETE ValidationResult, Validator (lines 164-165)
  - DELETE TokenCount, CostAmount (lines 167-168)
**Estimated Time:** 5 minutes
**Risk:** medium (need to verify no dynamic usage)
**Verification:** Run full test suite, ruff check

---

## Task 10: Remove unused functions from key_descriptions.py
**Type:** dead-code
**Files:** /home/tuna/tunacode/src/tunacode/configuration/key_descriptions.py
**Actions:**
  - DELETE get_key_description function (lines 212-216)
  - DELETE get_service_type_for_api_key function (lines 217-227)
  - DELETE get_categories function (lines 229-235)
  - DELETE get_configuration_glossary function (lines 237-260)
**Estimated Time:** 3 minutes
**Risk:** medium (verify not intended for future use)
**Verification:** Run tests, verify no runtime errors

---

## Task 11: Remove unused retry functions from retry.py
**Type:** dead-code
**Files:** /home/tuna/tunacode/src/tunacode/utils/parsing/retry.py
**Actions:**
  - DELETE retry_on_json_error decorator (lines 11-82)
  - DELETE retry_json_parse_async function (lines 117-146)
**Estimated Time:** 3 minutes
**Risk:** medium
**Verification:** Run tests, verify retry_json_parse still works

---

## Task 12: Remove unnecessary pass statement in json_utils.py
**Type:** dead-code
**Files:** /home/tuna/tunacode/src/tunacode/utils/parsing/json_utils.py
**Actions:**
  - DELETE pass statement on line 111 (before raise)
  - Simplify exception handler on lines 74-79 (remove else: pass branches)
**Estimated Time:** 2 minutes
**Risk:** low
**Verification:** Tests pass, no behavior change

---

## Task 13: Consolidate BOX_HORIZONTAL and SEPARATOR_WIDTH constants
**Type:** duplication
**Files:**
  - /home/tuna/tunacode/src/tunacode/ui/renderers/tools/bash.py (lines 17-18)
  - /home/tuna/tunacode/src/tunacode/ui/renderers/tools/grep.py (lines 17-18)
  - /home/tuna/tunacode/src/tunacode/ui/renderers/tools/glob.py (lines 18-19)
  - /home/tuna/tunacode/src/tunacode/ui/renderers/tools/list_dir.py (lines 18-19)
  - /home/tuna/tunacode/src/tunacode/ui/renderers/tools/read_file.py (lines 18-19)
  - /home/tuna/tunacode/src/tunacode/ui/renderers/tools/update_file.py (lines 19-20)
  - /home/tuna/tunacode/src/tunacode/ui/renderers/tools/web_fetch.py (lines 17-18)
**Actions:**
  - ADD BOX_HORIZONTAL and SEPARATOR_WIDTH to constants.py
  - DELETE from all 7 tool renderer files
  - ADD import from constants.py to each file
**Estimated Time:** 5 minutes
**Risk:** low
**Verification:** Build passes, UI renders correctly

---

## Task 14: Consolidate _truncate_line function
**Type:** duplication
**Files:**
  - /home/tuna/tunacode/src/tunacode/ui/renderers/tools/bash.py (line 91)
  - /home/tuna/tunacode/src/tunacode/ui/renderers/tools/grep.py (line 114)
  - /home/tuna/tunacode/src/tunacode/ui/renderers/tools/list_dir.py (line 88)
  - /home/tuna/tunacode/src/tunacode/ui/renderers/tools/read_file.py (line 121)
  - /home/tuna/tunacode/src/tunacode/ui/renderers/tools/web_fetch.py (line 69)
**Actions:**
  - KEEP _truncate_line in bash.py (canonical location)
  - EXPORT from ui/renderers/tools/__init__.py
  - DELETE from grep.py, list_dir.py, read_file.py, web_fetch.py
  - IMPORT in those files from the canonical location
**Estimated Time:** 5 minutes
**Risk:** low
**Verification:** Build passes, tool output renders correctly

---

## Task 15: Move inline pricing import to file top
**Type:** import
**Files:** /home/tuna/tunacode/src/tunacode/core/agents/agent_components/node_processor.py
**Actions:**
  - DELETE inline import on line 33
  - ADD `from tunacode.configuration.pricing import calculate_cost, get_model_pricing` to file top
**Estimated Time:** 1 minute
**Risk:** low
**Verification:** Tests pass, no import errors

---

## Prioritization Order

### Tier 1: Safest/Fastest (Tasks 1-8, 12, 15)
Single-line or few-line deletions with zero risk:
- Task 1-8: Remove unused constants
- Task 12: Remove pass statements
- Task 15: Move inline import

### Tier 2: Medium Risk (Tasks 9-11)
Larger deletions requiring test verification:
- Task 9: Remove type aliases
- Task 10: Remove unused functions
- Task 11: Remove retry functions

### Tier 3: Refactoring (Tasks 13-14)
Require adding imports when deleting:
- Task 13: Consolidate constants
- Task 14: Consolidate _truncate_line

---

## Recommended Parallel Execution

**Wave 1** (can all run simultaneously):
- Tasks 1-8 (constants.py cleanup)
- Task 12 (json_utils.py cleanup)
- Task 15 (import fix)

**Wave 2** (after Wave 1 verified):
- Task 9 (types.py cleanup)
- Task 10 (key_descriptions.py cleanup)
- Task 11 (retry.py cleanup)

**Wave 3** (after Wave 2 verified):
- Task 13 (consolidate constants)
- Task 14 (consolidate _truncate_line)

---

## Summary

| Tier | Tasks | Lines to DELETE | Lines to ADD | Risk |
|------|-------|-----------------|--------------|------|
| 1 | 1-8, 12, 15 | ~80 lines | 0 lines | Low |
| 2 | 9-11 | ~100 lines | 0 lines | Medium |
| 3 | 13-14 | ~40 lines | ~20 lines | Low |

**Total Estimated Deletions**: ~220 lines
**Total Estimated Additions**: ~20 lines (imports only)
**Net Reduction**: ~200 lines

---

**End of Task List**
