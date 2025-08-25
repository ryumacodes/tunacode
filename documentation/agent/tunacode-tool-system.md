# TunaCode Tool System: Complete Technical Guide

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [How the Agent Knows to Use Tools](#how-the-agent-knows-to-use-tools)
3. [Tool Execution Flow](#tool-execution-flow)
4. [Complete Tool Reference](#complete-tool-reference)
5. [Advanced Topics](#advanced-topics)

## Architecture Overview

The TunaCode tool system is built on three key layers:

### 1. **pydantic-ai Integration Layer**
- Converts Python functions into tool schemas
- Sends schemas to LLM with each API request
- Processes LLM tool call responses back to Python

### 2. **Tool Definition Layer**
- XML prompt files define tool descriptions
- Python tool classes inherit from `BaseTool`
- Schema generation creates OpenAI-compatible format

### 3. **Execution Layer**
- Tool buffering for parallel execution
- Node processor handles tool calls
- Result management and error handling

## How the Agent Knows to Use Tools

### The Complete Flow

```
User Request
    ↓
Agent Creation (get_or_create_agent)
    ↓
Tools Registered with pydantic-ai
    ↓
API Request to LLM includes:
    - System Prompt (strategic guidance)
    - Tool Schemas (tactical details)
    - User Message
    ↓
LLM Response with tool_calls
    ↓
pydantic-ai extracts tool calls
    ↓
Node Processor routes to execution
```

### What the LLM Actually Receives

When pydantic-ai makes an API call, the LLM receives:

```json
{
  "messages": [
    {
      "role": "system",
      "content": "You are TunaCode... [full system prompt with tool categories and examples]"
    },
    {
      "role": "user",
      "content": "Find all Python files with class definitions"
    }
  ],
  "tools": [
    {
      "name": "grep",
      "description": "A powerful search tool built on ripgrep...",
      "parameters": {
        "type": "object",
        "properties": {
          "pattern": {"type": "string", "description": "regex pattern"},
          "path": {"type": "string", "description": "directory to search"}
        }
      }
    }
    // ... other tool schemas
  ]
}
```

### Tool Registration Code

```python
# From agent_config.py
tools_list = [
    Tool(bash, max_retries=max_retries),
    Tool(glob, max_retries=max_retries),
    Tool(grep, max_retries=max_retries),
    Tool(list_dir, max_retries=max_retries),
    Tool(read_file, max_retries=max_retries),
    Tool(run_command, max_retries=max_retries),
    Tool(todo_tool._execute, max_retries=max_retries),
    Tool(update_file, max_retries=max_retries),
    Tool(write_file, max_retries=max_retries),
]

agent = Agent(
    model=model,
    system_prompt=system_prompt,
    tools=tools_list,
    mcp_servers=get_mcp_servers(state_manager)
)
```

## Tool Execution Flow

### 1. **Tool Buffering Strategy**

```python
# Read-only tools are buffered
READ_ONLY_TOOLS = [
    "read_file",
    "grep",
    "list_dir",
    "glob",
    "exit_plan_mode"
]

# Write/execute tools trigger buffer flush
WRITE_TOOLS = ["write_file", "update_file"]
EXECUTE_TOOLS = ["bash", "run_command"]
```

### 2. **Parallel Execution**

When multiple read-only tools are called:

1. Tools are added to `ToolBuffer`
2. When a write/execute tool is encountered:
   - Buffer is flushed
   - Tools execute in parallel using `asyncio.gather()`
   - Results return in order
3. Write/execute tool runs sequentially

### 3. **Visual Flow Example**

```
Agent suggests: read A, grep B, read C, write D

1. Buffer: [read A]
2. Buffer: [read A, grep B]
3. Buffer: [read A, grep B, read C]
4. Hit write D → Flush buffer:
   - Execute A, B, C in parallel (350ms)
   - Then execute D sequentially
```

## Complete Tool Reference

### 1. **Read File Tool**

**Purpose**: Read file contents with line numbers

**Category**: Read-only (parallel-executable)

**Parameters**:
- `file_path` (required): Absolute path to file
- `offset` (optional): Line number to start from
- `limit` (optional): Number of lines to read

**Examples**:

```python
# Read entire file
read_file("/root/tunacode/src/main.py")

# Read specific portion
read_file("/root/tunacode/large.log", offset=1000, limit=500)

# Read image (multimodal)
read_file("/root/screenshot.png")
```

**Output**: Line-numbered content in `cat -n` format

### 2. **Grep Tool**

**Purpose**: Fast text search using ripgrep

**Category**: Read-only (parallel-executable)

**Parameters**:
- `pattern` (required): Regex pattern
- `path`: Directory/file to search
- `glob`: File pattern filter
- `type`: File type filter
- `output_mode`: "content", "files_with_matches", "count"
- `-i`: Case insensitive
- `-n`: Show line numbers
- `-A/-B/-C`: Context lines
- `multiline`: Cross-line patterns
- `head_limit`: Limit results

**Examples**:

```python
# Find all TODOs
grep("TODO")

# Case-insensitive Python search
grep("error", type="py", -i=True)

# Search with context
grep("def.*process", output_mode="content", -B=2, -A=2)

# Multiline struct search
grep("struct \\{[\\s\\S]*?field", multiline=True)
```

### 3. **Glob Tool**

**Purpose**: Find files by pattern

**Category**: Read-only (parallel-executable)

**Parameters**:
- `pattern` (required): Glob pattern
- `path`: Directory to search in

**Examples**:

```python
# All JavaScript files
glob("**/*.js")

# TypeScript in src
glob("src/**/*.ts")

# Test files
glob("**/*test*.py")

# Config files
glob("**/*.{json,yaml,yml,toml}")
```

### 4. **List Directory Tool**

**Purpose**: List directory contents

**Category**: Read-only (parallel-executable)

**Parameters**:
- `path` (required): Absolute directory path
- `ignore`: List of patterns to ignore

**Examples**:

```python
# List project root
list_dir("/root/tunacode")

# Ignore patterns
list_dir("/root/tunacode", ignore=["node_modules/**", "*.pyc"])
```

### 5. **Write File Tool**

**Purpose**: Create new files

**Category**: Write tool (sequential, requires confirmation)

**Parameters**:
- `file_path` (required): Absolute path
- `content` (required): File content

**Safety**: Fails if file exists (no overwrites)

**Examples**:

```python
# Create Python script
write_file("/root/tunacode/script.py", '''#!/usr/bin/env python3
print("Hello, World!")''')

# Create config
write_file("/root/tunacode/.env", '''DEBUG=true
PORT=3000''')
```

### 6. **Update File Tool**

**Purpose**: Modify existing files

**Category**: Write tool (sequential, requires confirmation)

**Parameters**:
- `file_path` (required): File to modify
- `old_string` (required): Text to find
- `new_string` (required): Replacement text
- `replace_all`: Replace all occurrences

**Examples**:

```python
# Single replacement
update_file("/root/config.py", "DEBUG = False", "DEBUG = True")

# Rename variable
update_file("/root/main.py", "old_var", "new_var", replace_all=True)

# Multi-line update
update_file("/root/utils.py",
    "def process(data):\\n    return data",
    "def process(data):\\n    # Process the data\\n    return data.strip()")
```

### 7. **Bash Tool**

**Purpose**: Execute shell commands with advanced features

**Category**: Execute tool (sequential, requires confirmation)

**Parameters**:
- `command` (required): Command to execute
- `description`: 5-10 word description
- `timeout`: Max milliseconds (default 120000)
- `run_in_background`: Run asynchronously

**Examples**:

```python
# Simple command
bash("ls -la", description="List all files")

# With timeout
bash("npm test", description="Run test suite", timeout=60000)

# Background process
bash("npm start", description="Start dev server", run_in_background=True)

# Multiple commands
bash("cd /root/project && npm install && npm build")
```

### 8. **Run Command Tool**

**Purpose**: Execute commands with environment control

**Category**: Execute tool (sequential, requires confirmation)

**Parameters**:
- `command` (required): Command to execute
- `cwd`: Working directory
- `env`: Environment variables
- `timeout`: Seconds (max 300)
- `capture_output`: Capture stdout/stderr

**Examples**:

```python
# With working directory
run_command("npm install", cwd="/root/project")

# With environment
run_command("python script.py", env={"PYTHONPATH": "/custom", "DEBUG": "true"})

# Extended timeout
run_command("make build", timeout=120)
```

### 9. **Todo Tool**

**Purpose**: Task management for complex work

**Category**: Task management

**Parameters**:
- `todos` (required): List of todo objects with:
  - `id`: Unique identifier
  - `content`: Task description
  - `status`: "pending", "in_progress", "completed"
  - `priority`: "high", "medium", "low"

**Examples**:

```python
# Create initial list
todo(todos=[
    {"id": "1", "content": "Analyze codebase", "status": "pending", "priority": "high"},
    {"id": "2", "content": "Design solution", "status": "pending", "priority": "high"},
    {"id": "3", "content": "Implement", "status": "pending", "priority": "medium"}
])

# Update progress
todo(todos=[
    {"id": "1", "content": "Analyze codebase", "status": "completed", "priority": "high"},
    {"id": "2", "content": "Design solution", "status": "in_progress", "priority": "high"},
    {"id": "3", "content": "Implement", "status": "pending", "priority": "medium"}
])
```

### 10. **Exit Plan Mode Tool**

**Purpose**: Exit planning mode to start implementation

**Category**: Read-only (special)

**Parameters**:
- `plan` (required): Markdown-formatted plan

**Example**:

```python
exit_plan_mode(plan='''## Implementation Plan

1. Create authentication middleware
2. Add user model and database schema
3. Implement login/logout endpoints
4. Add session management
5. Write tests for auth flow''')
```

### 11. **Present Plan Tool**

**Purpose**: Present plan for user approval

**Category**: Planning tool

**Parameters**:
- `plan` (required): Markdown plan

**Example**:

```python
present_plan(plan='''## Refactoring Plan

1. **Extract common logic** - Move duplicated code to utilities
2. **Update imports** - Adjust all import statements
3. **Run tests** - Ensure no functionality broken
4. **Update documentation** - Reflect new structure''')
```

## Advanced Topics

### Tool Decision Making

The agent decides which tools to use based on:

1. **System Prompt Rules**:
   - "When you say 'Let me...' you MUST execute the tool"
   - Tool categories and when to use each

2. **Task Analysis**:
   - "Find files" → glob
   - "Search content" → grep
   - "Read specific file" → read_file
   - "Explore structure" → list_dir

3. **Tool Descriptions**:
   - Each XML prompt file provides detailed guidance
   - Examples show common patterns

### Performance Optimization

**Parallel Execution Benefits**:
- 1 tool: ~300ms
- 3 tools sequential: ~900ms
- 3 tools parallel: ~350ms (2.5x faster!)

**Optimal Patterns**:
```python
# Good: Batch related reads
files = glob("**/*.py")
read_file("main.py")
read_file("utils.py")
grep("import", "src/")

# Bad: Interleaving reads and writes
read_file("a.py")
write_file("b.py", "...")  # Blocks parallelization
read_file("c.py")         # Can't parallelize with a.py
```

### Error Handling

Tools handle errors gracefully:

1. **ModelRetry**: Guides the LLM to fix issues
2. **ToolExecutionError**: Structured error information
3. **Validation**: Tools validate parameters before execution

### Tool Chaining Patterns

**Investigation Flow**:
```python
grep("error", "logs/") → read_file("logs/error.log") →
grep("ValueError", "src/") → read_file("src/validator.py")
```

**Implementation Flow**:
```python
todo(create tasks) → read_file(understand) →
write_file(implement) → bash("run tests")
```

### Security Considerations

1. **Path Restrictions**: Must use absolute paths
2. **Confirmation Required**: All writes/executes need approval
3. **Output Limits**: Prevent infinite output (30KB max)
4. **Timeout Protection**: Commands auto-terminate

## Conclusion

The TunaCode tool system combines:
- **pydantic-ai** for LLM integration
- **XML prompts** for detailed guidance
- **Parallel execution** for performance
- **Safety checks** for user protection

This architecture enables the agent to understand available tools, decide when to use them, and execute efficiently while maintaining safety and clarity.
