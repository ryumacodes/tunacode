# DSPy Tool Selection Prompt

This prompt is automatically generated and optimized by DSPy for TunaCode's tool selection.

## Format

Given the fields `user_request`, `current_directory`, produce the fields `tools_json`, `requires_confirmation`, `reasoning`.

---

Follow the following format.

User Request: The user's request or task
Current Directory: Current working directory context
Reasoning: Let's think step by step in order to ${produce the answer}. We ...
Tools Json: JSON array of tool calls with batch grouping, e.g. [[tool1, tool2, tool3], [tool4]]
Requires Confirmation: Whether any tools require user confirmation

---

## Learned Examples (Automatically Selected by DSPy)

### Example 1: Searching for Implementation
User Request: Show me the authentication system implementation
Current Directory: .
Reasoning: Let's think step by step. To show the authentication implementation, I need to search for auth-related files across the codebase. I'll use grep to find files containing 'auth', list the auth directory if it exists, and use glob to find all auth-related Python files. These are all read-only operations that can be executed in parallel.
Tools Json: [["grep(\"auth\", \"src/\")", "list_dir(\"src/auth/\")", "glob(\"**/*auth*.py\")"]]
Requires Confirmation: false

### Example 2: Reading Multiple Files (Optimal Batching)
User Request: Read all config files and the main module  
Current Directory: .
Reasoning: Let's think step by step. I need to read multiple specific files. All of these are read operations that can be batched together for parallel execution. I'll batch them in a group of 4 for optimal performance.
Tools Json: [["read_file(\"config.json\")", "read_file(\"settings.py\")", "read_file(\".env\")", "read_file(\"main.py\")"]]
Requires Confirmation: false

### Example 3: Search, Read, then Modify Pattern
User Request: Find the bug in validation and fix it
Current Directory: .
Reasoning: Let's think step by step. First, I need to search for validation-related code and errors. I'll use grep to search for error patterns and validation code, and list the validators directory. These search operations can be parallelized. After finding the issue, I'll need to read the specific file and then update it to fix the bug.
Tools Json: [["grep(\"error\", \"logs/\")", "grep(\"validation\", \"src/\")", "list_dir(\"src/validators/\")"], ["read_file(\"src/validators/user.py\")"], ["update_file(\"src/validators/user.py\", \"old\", \"new\")"]]
Requires Confirmation: true

---

## Key Patterns Learned by DSPy

1. **3-4 Tool Batching**: Optimal batch size for parallel read-only operations
2. **Read-Only Parallelization**: grep, list_dir, glob, read_file can run in parallel
3. **Sequential Writes**: write_file, update_file, run_command, bash must run sequentially
4. **Confirmation Required**: Any write/execute operation needs confirmation
5. **Search → Read → Modify**: Common pattern for debugging and fixes

---

User Request: ${user_request}
Current Directory: ${current_directory}
Reasoning: Let's think step by step...