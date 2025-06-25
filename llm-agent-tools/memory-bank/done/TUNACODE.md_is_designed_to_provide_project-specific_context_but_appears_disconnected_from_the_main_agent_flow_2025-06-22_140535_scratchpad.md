# Investigate why TUNACODE.md is not connected to the codeagent
_Started: 2025-06-22 14:00:48_

[1] Found that TUNACODE.md is defined in constants.py as GUIDE_FILE_NAME and get_code_style() in context.py reads all TUNACODE.md files up the directory tree
[2] Found that TUNACODE.md is a project guide file that users create in their project root to provide context to the AI assistant
[3] TUNACODE.md is loaded by get_code_style() in context.py which reads all TUNACODE.md files up the directory tree. However, the context module doesn't seem to be actively used in the current implementation.
