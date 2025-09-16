Delegates a complex, self-contained task to a specialized subagent.

**When to use:**
- Use this tool to offload work that requires independent analysis, exploration, or a multi-step execution handled by an autonomous expert.

**When not to use:**
- For simple, direct actions. If a task can be accomplished with a single, more specific tool, use that instead. This tool is for complex, multi-step operations that benefit from a dedicated agent's logic.
- Example: If you need to read the contents of a specific, known file path, use the `read_file` tool directly. Do not delegate this simple action to a subagent.
- Example: If you are searching for a specific string in the codebase, use the `grep` tool. The `task` tool would be overkill.

**Guidelines for usage:**
- Autonomous & Isolated: Subagents operate independently. Once a task is delegated, you cannot communicate with it further. It will perform its work and return a single, final report.
- The Prompt is the Contract: Your `prompt` must be exceptionally detailed. Include all necessary context, steps to perform, and the exact format for the desired output. The subagent's success depends entirely on the quality of your prompt.
- Process the Output: The subagent's result is returned only to you (the main agent), not the user. You are responsible for interpreting this result and presenting a summary or the relevant information to the user.
- Parallel Execution: To maximize efficiency, delegate multiple independent tasks to different subagents concurrently within a single turn.

**Available subagents:**
- `explorer`: Use this subagent to survey the current project directory. It analyzes file and folder structures, identifies the tech stack (languages, frameworks, dependencies), and provides a high-level summary of the project's architecture and purpose. It is ideal for gaining initial understanding of a new codebase.
- `coder`: Use this subagent to do general coding and code review. Especially useful for fixing compilation errors and refactoring code.
