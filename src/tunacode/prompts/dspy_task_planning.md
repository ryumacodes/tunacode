# DSPy Task Planning Prompt

This prompt is automatically generated and optimized by DSPy for TunaCode's complex task planning.

## Format

Given the fields `complex_request`, produce the fields `subtasks_with_tools`, `total_tool_calls`, `requires_todo`, `parallelization_opportunities`.

---

Follow the following format.

Complex Request: A complex task that needs breakdown
Reasoning: Let's think step by step in order to ${produce the answer}. We need to break this down into manageable subtasks...
Subtasks With Tools: JSON array of {task, tools, priority} objects
Total Tool Calls: Estimated total number of tool calls
Requires Todo: Whether todo tool should be used
Parallelization Opportunities: Number of parallel execution opportunities

---

## Learned Example (Selected by DSPy)

### Example: Authentication System Implementation
Complex Request: Implement user authentication system with JWT tokens
Reasoning: Let's think step by step. This is a complex implementation task that requires multiple components. First, I need to analyze the current application structure to understand how to integrate authentication. Then I'll design the user model and database schema. Next, I'll create the authentication endpoints for registration and login. I'll need to implement JWT token generation and validation. Finally, I'll add tests to ensure everything works correctly. Several of these tasks can be done in parallel once the initial analysis is complete.
Subtasks With Tools: [{"task": "Analyze current app structure", "tools": ["list_dir", "grep", "read_file"], "priority": "high"}, {"task": "Design user model", "tools": ["write_file"], "priority": "high"}, {"task": "Create auth endpoints", "tools": ["write_file", "update_file"], "priority": "high"}, {"task": "Add JWT tokens", "tools": ["write_file", "grep"], "priority": "high"}, {"task": "Write tests", "tools": ["write_file", "run_command"], "priority": "medium"}]
Total Tool Calls: 15
Requires Todo: true
Parallelization Opportunities: 3

---

## Key Patterns for Complex Tasks

1. **Break Down First**: Start with analysis/exploration before implementation
2. **Priority Levels**: High for core functionality, medium for tests/docs, low for nice-to-haves
3. **Tool Grouping**: Group related tools together for each subtask
4. **Todo Usage**: Use todo tool for tasks with 5+ subtasks
5. **Parallelization**: Identify independent subtasks that can run concurrently

---

Complex Request: ${complex_request}
Reasoning: Let's think step by step...