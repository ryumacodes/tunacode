# TunaCode Tools Documentation

This document provides comprehensive documentation for all tools available in the TunaCode CLI agent system.

## Overview

TunaCode provides a set of built-in tools that allow the AI agent to interact with the filesystem and execute commands. All tools follow a consistent architecture and provide safety features including user confirmation prompts and error handling.

## Architecture

### Base Classes

All tools inherit from one of two base classes:

- **`BaseTool`**: General-purpose tool base class with error handling, UI integration, and retry logic
- **`FileBasedTool`**: Specialized for file operations, extends `BaseTool` with enhanced file error handling

### Tool Execution Flow

1. **Agent Call**: The AI agent generates a tool call using Pydantic schema validation
2. **Confirmation**: ToolHandler checks for user confirmation (unless in "yolo mode")
3. **UI Prompt**: ToolUI shows the user what will be executed (Yes/No/Skip/Abort)
4. **Execution**: Tool's `execute()` method is called with validated parameters
5. **Response**: Output is formatted and returned to the agent

### Error Handling

Tools use structured error handling:
- **`ModelRetry`**: Guides the LLM when operations need correction or clarification
- **`ToolExecutionError`**: Structured errors with tool context and original exception details
- **File Operations**: Enhanced error context for file-related failures

## Available Tools

### 1. Bash Tool (`bash`)

**Purpose**: Enhanced shell command execution with advanced features

**Parameters**:
- `command` (string, required): The bash command to execute
- `cwd` (string, optional): Working directory for command execution
- `env` (dict, optional): Additional environment variables to set
- `timeout` (int, optional): Command timeout in seconds (default: 30, max: 300)
- `capture_output` (bool, optional): Whether to capture stdout/stderr (default: true)

**Features**:
- Working directory support for executing commands in specific locations
- Environment variable injection for custom execution contexts
- Configurable timeouts with automatic process termination
- Safety checks for potentially destructive commands (rm -rf, dd, etc.)
- Rich output formatting with exit codes, stdout, and stderr
- Intelligent error guidance for common failure patterns

**Output Format**:
```
Command: echo "hello"
Exit Code: 0
Working Directory: /path/to/cwd

STDOUT:
hello

STDERR:
(no errors)
```

**Safety Features**:
- Detects destructive command patterns and requires confirmation
- Validates working directories before execution
- Sanitizes environment variables
- Truncates overly long output to prevent system issues

**Example Usage**:
```python
# Basic command
await bash("ls -la")

# With working directory
await bash("npm install", cwd="/path/to/project")

# With environment variables
await bash("echo $MY_VAR", env={"MY_VAR": "test"})

# With timeout
await bash("long-running-command", timeout=60)
```

### 2. Read File Tool (`read_file`)

**Purpose**: Safe file reading with size limits and encoding handling

**Parameters**:
- `filepath` (string, required): Absolute path to the file to read

**Features**:
- File size validation (100KB limit) to prevent memory issues
- UTF-8 encoding with proper error handling for binary files
- Detailed error messages for common issues (file not found, encoding errors)

**Safety Features**:
- Size limits prevent reading huge files that could overwhelm the system
- Encoding detection and error reporting for non-text files
- Path validation and existence checking

**Example Usage**:
```python
content = await read_file("/path/to/file.txt")
```

### 3. Write File Tool (`write_file`)

**Purpose**: Create new files with conflict detection

**Parameters**:
- `filepath` (string, required): Path where the new file should be created
- `content` (string, required): Content to write to the file

**Features**:
- Prevents overwriting existing files (use `update_file` for modifications)
- Automatic directory creation for new file paths
- UTF-8 encoding for consistent text handling

**Safety Features**:
- Existence checking prevents accidental overwrites
- Directory creation ensures parent paths exist
- ModelRetry guidance when files already exist

**Example Usage**:
```python
await write_file("/path/to/new_file.txt", "Hello, world!")
```

### 4. Update File Tool (`update_file`)

**Purpose**: Modify existing files using target/patch pattern

**Parameters**:
- `filepath` (string, required): Path to the existing file to modify
- `target` (string, required): Exact text block to be replaced
- `patch` (string, required): New text block to insert in place of target

**Features**:
- Precise text replacement using exact string matching
- Single-occurrence replacement to prevent unintended changes
- Context-aware error messages when targets aren't found
- File existence validation before attempting updates

**Safety Features**:
- Exact matching prevents accidental replacements
- File existence checking before modification
- Context snippets help the LLM locate correct targets
- Validation that changes actually occurred

**Example Usage**:
```python
await update_file(
    "/path/to/file.py",
    target="def old_function():\n    pass",
    patch="def new_function():\n    return 'updated'"
)
```

### 5. Run Command Tool (`run_command`)

**Purpose**: Basic shell command execution with output capture

**Parameters**:
- `command` (string, required): Shell command to execute

**Features**:
- Simple command execution with stdout/stderr capture
- Output truncation for long results
- Basic error handling for command failures

**Output Format**:
```
STDOUT:
command output here

STDERR:
any errors here
```

**Note**: The `bash` tool is recommended over `run_command` for new implementations as it provides enhanced features and better error handling.

**Example Usage**:
```python
result = await run_command("ls -la")
```

## Tool Development Guidelines

### Creating New Tools

1. **Choose Base Class**:
   - Use `BaseTool` for general operations (commands, API calls, etc.)
   - Use `FileBasedTool` for file operations (enhanced error handling)

2. **Implement Required Methods**:
   ```python
   class MyTool(BaseTool):
       @property
       def tool_name(self) -> str:
           return "MyTool"

       async def _execute(self, **kwargs) -> ToolResult:
           # Your implementation here
           return "Success message"
   ```

3. **Register with Agent**:
   - Add import to `src/tunacode/core/agents/main.py`
   - Add `Tool(your_function, max_retries=max_retries)` to agent tools list

4. **Error Handling**:
   - Use `ModelRetry` for guidance that helps the LLM correct mistakes
   - Use structured error messages that provide actionable information
   - Include context about what the tool was trying to accomplish

### Best Practices

- **Atomicity**: Tools should perform one specific operation well
- **Safety**: Always validate inputs and provide confirmation for destructive operations
- **Idempotency**: Tools should be safe to retry without side effects
- **Error Context**: Provide clear, actionable error messages
- **Documentation**: Document parameters, behavior, and safety considerations

## Security Considerations

- All file operations require user confirmation unless in "yolo mode"
- Destructive commands trigger additional safety prompts
- Path validation prevents directory traversal attacks
- Environment variable sanitization prevents injection attacks
- File size limits prevent denial-of-service through large file operations

## Configuration

Tool behavior can be configured through:
- **User Configuration**: `~/.config/tunacode.json` for defaults
- **Session State**: Runtime permissions and settings
- **CLAUDE.md**: Project-specific guidance for tool usage
- **Command Line**: `/yolo` mode to skip confirmations

## External Tools

TunaCode also supports external tools through the Model Context Protocol (MCP):
- MCP servers can be configured to provide additional tools
- External tools integrate seamlessly with the built-in tool system
- See MCP documentation for setup and configuration details
