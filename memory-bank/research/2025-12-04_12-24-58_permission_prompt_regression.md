# Research – Permission Prompt Regression for Write Tools
**Date:** 2025-12-04
**Owner:** Claude Agent
**Phase:** Research
**Status:** RESOLVED - Confirmed working

## Resolution

**2025-12-04:** Issue was a one-off/transient. Permission prompts confirmed working after re-test. Likely cause was accidental YOLO mode toggle or session state anomaly. No code changes needed.

## Goal
Investigate why the REPL no longer asks for permission before executing write tools (bash, write_file, update_file).

## Findings

### Authorization System Architecture

The permission system is fully implemented in `src/tunacode/tools/authorization/`:

| File | Purpose |
|------|---------|
| `handler.py` | `ToolHandler` class - coordinates authorization |
| `policy.py` | `AuthorizationPolicy` - evaluates rules |
| `rules.py` | Four authorization rules with priorities |
| `context.py` | `AuthContext` - immutable context for decisions |
| `notifier.py` | `ToolRejectionNotifier` - handles rejections |
| `factory.py` | Creates default policy with all rules |

### Authorization Rules (Priority Order)

1. **ReadOnlyToolRule** (200) - Allows: `read_file`, `grep`, `list_dir`, `glob`, `react`, `research_codebase`
2. **TemplateAllowedToolsRule** (210) - Allows tools in active template's `allowed_tools`
3. **YoloModeRule** (300) - Bypasses ALL confirmations when `session.yolo = True`
4. **ToolIgnoreListRule** (310) - Bypasses tools in `session.tool_ignore` list

### Tool Execution Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│ 1. app.py:130 - process_request() with tool_callback                   │
│    ↓                                                                    │
│ 2. main.py:390 - _process_node() with tool_callback                    │
│    ↓                                                                    │
│ 3. node_processor.py:265 - Categorize tools:                           │
│    • part.tool_name in READ_ONLY_TOOLS → read_only_tasks               │
│    • else → write_execute_tasks                                        │
│    ↓                                                                    │
│ 4. node_processor.py:335 - For write tools: await tool_callback(part)  │
│    ↓                                                                    │
│ 5. app.py:269 - tool_handler.should_confirm(part.tool_name)            │
│    ↓                                                                    │
│ 6. If True: Show ToolConfirmationModal                                 │
│    If False: Return early (skip confirmation)                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Key Files for Permission Check

| Location | Line | Function |
|----------|------|----------|
| `ui/app.py` | 264-281 | `build_textual_tool_callback()` |
| `ui/app.py` | 269 | `tool_handler.should_confirm(part.tool_name)` |
| `ui/app.py` | 180-188 | `request_tool_confirmation()` |
| `ui/screens/confirmation.py` | 28-60 | `ToolConfirmationModal` |
| `tools/authorization/handler.py` | 44-46 | `should_confirm()` |
| `tools/authorization/policy.py` | 15-19 | Policy evaluation loop |
| `core/agents/agent_components/node_processor.py` | 322-338 | Write tool execution |

### Potential Root Causes

#### 1. YOLO Mode Accidentally Enabled
**Location:** `core/state.py:43`
```python
yolo: bool = False  # Default is OFF
```
The `/yolo` command toggles this. If enabled, ALL tools bypass confirmation.

**Check:** Print `state_manager.session.yolo` during tool execution.

#### 2. Tool Name Type Mismatch
**Issue:** `part.tool_name` (string from pydantic-ai) vs `ToolName` (enum in rules)

`ToolName` extends `str`, so comparisons *should* work:
```python
"bash" == ToolName.BASH  # True
"bash" in [ToolName.READ_FILE, ...]  # Should work
```

**Risk:** If pydantic-ai returns tool names differently than expected (e.g., prefixed or modified), the comparison could fail.

#### 3. Callback Not Being Called for Write Tools
**Location:** `node_processor.py:322-338`

Write tools should go through the sequential loop:
```python
for part, node in write_execute_tasks:
    ...
    await tool_callback(part, node)  # Line 335
```

**Risk:** If `write_execute_tasks` is empty (tools incorrectly categorized), callback won't run.

#### 4. Modal Display Issue
**Location:** `ui/app.py:180-197`

The modal uses Textual's async message passing:
1. `post_message(ShowToolConfirmationModal(request=request))`
2. `on_show_tool_confirmation_modal()` calls `push_screen()`
3. `on_tool_confirmation_result()` resolves the Future

**Risk:** If message handling fails silently, modal won't appear.

#### 5. Exception Swallowing in Parallel Execution
**Location:** `tool_executor.py:31-36`

```python
async def execute_with_error_handling(part, node):
    try:
        return await callback(part, node)
    except Exception as e:
        logger.error(f"Error executing parallel tool: {e}", exc_info=True)
        return e  # Returns exception instead of raising!
```

**Impact:** Only affects read-only tools (parallel execution), not write tools (sequential).

### Recent Changes Analysis

| Commit | Description | Risk |
|--------|-------------|------|
| `b4a0902` | Remove cli/, update entry point to ui.main | Refactored but logic preserved |
| `e856737` | feat(ui): add tooling | Added tool_start_callback, no logic changes |
| `17f4bb6` | Major UI reorganization | Created authorization module |

The `build_textual_tool_callback` implementation is **identical** before and after refactoring.

## Key Patterns / Solutions Found

### Debug Steps
1. Add logging in `build_textual_tool_callback`:
   ```python
   async def _callback(part: Any, _node: Any = None) -> None:
       print(f"DEBUG: tool_callback called for {part.tool_name}")
       ...
       should_confirm_result = tool_handler.should_confirm(part.tool_name)
       print(f"DEBUG: should_confirm={should_confirm_result}")
   ```

2. Check YOLO mode:
   ```python
   print(f"YOLO mode: {state_manager.session.yolo}")
   ```

3. Check tool ignore list:
   ```python
   print(f"Ignored tools: {state_manager.session.tool_ignore}")
   ```

4. Verify tool categorization in `node_processor.py:265`:
   ```python
   print(f"Tool {part.tool_name} in READ_ONLY_TOOLS: {part.tool_name in READ_ONLY_TOOLS}")
   ```

## Knowledge Gaps

1. **Actual tool name format** from pydantic-ai - need to log `part.tool_name` to verify
2. **Session state persistence** - is YOLO mode being saved/restored unexpectedly?
3. **Textual message handling** - is `ShowToolConfirmationModal` being received?

## Recommended Next Steps

1. **Add debug logging** to `build_textual_tool_callback` to trace execution
2. **Verify tool categorization** - log which list each tool goes into
3. **Check YOLO state** at startup and before tool execution
4. **Test with fresh session** to rule out persisted state

## References

- `src/tunacode/ui/app.py:264-281` - Tool callback implementation
- `src/tunacode/tools/authorization/` - Authorization module
- `src/tunacode/core/agents/agent_components/node_processor.py:225-378` - Tool processing
- `src/tunacode/constants.py:61-70` - Tool categorization constants
- `src/tunacode/core/state.py:43` - YOLO mode default
