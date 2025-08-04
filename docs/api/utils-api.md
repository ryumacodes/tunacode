<!-- This document covers the API for all utility functions: file operations, text processing, security, and token counting -->

# Utilities API Reference

This document provides detailed API documentation for TunaCode's utility functions.

## File Utilities

`tunacode.utils.file_utils`

File operation helpers with safety and encoding features.

### read_file_with_fallback()
```python
def read_file_with_fallback(file_path: Union[str, Path]) -> str:
    """
    Read file with automatic encoding detection.

    Args:
        file_path: Path to file

    Returns:
        str: File contents

    Note:
        Tries UTF-8 first, falls back to chardet.

    Example:
        >>> content = read_file_with_fallback("data.txt")
    """
```

### get_file_info()
```python
def get_file_info(file_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Get comprehensive file information.

    Args:
        file_path: Path to file

    Returns:
        Dict containing:
            - path: Absolute path
            - name: File name
            - size: Size in bytes
            - size_human: Human-readable size
            - modified: Modification time
            - created: Creation time
            - is_file: Whether it's a file
            - is_dir: Whether it's a directory
            - extension: File extension
            - permissions: Octal permissions

    Example:
        >>> info = get_file_info("script.py")
        >>> print(f"{info['name']}: {info['size_human']}")
        script.py: 2.5KB
    """
```

### format_size()
```python
def format_size(size_bytes: int) -> str:
    """
    Format bytes as human-readable size.

    Args:
        size_bytes: Size in bytes

    Returns:
        str: Formatted size (e.g., "1.5KB")

    Example:
        >>> format_size(1536)
        '1.5KB'
        >>> format_size(1073741824)
        '1.0GB'
    """
```

### ensure_parent_dir()
```python
def ensure_parent_dir(file_path: Union[str, Path]) -> Path:
    """
    Ensure parent directory exists.

    Args:
        file_path: Path to file

    Returns:
        Path: Resolved file path

    Example:
        >>> path = ensure_parent_dir("output/data/file.txt")
        # Creates output/data/ if needed
    """
```

### is_binary_file()
```python
def is_binary_file(file_path: Union[str, Path]) -> bool:
    """
    Check if file is binary.

    Args:
        file_path: Path to file

    Returns:
        bool: True if binary

    Example:
        >>> is_binary_file("image.png")
        True
        >>> is_binary_file("script.py")
        False
    """
```

## Text Utilities

`tunacode.utils.text_utils`

Text processing and manipulation helpers.

### truncate_text()
```python
def truncate_text(
    text: str,
    max_length: int,
    suffix: str = "..."
) -> str:
    """
    Truncate text with suffix.

    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Truncation indicator

    Returns:
        str: Truncated text

    Example:
        >>> truncate_text("This is a long text", 10)
        'This is...'
    """
```

### estimate_tokens()
```python
def estimate_tokens(
    text: str,
    model: str = "gpt-3.5-turbo"
) -> int:
    """
    Estimate token count for text.

    Args:
        text: Text to count
        model: Model for estimation

    Returns:
        int: Estimated token count

    Example:
        >>> tokens = estimate_tokens("Hello, world!")
        >>> print(f"~{tokens} tokens")
    """
```

### wrap_in_markdown()
```python
def wrap_in_markdown(
    content: str,
    language: str = ""
) -> str:
    """
    Wrap content in markdown code block.

    Args:
        content: Code content
        language: Language identifier

    Returns:
        str: Markdown formatted code

    Example:
        >>> code = wrap_in_markdown("print('hello')", "python")
        ```python
        print('hello')
        ```
    """
```

### extract_code_blocks()
```python
def extract_code_blocks(text: str) -> List[Dict[str, str]]:
    """
    Extract code blocks from markdown.

    Args:
        text: Markdown text

    Returns:
        List of dicts with:
            - language: Code language
            - content: Code content

    Example:
        >>> blocks = extract_code_blocks(markdown_text)
        >>> for block in blocks:
        ...     print(f"{block['language']}: {len(block['content'])} chars")
    """
```

### sanitize_for_display()
```python
def sanitize_for_display(text: str) -> str:
    """
    Sanitize text for terminal display.

    Args:
        text: Text to sanitize

    Returns:
        str: Sanitized text

    Note:
        Removes ANSI codes, replaces tabs, ensures printable.
    """
```

### indent_text()
```python
def indent_text(
    text: str,
    indent: str = "  ",
    first_line: bool = True
) -> str:
    """
    Indent text lines.

    Args:
        text: Text to indent
        indent: Indent string
        first_line: Whether to indent first line

    Returns:
        str: Indented text
    """
```

## Diff Utilities

`tunacode.utils.diff_utils`

Utilities for generating and formatting diffs.

### generate_diff()
```python
def generate_diff(
    old_text: str,
    new_text: str,
    filename: str = "file",
    context_lines: int = 3
) -> str:
    """
    Generate unified diff.

    Args:
        old_text: Original text
        new_text: Modified text
        filename: File name for diff
        context_lines: Context lines to show

    Returns:
        str: Unified diff output

    Example:
        >>> diff = generate_diff("hello", "hello world")
        --- a/file
        +++ b/file
        @@ -1 +1 @@
        -hello
        +hello world
    """
```

### format_diff_for_display()
```python
def format_diff_for_display(
    diff_text: str,
    use_color: bool = True
) -> str:
    """
    Format diff with color highlighting.

    Args:
        diff_text: Diff text
        use_color: Whether to add colors

    Returns:
        str: Formatted diff

    Colors:
        - Green: Added lines
        - Red: Removed lines
        - Cyan: Location markers
    """
```

### apply_patch()
```python
def apply_patch(
    original: str,
    patch: str
) -> str:
    """
    Apply a patch to text.

    Args:
        original: Original text
        patch: Patch to apply

    Returns:
        str: Patched text

    Raises:
        ValueError: If patch cannot be applied
    """
```

## Security Utilities

`tunacode.utils.security`

Security validation and sanitization.

### validate_command()
```python
async def validate_command(command: str) -> bool:
    """
    Validate shell command for security.

    Args:
        command: Command to validate

    Returns:
        bool: Whether command is safe

    Checks for:
        - Dangerous patterns (rm -rf /, etc.)
        - Fork bombs
        - Curl/wget piping to shell
        - Device overwrites

    Example:
        >>> if await validate_command(user_cmd):
        ...     execute(user_cmd)
    """
```

### sanitize_path()
```python
def sanitize_path(
    path: str,
    base_path: Optional[Path] = None
) -> Path:
    """
    Sanitize and validate file path.

    Args:
        path: Path to sanitize
        base_path: Optional base directory

    Returns:
        Path: Clean, safe path

    Raises:
        ValueError: If path is unsafe

    Example:
        >>> safe_path = sanitize_path("../../../etc/passwd", base_path="/app")
        ValueError: Path is outside base directory
    """
```

### contains_path_traversal()
```python
def contains_path_traversal(path: str) -> bool:
    """
    Check for path traversal attempts.

    Args:
        path: Path to check

    Returns:
        bool: True if traversal detected

    Detects:
        - .. patterns
        - URL encoded traversals
        - Mixed encodings
    """
```

### validate_git_operation()
```python
def validate_git_operation(
    operation: str,
    args: List[str]
) -> bool:
    """
    Validate git operations.

    Args:
        operation: Git command
        args: Command arguments

    Returns:
        bool: Whether operation is safe

    Warns about:
        - Force pushes
        - Hard resets
        - Destructive cleans
    """
```

### escape_shell_arg()
```python
def escape_shell_arg(arg: str) -> str:
    """
    Escape shell argument safely.

    Args:
        arg: Argument to escape

    Returns:
        str: Escaped argument

    Example:
        >>> cmd = f"echo {escape_shell_arg(user_input)}"
    """
```

## Token Counter

`tunacode.utils.token_counter`

Token counting with tiktoken integration.

### TokenCounter
```python
class TokenCounter:
    """Efficient token counting with caching."""

    def __init__(self):
        """Initialize counter with encoding cache."""
```

#### Methods

##### get_encoding()
```python
def get_encoding(self, model: str) -> Any:
    """
    Get tiktoken encoding for model.

    Args:
        model: Model name

    Returns:
        Encoding object or None

    Note:
        Encodings are cached per model.
    """
```

##### count_tokens()
```python
def count_tokens(
    self,
    text: str,
    model: str = "gpt-3.5-turbo"
) -> int:
    """
    Count tokens in text.

    Args:
        text: Text to count
        model: Model for encoding

    Returns:
        int: Token count

    Example:
        >>> counter = TokenCounter()
        >>> tokens = counter.count_tokens("Hello world", "gpt-4")
    """
```

##### estimate_messages_tokens()
```python
def estimate_messages_tokens(
    self,
    messages: List[Dict[str, str]],
    model: str = "gpt-3.5-turbo"
) -> int:
    """
    Estimate tokens in messages.

    Args:
        messages: List of message dicts
        model: Model for encoding

    Returns:
        int: Total token estimate

    Note:
        Includes message formatting overhead.
    """
```

## Message Utilities

`tunacode.utils.message_utils`

Message format conversion and processing.

### format_message_for_display()
```python
def format_message_for_display(message: Message) -> str:
    """
    Format message for terminal display.

    Args:
        message: Message object

    Returns:
        str: Formatted message with colors

    Example:
        >>> print(format_message_for_display(msg))
        USER: Hello, how are you?
    """
```

### extract_text_from_message()
```python
def extract_text_from_message(
    message: Union[str, Dict, List]
) -> str:
    """
    Extract plain text from various formats.

    Args:
        message: Message in any format

    Returns:
        str: Extracted text

    Handles:
        - String messages
        - Dict with 'text' or 'content'
        - List of message parts
    """
```

### messages_to_dict()
```python
def messages_to_dict(
    messages: List[Message]
) -> List[Dict[str, Any]]:
    """
    Convert messages to serializable dicts.

    Args:
        messages: List of Message objects

    Returns:
        List[Dict]: Serializable messages
    """
```

### truncate_message_history()
```python
def truncate_message_history(
    messages: List[Message],
    max_tokens: int,
    model: str = "gpt-3.5-turbo",
    keep_system: bool = True
) -> List[Message]:
    """
    Truncate messages to fit token limit.

    Args:
        messages: Message history
        max_tokens: Maximum tokens
        model: Model for counting
        keep_system: Preserve system messages

    Returns:
        List[Message]: Truncated messages
    """
```

## Retry Utilities

`tunacode.utils.retry`

Retry logic with exponential backoff.

### retry_with_backoff()
```python
async def retry_with_backoff(
    func: Callable,
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    max_delay: float = 60.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,)
) -> Any:
    """
    Retry function with exponential backoff.

    Args:
        func: Async function to retry
        max_retries: Maximum attempts
        initial_delay: Initial delay in seconds
        backoff_factor: Delay multiplier
        max_delay: Maximum delay
        exceptions: Exceptions to retry

    Returns:
        Function result

    Raises:
        Last exception if all retries fail

    Example:
        >>> result = await retry_with_backoff(
        ...     api_call,
        ...     max_retries=5,
        ...     exceptions=(NetworkError,)
        ... )
    """
```

### RetryableError
```python
class RetryableError(Exception):
    """Error that should trigger retry."""

    def __init__(
        self,
        message: str,
        retry_after: Optional[float] = None
    ):
        """
        Initialize error.

        Args:
            message: Error message
            retry_after: Suggested retry delay
        """
```

## System Utilities

`tunacode.utils.system`

System information and operations.

### get_system_info()
```python
def get_system_info() -> Dict[str, Any]:
    """
    Get comprehensive system information.

    Returns:
        Dict containing:
            - platform: OS name
            - platform_version: OS version
            - architecture: CPU architecture
            - python_version: Python version
            - cpu_count: Number of CPUs
            - memory_total: Total RAM
            - memory_available: Available RAM
            - disk_usage: Disk usage percentage
            - user: Current user
            - home: Home directory
            - cwd: Current directory

    Example:
        >>> info = get_system_info()
        >>> print(f"Python {info['python_version']} on {info['platform']}")
    """
```

### is_git_repository()
```python
def is_git_repository(
    path: Optional[Path] = None
) -> bool:
    """
    Check if path is in git repository.

    Args:
        path: Path to check (default: cwd)

    Returns:
        bool: True if in git repo
    """
```

### get_terminal_size()
```python
def get_terminal_size() -> Tuple[int, int]:
    """
    Get terminal dimensions.

    Returns:
        Tuple[int, int]: (width, height)

    Note:
        Falls back to (80, 24) if detection fails.
    """
```

### which_installation_method()
```python
def which_installation_method() -> str:
    """
    Detect TunaCode installation method.

    Returns:
        str: One of:
            - "pipx"
            - "pip_user"
            - "pip_venv"
            - "pip_global"
            - "development"
    """
```

### run_shell_command()
```python
async def run_shell_command(
    command: Union[str, List[str]],
    timeout: Optional[float] = None,
    check: bool = True
) -> Tuple[str, str, int]:
    """
    Run shell command safely.

    Args:
        command: Command to run
        timeout: Timeout in seconds
        check: Whether to raise on error

    Returns:
        Tuple of (stdout, stderr, returncode)

    Example:
        >>> stdout, stderr, code = await run_shell_command("ls -la")
    """
```

## Import Cache

`tunacode.utils.import_cache`

Performance optimization for module imports.

### ImportCache
```python
class ImportCache:
    """Cache imported modules for performance."""

    def __init__(self):
        """Initialize cache."""
```

#### Methods

##### import_module()
```python
def import_module(self, name: str) -> Any:
    """
    Import module with caching.

    Args:
        name: Module name

    Returns:
        Imported module

    Note:
        Tracks import times for profiling.
    """
```

##### get_import_stats()
```python
def get_import_stats(self) -> Dict[str, float]:
    """
    Get import timing statistics.

    Returns:
        Dict[str, float]: Module -> import time
    """
```

##### clear_cache()
```python
def clear_cache(self, module_name: Optional[str] = None) -> None:
    """
    Clear import cache.

    Args:
        module_name: Specific module or all
    """
```

## Usage Examples

### File Operations

```python
from tunacode.utils.file_utils import (
    read_file_with_fallback,
    get_file_info,
    ensure_parent_dir
)

# Read file safely
content = read_file_with_fallback("data.txt")

# Get file info
info = get_file_info("script.py")
print(f"Size: {info['size_human']}")
print(f"Modified: {info['modified']}")

# Ensure directory exists
output_path = ensure_parent_dir("output/results/data.json")
```

### Text Processing

```python
from tunacode.utils.text_utils import (
    truncate_text,
    extract_code_blocks,
    wrap_in_markdown
)

# Truncate long text
summary = truncate_text(long_text, max_length=100)

# Extract code from markdown
blocks = extract_code_blocks(markdown_content)
for block in blocks:
    print(f"Found {block['language']} code")

# Format code
formatted = wrap_in_markdown(code, "python")
```

### Security

```python
from tunacode.utils.security import (
    validate_command,
    sanitize_path
)

# Validate command
user_cmd = input("Enter command: ")
if await validate_command(user_cmd):
    # Safe to execute
    pass
else:
    print("Command rejected for security")

# Sanitize path
try:
    safe_path = sanitize_path(user_path, base_path="/app")
    # Use safe_path
except ValueError as e:
    print(f"Invalid path: {e}")
```
