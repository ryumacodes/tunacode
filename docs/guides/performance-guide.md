<!-- This guide covers performance optimization including parallel execution, caching, memory management, and best practices -->

# TunaCode Performance Optimization Guide

This guide covers performance optimization strategies for TunaCode, including parallel tool execution, caching, memory management, and best practices for efficient operation.

## Performance Architecture

TunaCode is designed with performance in mind:

- **Async-first architecture** for non-blocking operations
- **Parallel tool execution** for read-only operations
- **Smart caching** for imports and file operations
- **Lazy loading** for on-demand resource allocation
- **Token management** to prevent context overflow

## Parallel Tool Execution

### Overview

TunaCode can execute read-only tools in parallel, providing up to 3x performance improvement for multi-tool operations.

### Configuration

Control parallel execution with environment variable:

```bash
# Set maximum parallel tools (default: CPU count)
export TUNACODE_MAX_PARALLEL=8
tunacode

# Disable parallel execution
export TUNACODE_MAX_PARALLEL=1
tunacode
```

### How It Works

The agent automatically batches consecutive read-only tools:

```python
# Agent request with multiple file reads
"Please analyze main.py, utils.py, and config.py"

# Execution plan:
# Batch 1 (parallel): read_file(main.py), read_file(utils.py), read_file(config.py)
# All three files read simultaneously!
```

### Supported Parallel Tools

These tools can execute in parallel:
- `read_file` - File reading
- `grep` - Content search
- `list_dir` - Directory listing
- `glob` - Pattern matching

### Visual Feedback

Enable thoughts display to see parallel execution:

```bash
/thoughts on

# You'll see:
🚀 PARALLEL BATCH #1: Executing 3 read-only tools concurrently
  └─ read_file: main.py
  └─ read_file: utils.py
  └─ read_file: config.py
✅ Parallel batch completed successfully
```

## Performance Best Practices

### 1. Batch Operations

**Good:** Request multiple operations at once
```
"Read all Python files in src/ and analyze their imports"
```

**Bad:** Sequential requests
```
"Read src/main.py"
"Now read src/utils.py"
"Now read src/config.py"
```

### 2. Use Glob Patterns

**Good:** Efficient pattern matching
```
"Find all test files matching tests/**/test_*.py"
```

**Bad:** Manual directory traversal
```
"List all directories and find test files"
```

### 3. Leverage Grep Prefiltering

The grep tool uses fast-glob prefiltering:

```python
# Efficient: Prefilters to .py files only
"Search for 'class Database' in all Python files"

# Less efficient: Searches all files
"Search for 'class Database' in all files"
```

### 4. Context Window Management

Monitor token usage to prevent overflow:

```bash
# Context window display shows:
Context: ████████████████░░░░ 80% (160,000/200,000 tokens)

# Use /compact to summarize when getting full
/compact
```

## Caching Strategies

### 1. Import Cache

TunaCode caches Python imports for faster subsequent loads:

```python
# First use: ~500ms
from heavy_library import process

# Subsequent uses: ~1ms (cached)
from heavy_library import process
```

### 2. File Reading Optimization

The file reading tools implement smart caching:

```python
# Encoding detection cached per file
# UTF-8 attempted first (most common)
# Fallback to chardet only when needed
```

### 3. Agent Instance Caching

Agents are cached per model to avoid recreation:

```python
# First request with gpt-4: Creates new agent
# Subsequent gpt-4 requests: Reuses cached agent
# Switching models: Creates new agent (cached separately)
```

## Memory Management

### 1. Message History Pruning

Use `/compact` to reduce memory usage:

```bash
# Before: 50 messages, 180k tokens
/compact

# After: 5 messages, 20k tokens (summary retained)
```

### 2. Large File Handling

For large files, use offset/limit:

```python
# In your tool implementation
async def run(self, file_path: str, offset: int = 0, limit: int = 1000):
    # Read only a portion of the file
    lines = content.splitlines()[offset:offset+limit]
```

### 3. Streaming Responses

Enable streaming to reduce memory for long outputs:

```bash
# Streaming enabled (default)
/streaming on

# Processes and displays output incrementally
# Lower memory usage for long responses
```

## Tool Performance Optimization

### 1. Grep Tool Optimizations

The grep tool implements several optimizations:

```python
# 3-second timeout for first match
# MAX_GLOB prefiltering (10,000 file limit)
# Ripgrep backend for speed
```

### 2. Efficient File Operations

```python
# Good: Use glob for pattern matching
files = await glob_tool.run(pattern="**/*.py")

# Bad: List all files then filter
all_files = await list_dir_tool.run()
py_files = [f for f in all_files if f.endswith('.py')]
```

### 3. Batch Write Operations

When updating multiple files:

```python
# Group related updates
"Update all import statements in the module files"

# Better than individual updates
"Update imports in file1.py"
"Update imports in file2.py"
```

## Async Performance Patterns

### 1. Concurrent Operations

```python
# Good: Concurrent execution
async def process_files(files: List[str]):
    tasks = [process_file(f) for f in files]
    results = await asyncio.gather(*tasks)
    return results

# Bad: Sequential execution
async def process_files(files: List[str]):
    results = []
    for f in files:
        result = await process_file(f)
        results.append(result)
    return results
```

### 2. Async Context Managers

```python
# Efficient resource management
async with aiofiles.open(file_path) as f:
    content = await f.read()
    # File automatically closed

# Prevents resource leaks
```

### 3. Task Cancellation

```python
# Support cancellation for long operations
async def long_operation():
    for i in range(1000):
        if asyncio.current_task().cancelled():
            break
        await process_item(i)
        await asyncio.sleep(0)  # Yield control
```

## Performance Monitoring

### 1. Token Usage Tracking

Monitor token usage and costs:

```python
# After each request
Tokens: 2,451 (≈$0.0073) | Total: 45,234 (≈$0.1357)
```

### 2. Execution Time Logging

Enable debug logging for timing:

```bash
LOG_LEVEL=DEBUG tunacode

# Logs show execution times:
[DEBUG] Tool execution completed in 0.234s
[DEBUG] Parallel batch completed in 0.456s (3 tools)
```

### 3. Performance Commands

Use debug commands to analyze performance:

```bash
# Show iteration usage
/iterations

# Display message token counts
/dump

# Analyze tool usage patterns
/analytics tools
```

## Configuration Tuning

### 1. Optimal Parallel Settings

```bash
# For I/O bound operations (file reading)
export TUNACODE_MAX_PARALLEL=16

# For CPU bound operations
export TUNACODE_MAX_PARALLEL=$(($(nproc) * 2))

# For memory constrained systems
export TUNACODE_MAX_PARALLEL=4
```

### 2. Context Window Settings

Adjust in configuration:

```json
{
    "context_window": 200000,
    "max_response_tokens": 4096,
    "max_iterations": 20
}
```

### 3. Model Selection

Choose models based on performance needs:

| Model | Speed | Context | Cost | Best For |
|-------|-------|---------|------|----------|
| gpt-4o-mini | Fast | 128k | Low | Simple tasks |
| claude-3-haiku | Very Fast | 200k | Low | Quick operations |
| gpt-4o | Medium | 128k | Medium | Complex tasks |
| claude-3.5-sonnet | Medium | 200k | Medium | Coding tasks |

## Common Performance Issues

### 1. Slow File Operations

**Problem:** File operations taking too long

**Solutions:**
- Use glob patterns instead of recursive listing
- Enable parallel execution
- Implement file filtering at the tool level

### 2. Context Window Overflow

**Problem:** Running out of context space

**Solutions:**
- Use `/compact` regularly
- Break large tasks into smaller chunks
- Clear message history with `/clear all`

### 3. High Memory Usage

**Problem:** TunaCode using excessive memory

**Solutions:**
- Limit message history
- Use streaming for large outputs
- Implement pagination for large results

### 4. Slow Tool Execution

**Problem:** Individual tools running slowly

**Solutions:**
- Add timeouts to prevent hanging
- Use async operations properly
- Cache expensive computations

## Performance Testing

### 1. Benchmark Tool Execution

```python
# Create a benchmark script
import time
import asyncio
from tunacode.tools.read_file import ReadFileTool

async def benchmark_parallel():
    tool = ReadFileTool(mock_ui)
    files = ["file1.py", "file2.py", "file3.py"]

    start = time.time()
    tasks = [tool.run(file_path=f) for f in files]
    await asyncio.gather(*tasks)
    parallel_time = time.time() - start

    print(f"Parallel: {parallel_time:.3f}s")
```

### 2. Profile Memory Usage

```bash
# Use memory_profiler
pip install memory_profiler
python -m memory_profiler your_script.py
```

### 3. Analyze Token Usage

```python
# Track token usage patterns
from tunacode.utils.token_counter import TokenCounter

counter = TokenCounter()
tokens = counter.count_tokens(text, model="gpt-4")
print(f"Tokens: {tokens}")
```

## Advanced Optimizations

### 1. Custom Thread Pool

For CPU-intensive operations:

```python
import concurrent.futures

class OptimizedTool(BaseTool):
    def __init__(self, ui):
        super().__init__(ui)
        self.executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=4
        )

    async def run(self, **kwargs):
        # Offload CPU work to thread pool
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            self.executor,
            self.cpu_intensive_work,
            kwargs
        )
        return result
```

### 2. Connection Pooling

For tools making HTTP requests:

```python
class APITool(BaseTool):
    def __init__(self, ui):
        super().__init__(ui)
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, *args):
        await self.session.close()

    async def run(self, url: str):
        async with self.session.get(url) as response:
            return await response.text()
```

### 3. Result Streaming

For large results:

```python
async def run(self, query: str):
    # Stream results instead of loading all
    async for chunk in self.process_query_stream(query):
        await self.ui.print(chunk)

    return "Streaming complete"
```

## Performance Checklist

Before deploying or sharing tools:

- [ ] Test with large inputs
- [ ] Verify parallel execution works correctly
- [ ] Add appropriate timeouts
- [ ] Implement proper error handling
- [ ] Cache expensive operations
- [ ] Use async/await properly
- [ ] Handle cancellation gracefully
- [ ] Monitor memory usage
- [ ] Profile execution time
- [ ] Document performance characteristics

## Future Performance Improvements

Planned optimizations:

1. **Incremental Parsing**: Stream-parse large files
2. **Smart Caching**: LRU cache for file operations
3. **Predictive Loading**: Pre-fetch likely files
4. **GPU Acceleration**: For compatible operations
5. **Distributed Execution**: Multi-machine tool execution

## Summary

Key performance principles:

1. **Batch Operations**: Group related operations
2. **Use Parallelism**: Leverage parallel tool execution
3. **Manage Context**: Keep context window under control
4. **Cache Wisely**: Cache expensive operations
5. **Monitor Usage**: Track tokens and execution time
6. **Optimize Tools**: Write efficient tool implementations

Following these guidelines ensures TunaCode remains responsive and efficient even with complex workloads.
