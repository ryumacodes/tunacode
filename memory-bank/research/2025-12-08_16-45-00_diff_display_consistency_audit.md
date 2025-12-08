# Research - Diff Display Consistency Audit for Editing Tools

**Date:** 2025-12-08
**Owner:** Claude Code Assistant
**Phase:** Research
**Tags:** [diff-display, tool-authorization, ui-consistency, nextstep-ui, approval-flow]

## Goal

Audit all tools that edit/write/modify content to ensure they show a diff to the user before approval, consistent with recent work done on the `update_file` tool.

## Findings

### Editing Tools Inventory

| Tool | Type | Shows Diff on Approval? | Shows Diff on Result? | Gap? |
|------|------|------------------------|----------------------|------|
| `update_file` | File patch/edit | YES | YES | NO |
| `write_file` | New file creation | NO | NO | **YES** |
| `bash` | Shell execution | NO | NO | **PARTIAL** |

### Tool-by-Tool Analysis

#### 1. `update_file` - COMPLIANT
- **File:** `src/tunacode/tools/update_file.py`
- **Behavior:** Patches existing files with fuzzy text matching
- **Approval Diff:** YES - `ConfirmationRequestFactory` generates preview diff at `src/tunacode/tools/authorization/requests.py:17-40`
- **Result Diff:** YES - Returns unified diff in result string, rendered via `render_diff_tool()` at `src/tunacode/ui/renderers/panels.py:158-206`
- **Implementation:** Uses `difflib.unified_diff()` with git-style headers

#### 2. `write_file` - **GAP IDENTIFIED**
- **File:** `src/tunacode/tools/write_file.py`
- **Behavior:** Creates new files (fails if file exists)
- **Approval Diff:** NO - Only shows `filepath` and `content` args in approval prompt
- **Result Diff:** NO - Returns only `"Successfully wrote to new file: {filepath}"`
- **Gap:** User cannot see WHAT content will be written before approving
- **Severity:** HIGH - Violates NeXTSTEP "User Informed" principle

#### 3. `bash` - **PARTIAL GAP**
- **File:** `src/tunacode/tools/bash.py`
- **Behavior:** Executes shell commands (can modify files indirectly)
- **Approval Diff:** NO - Shows command string only
- **Result Diff:** NO - Shows stdout/stderr output
- **Gap:** Commands like `echo "..." > file` or `sed -i` modify files without diff
- **Severity:** MEDIUM - Not always editing files, but when it does, no preview
- **Note:** May be acceptable for bash since it's a general-purpose tool

### Authorization Flow Analysis

**Current Flow (from `src/tunacode/tools/authorization/`):**

1. `ToolHandler.should_confirm()` checks if confirmation needed
2. `ConfirmationRequestFactory.create()` builds request with optional diff
3. UI displays confirmation at `src/tunacode/ui/app.py:424-471`
4. Diff shown ONLY if `request.diff_content` is not None

**Diff Generation Entry Point:**
```python
# src/tunacode/tools/authorization/requests.py:17-40
if tool_name == ToolName.UPDATE_FILE and Path(filepath).exists():
    # Generate diff preview
    diff_content = unified_diff(original, new_content, ...)
```

**Key Observation:** Only `update_file` has diff generation logic. The factory needs extension for `write_file`.

### UI Rendering Analysis

**Smart Router at `src/tunacode/ui/renderers/panels.py:476-531`:**

- Detects diff content by markers: `"\n--- a/"` and `"\n+++ b/"`
- Routes to `render_diff_tool()` for syntax-highlighted display
- Falls back to basic `tool_panel()` for other tools

**Confirmation Display at `src/tunacode/ui/app.py:443-449`:**
```python
if request.diff_content:
    content_parts.append(Text("\nPreview changes:\n", style="bold"))
    content_parts.append(
        Syntax(request.diff_content, "diff", theme="monokai", word_wrap=True)
    )
```

### Key Patterns / Solutions Found

1. **Pattern: Marker-Based Diff Detection**
   - UI detects unified diff by `--- a/` and `+++ b/` markers
   - Tool-agnostic: any tool returning this format gets diff rendering

2. **Pattern: Message + Diff Concatenation**
   - `update_file` returns: `"Success message\n\n{diff_text}"`
   - UI splits at `"\n--- a/"` boundary
   - Clean separation for display

3. **Pattern: Pre-execution Preview**
   - `ConfirmationRequestFactory` simulates tool execution to generate preview
   - Uses same fuzzy matching logic as actual tool

4. **Solution: Extend Factory for write_file**
   - Add case for `write_file` in `requests.py`
   - Show content as syntax-highlighted code block (not diff)
   - Use language detection based on file extension

## Knowledge Gaps

1. **Language Detection:** How to detect syntax highlighting language from filepath?
   - Rich's `Syntax.guess_lexer()` may work
   - Or maintain extension-to-lexer mapping

2. **Content Truncation:** How much content is safe to show in approval?
   - Current `MAX_CALLBACK_CONTENT = 50_000` may be too large
   - Need sensible preview limit for write_file

3. **Bash Diff Handling:** Should bash commands that write files show diffs?
   - Requires parsing command to detect file writes
   - May be over-engineering for a general-purpose tool

## Proposed Solutions

### Priority 1: write_file Approval Preview (HIGH)

**Location:** `src/tunacode/tools/authorization/requests.py`

**Implementation:**
```python
if tool_name == ToolName.WRITE_FILE:
    content = args.get("content", "")
    filepath = args.get("filepath", "")
    # Show content with syntax highlighting
    lexer = Syntax.guess_lexer(filepath) or "text"
    preview = f"New file content:\n```{lexer}\n{content}\n```"
    return ToolConfirmationRequest(
        tool_name=tool_name,
        args=args,
        diff_content=None,
        preview_content=preview  # New field needed
    )
```

**UI Change:** `app.py:443-449` needs to handle `preview_content` in addition to `diff_content`

### Priority 2: write_file Result Display (MEDIUM)

**Location:** `src/tunacode/ui/renderers/panels.py:476-531`

**Implementation:**
- Add case in `tool_panel_smart()` for `write_file`
- Show syntax-highlighted content in result panel
- Requires `write_file` to return content in result (currently doesn't)

### Priority 3: bash File Write Detection (LOW)

**Complexity:** High - requires command parsing
**Recommendation:** Document as known limitation, not implement

## References

- `src/tunacode/tools/update_file.py` - Reference implementation for diff
- `src/tunacode/tools/write_file.py:34` - Current simple return
- `src/tunacode/tools/authorization/requests.py:10-44` - Factory to extend
- `src/tunacode/ui/app.py:443-449` - Confirmation diff display
- `src/tunacode/ui/renderers/panels.py:158-206` - `render_diff_tool()`
- `src/tunacode/ui/renderers/panels.py:476-531` - Smart router
- `memory-bank/research/2025-12-06_22-01-23_edit_tool_diff_display_research.md` - Prior research

## Summary

**Primary Gap:** `write_file` tool does not show content preview before approval or in result.

**Root Cause:** `ConfirmationRequestFactory` only handles `update_file`, and `write_file` returns minimal result.

**Recommended Fix:**
1. Extend `ConfirmationRequestFactory` to preview `write_file` content
2. Add `preview_content` field to `ToolConfirmationRequest`
3. Update UI to render preview (syntax-highlighted, not diff format)
4. Optionally: Update `write_file` to return content in result for post-execution display

**Effort Estimate:** Small - focused changes to 3-4 files
