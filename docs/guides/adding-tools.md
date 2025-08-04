<!-- This guide explains how to create new tools for the agent system, including tool architecture and registration -->

# Adding Tools to TunaCode

This guide explains how to create new tools for TunaCode's agent system. Tools are the primary way agents interact with the system, files, and external services.

## Tool Architecture Overview

Tools in TunaCode follow a consistent pattern:

1. Inherit from `BaseTool` or `FileBasedTool`
2. Implement required methods (`run` and `format_confirmation`)
3. Register in settings
4. Categorize for security and performance

## Step-by-Step Tool Creation

### Step 1: Choose the Base Class

```python
from tunacode.tools.base import BaseTool, FileBasedTool

# For general tools
class MyTool(BaseTool):
    pass

# For file-related tools
class MyFileTool(FileBasedTool):
    pass
```

### Step 2: Implement the Tool

Create your tool in `src/tunacode/tools/my_tool.py`:

```python
from typing import Any, Dict
from tunacode.tools.base import BaseTool
from tunacode.ui.tool_ui import ConfirmationInfo
from pydantic_ai import ModelRetry
import asyncio

class MyCustomTool(BaseTool):
    """
    A custom tool that does something useful.

    This tool demonstrates the key patterns for tool implementation.
    """

    async def run(self, **kwargs) -> str:
        """
        Execute the tool operation.

        Args:
            **kwargs: Tool-specific arguments from the agent

        Returns:
            str: Result message to return to the agent

        Raises:
            ModelRetry: For retryable errors
        """
        # Extract and validate arguments
        param1 = kwargs.get('param1')
        param2 = kwargs.get('param2', 'default')

        if not param1:
            raise ModelRetry("param1 is required")

        try:
            # Show spinner during operation (optional)
            if self.show_spinner:
                await self.ui.show_spinner("Processing...")

            # Perform the tool operation
            result = await self._do_operation(param1, param2)

            # Log success
            await self.ui.success(f"Operation completed: {result}")

            # Return result to agent
            return f"Successfully processed with result: {result}"

        except Exception as e:
            # Use unified error handling
            return await self._handle_error(e, "MyCustomTool operation")
        finally:
            # Hide spinner
            if self.show_spinner:
                await self.ui.hide_spinner()

    async def _do_operation(self, param1: str, param2: str) -> str:
        """Internal operation implementation"""
        # Simulate async operation
        await asyncio.sleep(0.1)
        return f"{param1} + {param2}"

    def format_confirmation(self, **kwargs) -> ConfirmationInfo:
        """
        Format confirmation prompt for user.

        Returns:
            ConfirmationInfo: Structured confirmation data
        """
        param1 = kwargs.get('param1', 'unknown')
        param2 = kwargs.get('param2', 'default')

        return ConfirmationInfo(
            tool_name="my_custom_tool",
            short_description=f"Process '{param1}' with option '{param2}'",
            details={
                "Parameter 1": param1,
                "Parameter 2": param2,
                "Impact": "This operation will do XYZ"
            },
            security_level="medium"  # low, medium, high
        )
```

### Step 3: File-Based Tool Example

For tools that work with files:

```python
from pathlib import Path
from tunacode.tools.base import FileBasedTool
from tunacode.ui.tool_ui import ConfirmationInfo
from pydantic_ai import ModelRetry

class FileAnalyzerTool(FileBasedTool):
    """Analyze file contents and provide insights"""

    async def run(self, file_path: str, analysis_type: str = "basic") -> str:
        """Analyze a file"""
        # Use inherited path validation
        path = self._validate_path(file_path)

        if not path.exists():
            return f"Error: File not found: {file_path}"

        if not path.is_file():
            return f"Error: Not a file: {file_path}"

        # Use inherited encoding-safe file reading
        try:
            content = await self._read_file_with_encoding(path)
        except Exception as e:
            return await self._handle_error(e, f"reading {file_path}")

        # Perform analysis
        if analysis_type == "basic":
            analysis = self._basic_analysis(content)
        elif analysis_type == "detailed":
            analysis = await self._detailed_analysis(content)
        else:
            raise ModelRetry(f"Unknown analysis type: {analysis_type}")

        return f"Analysis of {file_path}:\n{analysis}"

    def _basic_analysis(self, content: str) -> str:
        """Basic file analysis"""
        lines = content.splitlines()
        return f"""
- Lines: {len(lines)}
- Characters: {len(content)}
- Words: {len(content.split())}
- Empty lines: {sum(1 for line in lines if not line.strip())}
"""

    async def _detailed_analysis(self, content: str) -> str:
        """Detailed async analysis"""
        # Simulate complex async analysis
        await asyncio.sleep(0.5)

        # Add more detailed analysis
        basic = self._basic_analysis(content)

        # Check for patterns
        has_todos = "TODO" in content or "FIXME" in content
        has_functions = "def " in content or "function " in content

        return f"""{basic}
- Contains TODOs: {has_todos}
- Contains functions: {has_functions}
- File type: {Path(content).suffix or 'unknown'}
"""

    def format_confirmation(self, file_path: str, analysis_type: str = "basic") -> ConfirmationInfo:
        """Format confirmation for file analysis"""
        return ConfirmationInfo(
            tool_name="file_analyzer",
            short_description=f"Analyze {file_path}",
            details={
                "File": file_path,
                "Analysis Type": analysis_type,
                "Operation": "Read-only analysis"
            },
            security_level="low"  # Read-only operation
        )
```

### Step 4: Register the Tool

Add your tool to `src/tunacode/configuration/settings.py`:

```python
@dataclass(frozen=True)
class ApplicationSettings:
    # ... existing code ...

    # Add to internal tools list
    INTERNAL_TOOLS: List[str] = field(default_factory=lambda: [
        "read_file",
        "write_file",
        "update_file",
        "run_command",
        "bash",
        "grep",
        "list_dir",
        "glob",
        "todo",
        "my_custom_tool",      # Add your tool here
        "file_analyzer"        # Add file tool here
    ])
```

### Step 5: Categorize the Tool

Categorize your tool for security and performance in `settings.py`:

```python
# For read-only tools (can run in parallel)
READ_ONLY_TOOLS: List[str] = field(default_factory=lambda: [
    "read_file", "grep", "list_dir", "glob",
    "file_analyzer"  # Add if read-only
])

# For tools that modify files
WRITE_TOOLS: List[str] = field(default_factory=lambda: [
    "write_file", "update_file", "todo",
    "my_custom_tool"  # Add if it writes
])

# For tools that execute commands
EXECUTE_TOOLS: List[str] = field(default_factory=lambda: [
    "run_command", "bash"
])
```

### Step 6: Update Tool Imports

Update `src/tunacode/core/agents/main.py` to import your tool:

```python
# In the tool imports section
from tunacode.tools.my_tool import MyCustomTool
from tunacode.tools.file_analyzer import FileAnalyzerTool

# In create_agent function where tools are instantiated
tools = [
    ReadFileTool(ui),
    WriteFileTool(ui),
    # ... other tools ...
    MyCustomTool(ui),      # Add your tool
    FileAnalyzerTool(ui),  # Add file tool
]
```

## Advanced Tool Features

### 1. Tool with Preview/Diff

For tools that modify content, show a preview:

```python
def format_confirmation(self, file_path: str, changes: str) -> ConfirmationInfo:
    """Show diff preview"""
    # Generate diff
    from tunacode.utils.diff_utils import generate_diff
    current_content = self._read_current_content(file_path)
    diff = generate_diff(current_content, changes, file_path)

    return ConfirmationInfo(
        tool_name="content_modifier",
        short_description=f"Modify {file_path}",
        details={"File": file_path},
        preview=diff,
        syntax="diff"  # Enables syntax highlighting
    )
```

### 2. Tool with Progress Updates

For long-running operations:

```python
async def run(self, items: List[str]) -> str:
    """Process multiple items with progress"""
    results = []

    for i, item in enumerate(items):
        # Update progress
        progress = f"Processing {i+1}/{len(items)}: {item}"
        await self.ui.info(progress)

        # Process item
        result = await self._process_item(item)
        results.append(result)

    return f"Processed {len(results)} items successfully"
```

### 3. Tool with Retryable Errors

Use ModelRetry for errors the agent can fix:

```python
async def run(self, query: str, max_results: int = 10) -> str:
    """Search with retryable errors"""
    if max_results > 100:
        # Agent can retry with different parameters
        raise ModelRetry("max_results cannot exceed 100, please use a smaller value")

    if not query.strip():
        # Agent can provide better input
        raise ModelRetry("Query cannot be empty")

    try:
        results = await self._perform_search(query, max_results)
        return self._format_results(results)
    except NetworkError:
        # Transient errors worth retrying
        raise ModelRetry("Network error, please try again")
    except Exception as e:
        # Non-retryable errors
        return await self._handle_error(e, "search operation")
```

### 4. Tool with External Service

For tools that call external APIs:

```python
class WeatherTool(BaseTool):
    """Get weather information"""

    def __init__(self, ui: UIProtocol, api_key: str):
        super().__init__(ui)
        self.api_key = api_key
        self.base_url = "https://api.weather.com/v1"

    async def run(self, location: str) -> str:
        """Get weather for location"""
        import aiohttp

        async with aiohttp.ClientSession() as session:
            url = f"{self.base_url}/weather"
            params = {"location": location, "key": self.api_key}

            try:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._format_weather(data)
                    else:
                        raise ModelRetry(f"API error: {response.status}")
            except aiohttp.ClientError as e:
                raise ModelRetry(f"Network error: {e}")
```

## Tool Best Practices

### 1. Error Handling

```python
async def run(self, **kwargs) -> str:
    try:
        # Validate inputs first
        self._validate_inputs(kwargs)

        # Perform operation
        result = await self._do_work(kwargs)

        # Return success
        return f"Success: {result}"

    except ValueError as e:
        # Input validation errors - agent can fix
        raise ModelRetry(str(e))
    except PermissionError as e:
        # Permission errors - not retryable
        return f"Error: Permission denied - {e}"
    except Exception as e:
        # Use base class error handler
        return await self._handle_error(e, "operation")
```

### 2. Input Validation

```python
def _validate_inputs(self, kwargs: Dict[str, Any]) -> None:
    """Validate tool inputs"""
    # Required parameters
    if 'required_param' not in kwargs:
        raise ModelRetry("required_param is required")

    # Type validation
    if not isinstance(kwargs.get('number_param', 0), (int, float)):
        raise ModelRetry("number_param must be a number")

    # Range validation
    value = kwargs.get('range_param', 0)
    if not 0 <= value <= 100:
        raise ModelRetry("range_param must be between 0 and 100")

    # Path validation for file tools
    if 'file_path' in kwargs:
        path = Path(kwargs['file_path'])
        if not path.is_absolute():
            # Convert to absolute
            kwargs['file_path'] = str(path.absolute())
```

### 3. Async Best Practices

```python
async def run(self, files: List[str]) -> str:
    """Process multiple files concurrently"""
    # Create tasks for concurrent execution
    tasks = []
    for file_path in files:
        task = asyncio.create_task(self._process_file(file_path))
        tasks.append(task)

    # Wait for all tasks
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Handle results
    successful = []
    failed = []

    for file_path, result in zip(files, results):
        if isinstance(result, Exception):
            failed.append(f"{file_path}: {result}")
        else:
            successful.append(result)

    # Format response
    response = f"Processed {len(successful)} files successfully"
    if failed:
        response += f"\nFailed: {len(failed)} files\n" + "\n".join(failed)

    return response
```

### 4. Security Considerations

```python
async def run(self, command: str, **kwargs) -> str:
    """Execute with security validation"""
    # Import security utilities
    from tunacode.utils.security import validate_command

    # Validate command
    if not await validate_command(command):
        return "Error: Command failed security validation"

    # Sanitize paths
    if 'path' in kwargs:
        from tunacode.utils.security import sanitize_path
        try:
            safe_path = sanitize_path(kwargs['path'])
            kwargs['path'] = str(safe_path)
        except ValueError as e:
            return f"Error: Invalid path - {e}"

    # Execute with restrictions
    return await self._execute_safely(command, **kwargs)
```

## Testing Your Tool

### 1. Unit Test

Create `tests/tools/test_my_tool.py`:

```python
import pytest
from tunacode.tools.my_tool import MyCustomTool
from tests.mocks import MockUI

@pytest.mark.asyncio
async def test_my_tool_success():
    """Test successful tool execution"""
    # Create mock UI
    ui = MockUI()
    tool = MyCustomTool(ui)

    # Execute tool
    result = await tool.run(param1="test", param2="value")

    # Verify result
    assert "Successfully processed" in result
    assert "test + value" in result

    # Verify UI interactions
    assert ui.success_called
    assert "Operation completed" in ui.last_success_message

@pytest.mark.asyncio
async def test_my_tool_missing_param():
    """Test tool with missing required parameter"""
    ui = MockUI()
    tool = MyCustomTool(ui)

    # Should raise ModelRetry
    with pytest.raises(ModelRetry) as exc_info:
        await tool.run(param2="value")  # Missing param1

    assert "param1 is required" in str(exc_info.value)

@pytest.mark.asyncio
async def test_my_tool_confirmation():
    """Test confirmation formatting"""
    ui = MockUI()
    tool = MyCustomTool(ui)

    # Get confirmation info
    info = tool.format_confirmation(param1="test", param2="value")

    # Verify confirmation
    assert info.tool_name == "my_custom_tool"
    assert "test" in info.short_description
    assert info.details["Parameter 1"] == "test"
    assert info.security_level == "medium"
```

### 2. Integration Test

Test with the agent system:

```python
@pytest.mark.asyncio
async def test_tool_in_agent():
    """Test tool integration with agent"""
    from tunacode.core.agents.main import create_agent
    from tunacode.core.state import StateManager

    # Create state and agent
    state = StateManager()
    agent = await create_agent(state)

    # Verify tool is available
    tool_names = [tool.__class__.__name__ for tool in agent.tools]
    assert "MyCustomTool" in tool_names
```

### 3. Manual Testing

Test in the REPL:

```python
# Start TunaCode
python -m tunacode

# Test your tool via agent
> Please use my_custom_tool with param1="hello" and param2="world"

# Verify confirmation appears
# Verify execution works
# Verify result is correct
```

## Tool Documentation

### 1. Docstring Format

```python
class MyTool(BaseTool):
    """
    One-line summary of what the tool does.

    Detailed description of the tool's purpose, capabilities,
    and any important notes about its usage.

    Args (in run method):
        param1: Description of parameter 1
        param2: Description of parameter 2 (default: value)

    Returns:
        Description of what the tool returns to the agent

    Raises:
        ModelRetry: When and why this is raised

    Example:
        Tool usage example from agent perspective
    """
```

### 2. Type Hints

Always use type hints:

```python
from typing import Optional, List, Dict, Any

async def run(
    self,
    file_path: str,
    options: Optional[Dict[str, Any]] = None,
    filters: Optional[List[str]] = None
) -> str:
    """Process with type hints"""
    pass
```

## Common Patterns

### 1. Configuration Options

```python
class ConfigurableTool(BaseTool):
    """Tool with configuration"""

    def __init__(self, ui: UIProtocol, config: Optional[Dict] = None):
        super().__init__(ui)
        self.config = config or {}
        self.timeout = self.config.get('timeout', 30)
        self.max_retries = self.config.get('max_retries', 3)
```

### 2. Batch Operations

```python
async def run(self, items: List[str], batch_size: int = 10) -> str:
    """Process items in batches"""
    results = []

    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        batch_results = await self._process_batch(batch)
        results.extend(batch_results)

        # Progress update
        await self.ui.info(f"Processed {len(results)}/{len(items)} items")

    return f"Completed: {len(results)} items"
```

### 3. Caching Results

```python
class CachedTool(BaseTool):
    """Tool with result caching"""

    def __init__(self, ui: UIProtocol):
        super().__init__(ui)
        self._cache = {}

    async def run(self, key: str) -> str:
        """Get with caching"""
        if key in self._cache:
            await self.ui.info("Using cached result")
            return self._cache[key]

        result = await self._expensive_operation(key)
        self._cache[key] = result
        return result
```

## Troubleshooting

### Tool Not Found

1. Ensure tool is in `INTERNAL_TOOLS` list
2. Check import in `main.py`
3. Verify tool class name matches

### Confirmation Not Showing

1. Check tool categorization
2. Verify not in YOLO mode
3. Ensure format_confirmation returns ConfirmationInfo

### Parallel Execution Issues

1. Only READ_ONLY_TOOLS run in parallel
2. Ensure tool is truly read-only
3. Check for side effects

## Next Steps

1. Review existing tools for examples
2. Understand the [Tool System Architecture](../modules/tools-system.md)
3. Learn about [MCP Integration](mcp-integration.md) for external tools
4. Read [Testing Guidelines](testing-guide.md)
