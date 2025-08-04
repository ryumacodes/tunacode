<!-- This document details the API for all tools: BaseTool class, tool implementations, and creating custom tools -->

# Tools API Reference

This document provides detailed API documentation for TunaCode's tool system.

## Base Classes

### BaseTool

`tunacode.tools.base.BaseTool`

Abstract base class for all tools.

```python
class BaseTool(ABC):
    """Base class for all TunaCode tools."""

    def __init__(self, ui: UIProtocol):
        """
        Initialize tool.

        Args:
            ui: UI protocol implementation for logging and display
        """
        self.ui = ui
        self.show_spinner = True  # Whether to show spinner during execution
```

#### Abstract Methods

##### run()
```python
@abstractmethod
async def run(self, **kwargs) -> str:
    """
    Execute the tool operation.

    Args:
        **kwargs: Tool-specific arguments

    Returns:
        str: Result message for the agent

    Raises:
        ModelRetry: For retryable errors
        Exception: For non-retryable errors
    """
```

##### format_confirmation()
```python
@abstractmethod
def format_confirmation(self, **kwargs) -> ConfirmationInfo:
    """
    Format confirmation prompt for user.

    Args:
        **kwargs: Tool-specific arguments

    Returns:
        ConfirmationInfo: Structured confirmation data
    """
```

#### Protected Methods

##### _handle_error()
```python
async def _handle_error(self, e: Exception, context: str) -> str:
    """
    Unified error handling.

    Args:
        e: Exception that occurred
        context: Context description for error message

    Returns:
        str: Formatted error message

    Raises:
        ModelRetry: If error is retryable

    Example:
        >>> return await self._handle_error(e, "reading file")
    """
```

### FileBasedTool

`tunacode.tools.base.FileBasedTool`

Base class for file-related tools.

```python
class FileBasedTool(BaseTool):
    """Base class for tools that operate on files."""
```

#### Protected Methods

##### _validate_path()
```python
def _validate_path(self, file_path: str) -> Path:
    """
    Validate and resolve file path.

    Args:
        file_path: Path string to validate

    Returns:
        Path: Resolved absolute path

    Raises:
        ValueError: If path is invalid

    Example:
        >>> path = self._validate_path("../file.txt")
    """
```

##### _read_file_with_encoding()
```python
async def _read_file_with_encoding(self, path: Path) -> str:
    """
    Read file with automatic encoding detection.

    Args:
        path: Path to file

    Returns:
        str: File contents

    Note:
        Tries UTF-8 first, falls back to chardet detection.
    """
```

## Tool Implementations

### ReadFileTool

`tunacode.tools.read_file.ReadFileTool`

```python
class ReadFileTool(FileBasedTool):
    """Read file contents with line numbers."""

    async def run(self, file_path: str) -> str:
        """
        Read a file and return contents with line numbers.

        Args:
            file_path: Path to file to read

        Returns:
            str: File contents with line numbers

        Example:
            >>> result = await tool.run(file_path="main.py")
            '     1  import asyncio\n     2  \n     3  async def main():'
        """
```

### WriteFileTool

`tunacode.tools.write_file.WriteFileTool`

```python
class WriteFileTool(FileBasedTool):
    """Create new files with content."""

    async def run(self, file_path: str, content: str) -> str:
        """
        Create a new file with content.

        Args:
            file_path: Path where to create file
            content: Content to write

        Returns:
            str: Success message

        Raises:
            ModelRetry: If file already exists

        Example:
            >>> await tool.run(
            ...     file_path="hello.py",
            ...     content="print('Hello, World!')"
            ... )
        """
```

### UpdateFileTool

`tunacode.tools.update_file.UpdateFileTool`

```python
class UpdateFileTool(FileBasedTool):
    """Update existing files with target/patch pattern."""

    async def run(
        self,
        file_path: str,
        target: str,
        new_content: str
    ) -> str:
        """
        Update file by replacing target with new content.

        Args:
            file_path: Path to file to update
            target: Text to find and replace
            new_content: Replacement text

        Returns:
            str: Success message

        Raises:
            ModelRetry: If target not found

        Example:
            >>> await tool.run(
            ...     file_path="config.py",
            ...     target="DEBUG = False",
            ...     new_content="DEBUG = True"
            ... )
        """
```

### BashTool

`tunacode.tools.bash.BashTool`

```python
class BashTool(BaseTool):
    """Execute bash commands with security validation."""

    async def run(self, command: str) -> str:
        """
        Execute a bash command.

        Args:
            command: Command to execute

        Returns:
            str: Command output (stdout + stderr)

        Raises:
            ModelRetry: If command fails validation

        Example:
            >>> output = await tool.run(command="ls -la")
        """
```

### GrepTool

`tunacode.tools.grep.GrepTool`

```python
class GrepTool(BaseTool):
    """Search file contents using regex patterns."""

    async def run(
        self,
        pattern: str,
        path: str = ".",
        file_pattern: Optional[str] = None
    ) -> str:
        """
        Search for pattern in files.

        Args:
            pattern: Regex pattern to search
            path: Directory or file to search
            file_pattern: Optional glob pattern for files

        Returns:
            str: Search results with file:line format

        Note:
            Has 3-second timeout for first match.

        Example:
            >>> results = await tool.run(
            ...     pattern="class.*Tool",
            ...     file_pattern="*.py"
            ... )
        """
```

### ListDirTool

`tunacode.tools.list_dir.ListDirTool`

```python
class ListDirTool(BaseTool):
    """List directory contents."""

    async def run(self, path: str = ".") -> str:
        """
        List directory contents.

        Args:
            path: Directory path to list

        Returns:
            str: Formatted directory listing

        Example:
            >>> listing = await tool.run(path="src/")
            '[DIR]  components/\n[FILE] main.py (1.2KB)'
        """
```

### GlobTool

`tunacode.tools.glob.GlobTool`

```python
class GlobTool(BaseTool):
    """Find files matching patterns."""

    async def run(
        self,
        pattern: str,
        path: str = "."
    ) -> str:
        """
        Find files matching glob pattern.

        Args:
            pattern: Glob pattern (e.g., "**/*.py")
            path: Base directory for search

        Returns:
            str: List of matching files

        Example:
            >>> files = await tool.run(pattern="tests/**/test_*.py")
        """
```

### TodoTool

`tunacode.tools.todo.TodoTool`

```python
class TodoTool(BaseTool):
    """Manage todo list items."""

    async def run(
        self,
        action: str,
        content: Optional[str] = None,
        id: Optional[int] = None,
        priority: str = "medium"
    ) -> str:
        """
        Manage todo items.

        Args:
            action: Action to perform (list, add, done, update, remove)
            content: Todo content (for add/update)
            id: Todo ID (for done/update/remove)
            priority: Priority level (high, medium, low)

        Returns:
            str: Operation result

        Example:
            >>> await tool.run(
            ...     action="add",
            ...     content="Implement new feature",
            ...     priority="high"
            ... )
        """
```

## Tool Configuration

### ConfirmationInfo

`tunacode.ui.tool_ui.ConfirmationInfo`

```python
@dataclass
class ConfirmationInfo:
    """Information for tool confirmation dialog."""

    tool_name: str
    short_description: str
    details: Optional[Dict[str, str]] = None
    preview: Optional[str] = None
    syntax: Optional[str] = None  # For syntax highlighting
    security_level: str = "medium"  # low, medium, high
```

### Tool Categories

`tunacode.configuration.settings`

```python
# Read-only tools (can execute in parallel)
READ_ONLY_TOOLS = ["read_file", "grep", "list_dir", "glob"]

# Tools that modify files
WRITE_TOOLS = ["write_file", "update_file", "todo"]

# Tools that execute commands
EXECUTE_TOOLS = ["run_command", "bash"]
```

## Creating Custom Tools

### Simple Tool Example

```python
from tunacode.tools.base import BaseTool
from tunacode.ui.tool_ui import ConfirmationInfo
from pydantic_ai import ModelRetry

class EchoTool(BaseTool):
    """Simple echo tool example."""

    async def run(self, message: str) -> str:
        """Echo the message back."""
        await self.ui.info(f"Echoing: {message}")
        return f"Echo: {message}"

    def format_confirmation(self, message: str) -> ConfirmationInfo:
        """Format confirmation."""
        return ConfirmationInfo(
            tool_name="echo",
            short_description=f"Echo message: {message}",
            security_level="low"
        )
```

### Advanced Tool Example

```python
class DataAnalysisTool(FileBasedTool):
    """Analyze data files."""

    async def run(
        self,
        file_path: str,
        analysis_type: str = "summary"
    ) -> str:
        """Analyze a data file."""
        # Validate path
        path = self._validate_path(file_path)

        if not path.exists():
            return f"Error: File not found: {file_path}"

        # Read file
        try:
            content = await self._read_file_with_encoding(path)
        except Exception as e:
            return await self._handle_error(e, f"reading {file_path}")

        # Perform analysis
        if analysis_type == "summary":
            result = self._summarize(content)
        elif analysis_type == "detailed":
            result = await self._detailed_analysis(content)
        else:
            raise ModelRetry(
                f"Unknown analysis type: {analysis_type}. "
                "Use 'summary' or 'detailed'"
            )

        return result

    def _summarize(self, content: str) -> str:
        """Create summary analysis."""
        lines = content.splitlines()
        return f"Summary: {len(lines)} lines, {len(content)} chars"

    async def _detailed_analysis(self, content: str) -> str:
        """Perform detailed analysis."""
        # Simulate async operation
        await asyncio.sleep(0.1)

        # Analysis logic
        word_count = len(content.split())
        unique_words = len(set(content.lower().split()))

        return f"""Detailed Analysis:
- Words: {word_count}
- Unique words: {unique_words}
- Average word length: {len(content) / word_count:.1f}"""

    def format_confirmation(
        self,
        file_path: str,
        analysis_type: str = "summary"
    ) -> ConfirmationInfo:
        """Format confirmation dialog."""
        return ConfirmationInfo(
            tool_name="data_analysis",
            short_description=f"Analyze {file_path}",
            details={
                "File": file_path,
                "Analysis Type": analysis_type,
                "Operation": "Read-only analysis"
            },
            security_level="low"
        )
```

## Tool Registration

### Adding to Settings

```python
# In tunacode/configuration/settings.py
INTERNAL_TOOLS = [
    # ... existing tools ...
    "echo",
    "data_analysis"
]

# Categorize appropriately
READ_ONLY_TOOLS = [
    # ... existing tools ...
    "data_analysis"  # Read-only tool
]
```

### Importing in Agent

```python
# In tunacode/core/agents/main.py
from tunacode.tools.echo import EchoTool
from tunacode.tools.data_analysis import DataAnalysisTool

# In create_agent function
tools = [
    # ... existing tools ...
    EchoTool(ui),
    DataAnalysisTool(ui),
]
```

## Error Handling Patterns

### Retryable Errors

```python
# Agent can retry with different parameters
if not valid_input:
    raise ModelRetry("Please provide valid input format")

if file_too_large:
    raise ModelRetry("File too large, please specify a smaller file")
```

### Non-Retryable Errors

```python
# Fatal errors that can't be fixed
if not authorized:
    return "Error: Permission denied"

if system_error:
    return await self._handle_error(e, "system operation")
```

### Error Context

```python
try:
    result = await dangerous_operation()
except SpecificError as e:
    # Provide context
    return await self._handle_error(
        e,
        f"performing operation on {file_path}"
    )
except Exception as e:
    # Generic handling
    return await self._handle_error(e, "unexpected error")
```

## Performance Considerations

### Parallel Execution

Tools in `READ_ONLY_TOOLS` can execute in parallel:

```python
# These will run concurrently
tasks = [
    read_tool.run(file_path="file1.py"),
    read_tool.run(file_path="file2.py"),
    grep_tool.run(pattern="TODO"),
]
results = await asyncio.gather(*tasks)
```

### Timeouts

```python
async def run(self, **kwargs) -> str:
    try:
        # Add timeout for long operations
        result = await asyncio.wait_for(
            self._long_operation(**kwargs),
            timeout=30.0
        )
        return result
    except asyncio.TimeoutError:
        return "Error: Operation timed out after 30 seconds"
```

### Resource Management

```python
class ResourceTool(BaseTool):
    async def run(self, **kwargs) -> str:
        # Use context managers
        async with aiofiles.open(file_path) as f:
            content = await f.read()
            # Process content
        # File automatically closed
        return "Success"
```
