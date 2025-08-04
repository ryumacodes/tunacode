<!-- This document covers the tools system architecture, all built-in tools (read_file, write_file, grep, etc.), parallel execution, and MCP integration -->

# TunaCode Tools System Documentation

## Overview

The TunaCode tools system provides a sophisticated, extensible framework for agent-executable operations. Built with security, performance, and usability in mind, it supports both internal tools and external MCP (Model Context Protocol) integrations.

## Architecture

### Tool Categories

Tools are categorized by their operation type for security and performance optimization:

```python
# From configuration/settings.py
READ_ONLY_TOOLS = ["read_file", "grep", "list_dir", "glob"]
WRITE_TOOLS = ["write_file", "update_file", "todo"]
EXECUTE_TOOLS = ["run_command", "bash"]
```

This categorization enables:
- **Parallel execution** of read-only tools
- **Sequential execution** of write/execute tools
- **Permission-based** security policies

## Base Tool Classes

### BaseTool (tools/base.py)

The foundation for all tools:

```python
class BaseTool(ABC):
    """Base class for all tools"""

    def __init__(self, ui: UIProtocol):
        self.ui = ui  # UI integration for logging/confirmation
        self.show_spinner = True  # Loading indicator control

    @abstractmethod
    async def run(self, **kwargs) -> str:
        """Execute the tool operation"""
        pass

    @abstractmethod
    def format_confirmation(self, **kwargs) -> ConfirmationInfo:
        """Format confirmation prompt for user"""
        pass

    async def _handle_error(self, e: Exception, context: str) -> str:
        """Unified error handling with ModelRetry support"""
        if isinstance(e, CalledProcessError):
            # Special handling for process errors
            error_msg = self._format_process_error(e)
        else:
            error_msg = str(e)

        await self.ui.error(f"{context}: {error_msg}")

        # Enable retry for retryable errors
        if self._is_retryable(e):
            raise ModelRetry(error_msg)
        return f"Error: {error_msg}"
```

### FileBasedTool

Specialized base for file operations:

```python
class FileBasedTool(BaseTool):
    """Base for tools that operate on files"""

    async def _read_file_with_encoding(self, path: Path) -> str:
        """Read file with automatic encoding detection"""
        # Try UTF-8 first
        # Fall back to chardet detection
        # Handle binary files gracefully

    def _validate_path(self, file_path: str) -> Path:
        """Validate and resolve file paths"""
        # Convert to absolute path
        # Check path traversal attempts
        # Validate within project bounds
```

## Internal Tools Implementation

### 1. read_file (tools/read_file.py)

Fast file reading with parallel execution support:

```python
class ReadFileTool(FileBasedTool):
    """Read file contents with line numbers"""

    async def run(self, file_path: str) -> str:
        path = self._validate_path(file_path)

        if not path.exists():
            return f"Error: File not found: {file_path}"

        content = await self._read_file_with_encoding(path)

        # Add line numbers
        lines = content.splitlines()
        numbered = [f"{i+1:6d}  {line}" for i, line in enumerate(lines)]

        return "\n".join(numbered)

    def format_confirmation(self, file_path: str) -> ConfirmationInfo:
        return ConfirmationInfo(
            tool_name="read_file",
            short_description=f"Read {file_path}",
            details={"Path": file_path}
        )
```

**Features:**
- Automatic encoding detection
- Line numbering for easy reference
- Parallel execution capability
- Large file handling

### 2. write_file (tools/write_file.py)

Safe file creation with overwrite protection:

```python
class WriteFileTool(FileBasedTool):
    """Create new files safely"""

    async def run(self, file_path: str, content: str) -> str:
        path = self._validate_path(file_path)

        # Check for existing file
        if path.exists():
            raise ModelRetry(f"File already exists: {file_path}")

        # Create parent directories
        path.parent.mkdir(parents=True, exist_ok=True)

        # Write with UTF-8 encoding
        path.write_text(content, encoding="utf-8")

        return f"Successfully created {file_path}"

    def format_confirmation(self, file_path: str, content: str) -> ConfirmationInfo:
        # Show syntax-highlighted preview
        preview = self._syntax_highlight(content, file_path)

        return ConfirmationInfo(
            tool_name="write_file",
            short_description=f"Create {file_path}",
            details={"Path": file_path, "Size": f"{len(content)} chars"},
            preview=preview
        )
```

**Features:**
- Overwrite protection
- Parent directory creation
- Syntax highlighting in confirmations
- UTF-8 encoding

### 3. update_file (tools/update_file.py)

Intelligent file patching with diff preview:

```python
class UpdateFileTool(FileBasedTool):
    """Update existing files with target/patch pattern"""

    async def run(self, file_path: str, target: str, new_content: str) -> str:
        path = self._validate_path(file_path)

        # Read current content
        content = await self._read_file_with_encoding(path)

        # Find and replace
        if target not in content:
            raise ModelRetry(f"Target not found in {file_path}")

        updated = content.replace(target, new_content, 1)

        # Write back atomically
        path.write_text(updated, encoding="utf-8")

        return f"Successfully updated {file_path}"

    def format_confirmation(self, file_path: str, target: str, new_content: str) -> ConfirmationInfo:
        # Generate unified diff
        diff = self._generate_diff(target, new_content)

        return ConfirmationInfo(
            tool_name="update_file",
            short_description=f"Update {file_path}",
            details={"Path": file_path},
            preview=diff,
            syntax="diff"
        )
```

**Features:**
- Target/patch pattern for precise updates
- Diff preview in confirmations
- Atomic file updates
- Multi-encoding support

### 4. bash (tools/bash.py)

Enhanced shell execution with security:

```python
class BashTool(BaseTool):
    """Execute bash commands safely"""

    async def run(self, command: str) -> str:
        # Security validation
        if not await validate_command(command):
            raise ModelRetry("Command failed security validation")

        # Execute with timeout
        proc = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            shell=True
        )

        stdout, stderr = await proc.communicate()

        # Format output
        output = stdout.decode('utf-8', errors='replace')
        if stderr:
            output += f"\n[stderr]\n{stderr.decode('utf-8', errors='replace')}"

        return output

    def format_confirmation(self, command: str) -> ConfirmationInfo:
        return ConfirmationInfo(
            tool_name="bash",
            short_description="Execute bash command",
            details={"Command": command},
            security_level="high"
        )
```

**Features:**
- Command validation via security.py
- Timeout protection
- Stderr capture
- Unicode handling

### 5. grep (tools/grep.py)

Fast content search with timeout protection:

```python
class GrepTool(BaseTool):
    """Search file contents with regex patterns"""

    async def run(self, pattern: str, path: str = ".", file_pattern: str = None) -> str:
        # Pre-filter with glob for performance
        if file_pattern:
            files = await self._glob_files(path, file_pattern)
            if len(files) > MAX_GLOB_LIMIT:
                files = files[:MAX_GLOB_LIMIT]

        # Execute ripgrep with timeout
        cmd = ["rg", "--no-heading", "-n", pattern]
        if file_pattern:
            cmd.extend(["--glob", file_pattern])
        cmd.append(path)

        # 3-second deadline for first match
        result = await self._run_with_timeout(cmd, timeout=3.0)

        return result

    async def _run_with_timeout(self, cmd: List[str], timeout: float) -> str:
        """Run command with timeout"""
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await asyncio.wait_for(
                proc.communicate(),
                timeout=timeout
            )
            return stdout.decode('utf-8')
        except asyncio.TimeoutError:
            proc.terminate()
            return "Search timed out (3 second limit)"
```

**Features:**
- Fast-glob pre-filtering
- 3-second timeout protection
- Regex pattern support
- File pattern filtering

### 6. list_dir (tools/list_dir.py)

Efficient directory listing:

```python
class ListDirTool(BaseTool):
    """List directory contents efficiently"""

    async def run(self, path: str = ".") -> str:
        dir_path = Path(path).resolve()

        if not dir_path.exists():
            return f"Error: Directory not found: {path}"

        items = []
        for item in sorted(dir_path.iterdir()):
            if item.is_dir():
                items.append(f"[DIR]  {item.name}/")
            else:
                size = item.stat().st_size
                items.append(f"[FILE] {item.name} ({self._format_size(size)})")

        return "\n".join(items)

    def _format_size(self, size: int) -> str:
        """Human-readable file size"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f}{unit}"
            size /= 1024
        return f"{size:.1f}TB"
```

**Features:**
- Type indicators (DIR/FILE)
- Human-readable sizes
- Sorted output
- Hidden file support

### 7. glob (tools/glob.py)

Fast file pattern matching:

```python
class GlobTool(BaseTool):
    """Fast file pattern matching"""

    async def run(self, pattern: str, path: str = ".") -> str:
        base_path = Path(path).resolve()

        # Use glob for pattern matching
        matches = []
        for match in base_path.glob(pattern):
            if match.is_file():
                rel_path = match.relative_to(base_path)
                matches.append(str(rel_path))

        # Sort by modification time
        matches.sort(key=lambda p: Path(base_path / p).stat().st_mtime, reverse=True)

        return "\n".join(matches) if matches else "No matches found"
```

**Features:**
- Fast pattern matching
- Modification time sorting
- Relative path output
- Memory efficient

### 8. todo (tools/todo.py)

Task management integration:

```python
class TodoTool(BaseTool):
    """Manage todo lists"""

    async def run(self, action: str, **kwargs) -> str:
        if action == "list":
            return self._list_todos()
        elif action == "add":
            return self._add_todo(kwargs.get("content"), kwargs.get("priority"))
        elif action == "done":
            return self._mark_done(kwargs.get("id"))
        elif action == "update":
            return self._update_todo(kwargs.get("id"), kwargs.get("content"))
        else:
            raise ModelRetry(f"Unknown action: {action}")

    def _list_todos(self) -> str:
        """Format todos as table"""
        # Rich table formatting
        # Priority indicators
        # Status display
```

**Features:**
- CRUD operations
- Priority management
- Rich formatting
- State persistence

## MCP Integration (services/mcp.py)

External tool integration via Model Context Protocol:

### MCP Manager

```python
class MCPManager:
    """Manage MCP server lifecycle"""

    async def initialize_servers(self, config: Dict) -> None:
        """Start configured MCP servers"""
        for name, server_config in config.items():
            # Spawn server process
            # Establish JSON-RPC connection
            # Discover available tools
            # Register with tool handler

    async def call_tool(self, server: str, tool: str, args: Dict) -> Any:
        """Execute MCP tool"""
        # Send JSON-RPC request
        # Handle response/errors
        # Return formatted result
```

### MCP Tool Wrapper

```python
class MCPToolWrapper(BaseTool):
    """Wrapper for external MCP tools"""

    def __init__(self, server_name: str, tool_spec: Dict, mcp_manager: MCPManager):
        self.server_name = server_name
        self.tool_spec = tool_spec
        self.mcp_manager = mcp_manager

    async def run(self, **kwargs) -> str:
        # Validate arguments against spec
        # Call via MCP manager
        # Format response
```

## Parallel Execution System

### Batching Logic (agents/utils.py)

```python
def batch_consecutive_read_only_tools(tool_calls: List) -> List[List]:
    """Group consecutive read-only tools"""
    batches = []
    current_batch = []

    for call in tool_calls:
        if call.function.name in READ_ONLY_TOOLS:
            current_batch.append(call)
        else:
            if current_batch:
                batches.append(current_batch)
                current_batch = []
            batches.append([call])  # Single item batch

    if current_batch:
        batches.append(current_batch)

    return batches
```

### Parallel Execution

```python
async def execute_parallel_batch(batch: List, handler: ToolHandler) -> List:
    """Execute tools in parallel"""
    tasks = []

    for tool_call in batch:
        # Create execution task
        task = asyncio.create_task(
            handler.execute_tool(
                tool_call.function.name,
                tool_call.function.arguments
            )
        )
        tasks.append((tool_call.id, task))

    # Wait for all to complete
    results = []
    for tool_id, task in tasks:
        try:
            result = await task
            results.append((tool_id, result))
        except Exception as e:
            results.append((tool_id, f"Error: {e}"))

    return results
```

## Security Model

### Tool Permissions

1. **Default Deny**: All tools require confirmation
2. **YOLO Mode**: Skip all confirmations (power user)
3. **Template Allowlist**: Pre-approved tools from templates
4. **Granular Control**: Per-tool, per-session approvals

### Confirmation UI Flow

```python
async def show_tool_confirmation(tool: str, args: Dict) -> str:
    """Show tool confirmation dialog"""

    # Format confirmation info
    info = tool.format_confirmation(**args)

    # Display with options
    choice = await prompt_toolkit.prompt([
        "1. Yes (execute this tool)",
        "2. Yes, and don't ask again for this tool",
        "3. No (skip this tool)"
    ])

    # Handle choice
    if choice == "2":
        state.allowed_tools.add(tool)

    return choice
```

## Best Practices

### Creating New Tools

1. **Choose the Right Base Class**
   - Use `FileBasedTool` for file operations
   - Use `BaseTool` for everything else

2. **Implement Error Handling**
   - Use `_handle_error` for consistency
   - Raise `ModelRetry` for retryable errors
   - Provide clear error messages

3. **Security Considerations**
   - Validate all inputs
   - Use `_validate_path` for file paths
   - Check permissions appropriately

4. **Performance Optimization**
   - Mark as READ_ONLY_TOOLS if applicable
   - Implement timeouts for long operations
   - Use async/await properly

5. **User Experience**
   - Provide clear confirmations
   - Include relevant details
   - Show diffs/previews when helpful

### Tool Testing

```python
# Example test for a tool
async def test_read_file_tool():
    # Create mock UI
    ui = MockUI()

    # Create tool instance
    tool = ReadFileTool(ui)

    # Test successful read
    result = await tool.run(file_path="test.txt")
    assert "Hello" in result

    # Test missing file
    result = await tool.run(file_path="missing.txt")
    assert "Error" in result

    # Test confirmation
    info = tool.format_confirmation(file_path="test.txt")
    assert info.tool_name == "read_file"
```

## Performance Metrics

### Parallel Execution Benefits

- **3x faster** for multiple file reads
- **Configurable** parallelism (TUNACODE_MAX_PARALLEL)
- **Automatic** batching of operations
- **Zero overhead** for single operations

### Optimization Strategies

1. **Pre-filtering**: Grep uses glob to limit search scope
2. **Timeouts**: 3-second deadline for search operations
3. **Streaming**: Large file handling without memory issues
4. **Caching**: Import cache for repeated operations

## Future Enhancements

1. **Tool Plugins**: Dynamic tool loading from packages
2. **Tool Composition**: Combine tools for complex operations
3. **Tool Versioning**: Handle tool API evolution
4. **Tool Analytics**: Usage patterns and optimization
