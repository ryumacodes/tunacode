<!-- This document describes all utility functions for file operations, text processing, security, token counting, and system operations -->

# TunaCode Utilities Documentation

## Overview

TunaCode's utilities module provides essential helper functions for file operations, text processing, security validation, token counting, and system operations. These utilities form the foundation for many higher-level features.

## File Utilities (utils/file_utils.py)

File operation helpers with safety and encoding features:

### read_file_with_fallback()
```python
def read_file_with_fallback(file_path: Union[str, Path]) -> str:
    """Read file with automatic encoding detection"""
    path = Path(file_path)

    # Try UTF-8 first (most common)
    try:
        return path.read_text(encoding='utf-8')
    except UnicodeDecodeError:
        pass

    # Try with chardet for encoding detection
    try:
        import chardet
        raw_data = path.read_bytes()
        detected = chardet.detect(raw_data)
        encoding = detected['encoding'] or 'utf-8'
        return raw_data.decode(encoding)
    except Exception:
        # Final fallback with error replacement
        return path.read_text(encoding='utf-8', errors='replace')
```

### get_file_info()
```python
def get_file_info(file_path: Union[str, Path]) -> Dict[str, Any]:
    """Get comprehensive file information"""
    path = Path(file_path)
    stat = path.stat()

    return {
        'path': str(path.absolute()),
        'name': path.name,
        'size': stat.st_size,
        'size_human': format_size(stat.st_size),
        'modified': datetime.fromtimestamp(stat.st_mtime),
        'created': datetime.fromtimestamp(stat.st_ctime),
        'is_file': path.is_file(),
        'is_dir': path.is_dir(),
        'extension': path.suffix,
        'permissions': oct(stat.st_mode)[-3:]
    }
```

### format_size()
```python
def format_size(size_bytes: int) -> str:
    """Format bytes as human-readable size"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f}{unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f}PB"
```

### ensure_parent_dir()
```python
def ensure_parent_dir(file_path: Union[str, Path]) -> Path:
    """Ensure parent directory exists"""
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path
```

### [DEAD CODE] DotDict class
```python
# This class is unused and should be removed
class DotDict(dict):
    """Dictionary with dot notation access"""
    def __getattr__(self, key):
        return self.get(key)
```

### [DEAD CODE] capture_stdout()
```python
# This function is unused and should be removed
def capture_stdout(func: Callable) -> str:
    """Capture stdout from a function"""
```

## Text Utilities (utils/text_utils.py)

Text processing and manipulation helpers:

### truncate_text()
```python
def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """Truncate text with suffix if exceeds max length"""
    if len(text) <= max_length:
        return text

    # Account for suffix length
    truncate_at = max_length - len(suffix)

    # Try to break at word boundary
    if ' ' in text[:truncate_at]:
        truncate_at = text.rfind(' ', 0, truncate_at)

    return text[:truncate_at] + suffix
```

### estimate_tokens()
```python
def estimate_tokens(text: str, model: str = "gpt-3.5-turbo") -> int:
    """Estimate token count for text"""
    # Simple estimation: ~4 characters per token
    # More accurate with tiktoken if available
    try:
        import tiktoken
        encoding = tiktoken.encoding_for_model(model)
        return len(encoding.encode(text))
    except:
        # Fallback estimation
        return len(text) // 4
```

### wrap_in_markdown()
```python
def wrap_in_markdown(content: str, language: str = "") -> str:
    """Wrap content in markdown code block"""
    return f"```{language}\n{content}\n```"
```

### extract_code_blocks()
```python
def extract_code_blocks(text: str) -> List[Dict[str, str]]:
    """Extract code blocks from markdown text"""
    pattern = r'```(\w*)\n(.*?)\n```'
    matches = re.findall(pattern, text, re.DOTALL)

    return [
        {"language": lang or "text", "content": content}
        for lang, content in matches
    ]
```

### sanitize_for_display()
```python
def sanitize_for_display(text: str) -> str:
    """Sanitize text for terminal display"""
    # Remove ANSI escape codes
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    text = ansi_escape.sub('', text)

    # Replace tabs with spaces
    text = text.replace('\t', '    ')

    # Ensure printable characters
    return ''.join(char if char.isprintable() or char == '\n' else '?' for char in text)
```

## Diff Utilities (utils/diff_utils.py)

Utilities for generating and formatting diffs:

### generate_diff()
```python
def generate_diff(old_text: str, new_text: str, filename: str = "file") -> str:
    """Generate unified diff between texts"""
    old_lines = old_text.splitlines(keepends=True)
    new_lines = new_text.splitlines(keepends=True)

    diff = unified_diff(
        old_lines,
        new_lines,
        fromfile=f"a/{filename}",
        tofile=f"b/{filename}",
        lineterm=''
    )

    return ''.join(diff)
```

### format_diff_for_display()
```python
def format_diff_for_display(diff_text: str, use_color: bool = True) -> str:
    """Format diff with color highlighting"""
    if not use_color:
        return diff_text

    lines = []
    for line in diff_text.splitlines():
        if line.startswith('+') and not line.startswith('+++'):
            lines.append(f"[green]{line}[/green]")
        elif line.startswith('-') and not line.startswith('---'):
            lines.append(f"[red]{line}[/red]")
        elif line.startswith('@'):
            lines.append(f"[cyan]{line}[/cyan]")
        else:
            lines.append(line)

    return '\n'.join(lines)
```

### apply_patch()
```python
def apply_patch(original: str, patch: str) -> str:
    """Apply a patch to original text"""
    # Simple implementation for single replacements
    # For complex patches, use python-patch library

    lines = original.splitlines(keepends=True)
    patch_lines = patch.splitlines(keepends=True)

    # Parse and apply patch
    # ... implementation details ...

    return ''.join(lines)
```

## Security Utilities (utils/security.py)

Security validation and sanitization:

### validate_command()
```python
async def validate_command(command: str) -> bool:
    """Validate shell command for security"""
    # Dangerous command patterns
    DANGEROUS_PATTERNS = [
        r'rm\s+-rf\s+/',          # Recursive root deletion
        r'rm\s+.*\s+/',           # Root deletion
        r'>\s*/dev/[^n]',         # Overwriting devices
        r'fork\s*\(\s*\)\s*bomb', # Fork bombs
        r':\(\)\{.*\|.*&\};:',    # Fork bomb syntax
        r'curl.*\|.*sh',          # Curl pipe to shell
        r'wget.*\|.*sh',          # Wget pipe to shell
    ]

    # Check each pattern
    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            logger.warning(f"Dangerous command blocked: {command}")
            return False

    # Additional checks
    if contains_path_traversal(command):
        return False

    return True
```

### sanitize_path()
```python
def sanitize_path(path: str, base_path: Optional[Path] = None) -> Path:
    """Sanitize and validate file path"""
    # Remove null bytes
    path = path.replace('\0', '')

    # Resolve to absolute path
    clean_path = Path(path).resolve()

    # Check if within base path
    if base_path:
        base = Path(base_path).resolve()
        try:
            clean_path.relative_to(base)
        except ValueError:
            raise ValueError(f"Path {path} is outside base directory")

    return clean_path
```

### contains_path_traversal()
```python
def contains_path_traversal(path: str) -> bool:
    """Check if path contains traversal attempts"""
    traversal_patterns = [
        '..',           # Parent directory
        '../',          # Parent directory with separator
        '..\\',         # Windows parent directory
        '%2e%2e',       # URL encoded
        '..%2f',        # Mixed encoding
        '..%5c',        # Windows encoded
    ]

    path_lower = path.lower()
    return any(pattern in path_lower for pattern in traversal_patterns)
```

### validate_git_operation()
```python
def validate_git_operation(operation: str, args: List[str]) -> bool:
    """Validate git operations for safety"""
    # Dangerous git operations
    dangerous_ops = {
        'push': ['--force', '-f', '--force-with-lease'],
        'reset': ['--hard'],
        'clean': ['-f', '-x', '-d'],
    }

    if operation in dangerous_ops:
        dangerous_flags = dangerous_ops[operation]
        for arg in args:
            if arg in dangerous_flags:
                logger.warning(f"Potentially dangerous git operation: {operation} {arg}")
                # Could prompt for confirmation here

    return True
```

## Token Counter (utils/token_counter.py)

Token counting with tiktoken integration:

### TokenCounter
```python
class TokenCounter:
    """Efficient token counting with caching"""

    def __init__(self):
        self._encodings = {}  # Cache encodings by model
        self._default_encoding = None

    def get_encoding(self, model: str) -> Any:
        """Get tiktoken encoding for model"""
        if model in self._encodings:
            return self._encodings[model]

        try:
            import tiktoken

            # Map model to encoding
            if "gpt-4" in model:
                encoding = tiktoken.encoding_for_model("gpt-4")
            elif "gpt-3.5" in model:
                encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
            elif "claude" in model:
                # Claude uses similar tokenization to GPT
                encoding = tiktoken.get_encoding("cl100k_base")
            else:
                encoding = tiktoken.get_encoding("cl100k_base")

            self._encodings[model] = encoding
            return encoding

        except Exception as e:
            logger.warning(f"Failed to load encoding for {model}: {e}")
            return None

    def count_tokens(self, text: str, model: str = "gpt-3.5-turbo") -> int:
        """Count tokens in text"""
        encoding = self.get_encoding(model)

        if encoding:
            try:
                return len(encoding.encode(text))
            except Exception:
                pass

        # Fallback estimation
        return self._estimate_tokens(text)

    def _estimate_tokens(self, text: str) -> int:
        """Fallback token estimation"""
        # Rules of thumb:
        # - ~4 characters per token for English
        # - Whitespace and punctuation often separate tokens
        # - Adjust for code (more tokens due to symbols)

        char_count = len(text)
        word_count = len(text.split())

        # Check if it's code
        is_code = any(indicator in text for indicator in ['{', '}', ';', 'def', 'class'])

        if is_code:
            # Code typically has more tokens
            estimated = char_count // 3
        else:
            # Regular text
            estimated = char_count // 4

        # Sanity check with word count
        min_tokens = word_count * 0.7
        max_tokens = word_count * 2

        return int(max(min_tokens, min(estimated, max_tokens)))
```

## Message Utilities (utils/message_utils.py)

Message format conversion and processing:

### format_message_for_display()
```python
def format_message_for_display(message: Message) -> str:
    """Format message for terminal display"""
    role_colors = {
        "user": "green",
        "assistant": "blue",
        "system": "yellow",
        "tool": "magenta"
    }

    color = role_colors.get(message.role, "white")
    role_text = f"[{color}]{message.role.upper()}[/{color}]"

    # Format content based on type
    if isinstance(message.content, str):
        content = message.content
    elif isinstance(message.content, list):
        # Handle multi-part messages
        parts = []
        for part in message.content:
            if part.get("type") == "text":
                parts.append(part.get("text", ""))
            elif part.get("type") == "image":
                parts.append("[Image]")
        content = "\n".join(parts)
    else:
        content = str(message.content)

    return f"{role_text}: {content}"
```

### extract_text_from_message()
```python
def extract_text_from_message(message: Union[str, Dict, List]) -> str:
    """Extract plain text from various message formats"""
    if isinstance(message, str):
        return message

    if isinstance(message, dict):
        # Handle different message structures
        if "text" in message:
            return message["text"]
        if "content" in message:
            return extract_text_from_message(message["content"])

    if isinstance(message, list):
        # Multi-part message
        texts = []
        for part in message:
            if isinstance(part, dict) and part.get("type") == "text":
                texts.append(part.get("text", ""))
        return "\n".join(texts)

    return str(message)
```

### messages_to_dict()
```python
def messages_to_dict(messages: List[Message]) -> List[Dict[str, Any]]:
    """Convert message objects to serializable dicts"""
    return [
        {
            "role": msg.role,
            "content": msg.content,
            "timestamp": msg.timestamp.isoformat() if hasattr(msg, 'timestamp') else None,
            "metadata": getattr(msg, 'metadata', {})
        }
        for msg in messages
    ]
```

## Retry Utilities (utils/retry.py)

Retry logic with exponential backoff:

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
    """Retry function with exponential backoff"""
    delay = initial_delay
    last_exception = None

    for attempt in range(max_retries):
        try:
            return await func()
        except exceptions as e:
            last_exception = e

            if attempt == max_retries - 1:
                # Last attempt failed
                raise

            # Log retry
            logger.warning(
                f"Attempt {attempt + 1} failed: {e}. "
                f"Retrying in {delay:.1f} seconds..."
            )

            # Wait with backoff
            await asyncio.sleep(delay)

            # Increase delay
            delay = min(delay * backoff_factor, max_delay)

    raise last_exception
```

### RetryableError
```python
class RetryableError(Exception):
    """Error that should trigger a retry"""
    def __init__(self, message: str, retry_after: Optional[float] = None):
        super().__init__(message)
        self.retry_after = retry_after
```

## System Utilities (utils/system.py)

System information and operations:

### get_system_info()
```python
def get_system_info() -> Dict[str, Any]:
    """Get comprehensive system information"""
    import platform
    import psutil

    return {
        "platform": platform.system(),
        "platform_version": platform.version(),
        "architecture": platform.machine(),
        "python_version": platform.python_version(),
        "cpu_count": os.cpu_count(),
        "memory_total": psutil.virtual_memory().total,
        "memory_available": psutil.virtual_memory().available,
        "disk_usage": psutil.disk_usage('/').percent,
        "user": os.environ.get('USER', 'unknown'),
        "home": str(Path.home()),
        "cwd": str(Path.cwd())
    }
```

### is_git_repository()
```python
def is_git_repository(path: Optional[Path] = None) -> bool:
    """Check if path is within a git repository"""
    path = path or Path.cwd()

    # Walk up directory tree looking for .git
    current = path.resolve()
    while current != current.parent:
        if (current / '.git').exists():
            return True
        current = current.parent

    return False
```

### get_terminal_size()
```python
def get_terminal_size() -> Tuple[int, int]:
    """Get terminal dimensions (width, height)"""
    try:
        size = os.get_terminal_size()
        return (size.columns, size.lines)
    except:
        # Fallback values
        return (80, 24)
```

### which_installation_method()
```python
def which_installation_method() -> str:
    """Detect how TunaCode was installed"""
    # Check if in virtual environment
    in_venv = sys.prefix != sys.base_prefix

    # Check for pipx
    tunacode_path = shutil.which("tunacode")
    if tunacode_path and "pipx" in tunacode_path:
        return "pipx"

    # Check for pip install --user
    if tunacode_path and Path.home() in Path(tunacode_path).parents:
        return "pip_user"

    if in_venv:
        return "pip_venv"

    return "pip_global"
```

## Import Cache (utils/import_cache.py)

Performance optimization for module imports:

### ImportCache
```python
class ImportCache:
    """Cache imported modules for performance"""

    def __init__(self):
        self._cache: Dict[str, Any] = {}
        self._import_times: Dict[str, float] = {}

    def import_module(self, name: str) -> Any:
        """Import module with caching"""
        if name in self._cache:
            return self._cache[name]

        start_time = time.time()

        try:
            module = importlib.import_module(name)
            self._cache[name] = module
            self._import_times[name] = time.time() - start_time

            logger.debug(f"Imported {name} in {self._import_times[name]:.3f}s")

            return module

        except ImportError as e:
            logger.error(f"Failed to import {name}: {e}")
            raise

    def get_import_stats(self) -> Dict[str, float]:
        """Get import timing statistics"""
        return self._import_times.copy()

    def clear_cache(self, module_name: Optional[str] = None):
        """Clear import cache"""
        if module_name:
            self._cache.pop(module_name, None)
            self._import_times.pop(module_name, None)
        else:
            self._cache.clear()
            self._import_times.clear()
```

## User Configuration (utils/user_configuration.py)

User configuration file management:

### load_user_config()
```python
def load_user_config() -> Dict[str, Any]:
    """Load user configuration with defaults"""
    from tunacode.configuration.defaults import DEFAULT_CONFIG
    from tunacode.configuration.settings import PathConfig

    config_path = PathConfig.CONFIG_FILE

    # Start with defaults
    config = DEFAULT_CONFIG.copy()

    # Load user config if exists
    if config_path.exists():
        try:
            with open(config_path, 'r') as f:
                user_config = json.load(f)

            # Deep merge
            config = deep_merge(config, user_config)

        except Exception as e:
            logger.error(f"Failed to load user config: {e}")

    return config
```

### save_user_config()
```python
def save_user_config(config: Dict[str, Any]) -> None:
    """Save user configuration to disk"""
    from tunacode.configuration.settings import PathConfig

    config_path = PathConfig.CONFIG_FILE

    # Ensure directory exists
    config_path.parent.mkdir(parents=True, exist_ok=True)

    # Write with pretty formatting
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2, sort_keys=True)

    logger.info(f"Saved configuration to {config_path}")
```

### deep_merge()
```python
def deep_merge(base: Dict, update: Dict) -> Dict:
    """Deep merge dictionaries"""
    result = base.copy()

    for key, value in update.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            # Recursive merge for nested dicts
            result[key] = deep_merge(result[key], value)
        else:
            # Direct assignment
            result[key] = value

    return result
```

## [DEAD CODE] Ripgrep Wrapper (utils/ripgrep.py)

This module is unused as grep.py tool is used instead:

```python
# This entire module should be removed
def ripgrep(pattern: str, path: str = ".", ...) -> str:
    """UNUSED - grep.py tool is used instead"""
```

## [DEAD CODE] BM25 Search (utils/bm25.py)

This module is part of unused code_index.py:

```python
# This entire module should be removed
class BM25:
    """UNUSED - Part of unused code indexing system"""
```

## Best Practices

### 1. Error Handling
```python
# Always provide context in errors
try:
    content = read_file_with_fallback(path)
except Exception as e:
    logger.error(f"Failed to read {path}: {e}")
    raise ValueError(f"Cannot read file: {path}") from e
```

### 2. Path Handling
```python
# Always use Path objects and resolve
path = Path(user_input).resolve()

# Validate paths
clean_path = sanitize_path(user_input, base_path=project_root)
```

### 3. Encoding Safety
```python
# Always handle encoding errors
content = path.read_text(encoding='utf-8', errors='replace')

# Or use the utility
content = read_file_with_fallback(path)
```

### 4. Security First
```python
# Always validate user input
if not await validate_command(user_command):
    raise SecurityError("Command not allowed")

# Sanitize paths
safe_path = sanitize_path(user_path)
```

## Performance Tips

1. **Use Import Cache**: For frequently imported modules
2. **Token Counting**: Cache encodings for repeated use
3. **File Operations**: Use async where possible
4. **Text Processing**: Process in chunks for large texts

## Future Enhancements

1. **Async File Operations**: Full async file I/O
2. **Better Token Counting**: Provider-specific accuracy
3. **Enhanced Security**: More validation patterns
4. **Performance Monitoring**: Built-in profiling
5. **Utility Plugins**: Extensible utility system
