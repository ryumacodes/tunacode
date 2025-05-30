# How to Create New Tools in TunaCode

This guide outlines the steps and conventions for adding new tools to the TunaCode CLI agent system.

---

## 1. Core Principles
- **Base Classes:** All tools inherit from `BaseTool` (for error handling, UI integration, retry logic) or `FileBasedTool` (adds git tracking for undo).
- **Consistency:** Each tool implements `_execute(self, **kwargs)`, and integrates seamlessly via the agent interface (pydantic-ai).
- **Modularity:** UI/UX logic, tool logic, and agent integration are kept separate for testability and maintainability.

---

## 2. Tool Creation Steps
1. **Subclass the appropriate base** in `src/tunacode/tools/base.py`:
   - Use `BaseTool` for general tools
   - Use `FileBasedTool` for tools that alter files tracked by git

2. **Define Your Tool:**
```python
from .base import BaseTool

class MyCoolTool(BaseTool):
    name = "my_cool_tool"
    description = "What this tool does."

    def _execute(self, ...):
        # Your logic here
        return {...}
```
- Add all input arguments to `schema_extra` in the Pydantic model if needed.
- Include user-friendly error handling via BaseTool helpers.

3. **Add to Agent:**
- Update `src/tunacode/core/agents/main.py`, adding an instance of your tool to the `tools=[...]` list (wrapped in `Tool()`).

4. **Register CLI/Integration:**
- If the tool should be exposed to the user, add it to autocomplete or `/help` as necessary.
- For shell/file tools, ensure actions are tracked for undo in `FileBasedTool`.

---

## 3. Tool Execution Flow
1. *Agent* generates tool call (using Pydantic schema)
2. *ToolHandler* checks for confirmation & invokes the tool
3. *ToolUI* prompts user (Yes/No/Skip/Abort)
4. *Tool's* `execute()` is called; output passed back to agent
5. *Undo* and *git integration* handled automatically for file tools

---

## 4. Best Practices
- **Be Atomic:** Tools should do one thing, well (easy to test/undo)
- **User Safety:** Leverage confirmation and error handling
- **Track File Changes:** Use `FileBasedTool` for editing/deleting files (enables `/undo`)
- **Retry-Friendly:** Support retries (idempotency recommended!)

---

## 5. Reference
- Base Classes: `src/tunacode/tools/base.py`
- Example Tools: `read_file.py`, `update_file.py`, `run_command.py`, `write_file.py`
- Agent Integration: `src/tunacode/core/agents/main.py`
- Tool Execution: `src/tunacode/cli/repl.py` (`_tool_handler`)
- UI: `src/tunacode/ui/tool_ui.py`

---

For further questions, check recent usage in the repo, and mimic style/conventions for easy review.