# Fix read-only tools permission prompts issue
_Started: 2025-06-21 10:33:28_

## Plan — 2025-06-21 10:33:38
1. Search for read-only tool implementations 2. Check permission handling logic 3. Verify tool confirmation flow 4. Test the fix

[1] Found read_only related code in multiple files - focusing on tool_handler.py and main.py
[2] Found READ_ONLY_TOOLS defined in constants.py includes read_file, grep, list_dir, glob
[3] Found ToolUI confirmation methods but need to see where they're called from in agent
[4] Found tool registration in main.py but need to find where tool confirmation happens
[5] Found confirmation check in repl.py line 102 - it should skip confirmation for read-only tools
[6] Issue identified: _tool_handler shows 'Tool(tool_name)' message before checking if confirmation is needed
[7] Fixed _tool_handler to only show Tool info message for tools that require confirmation
