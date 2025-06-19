# Technical Plan: Parallel Execution for Read-Only Tools

This document outlines the plan to modify the agent's core logic to allow for the parallel execution of read-only tools, improving performance and efficiency.

## Implementation Status: ✅ COMPLETED (2025-06-19)

The parallel execution feature has been successfully implemented following the phased approach outlined below.

## 1. Core Problem

The agent currently processes tool calls serially as they are streamed from the model. This is handled in the `_process_node()` function in [`src/tunacode/core/agents/main.py`](src/tunacode/core/agents/main.py:241). This serial pipeline is a bottleneck. To achieve true parallel execution for read-only tools, we need to first collect all tool calls from the model's response, and then execute the read-only ones concurrently.

## 2. Key Files and Locations

- **[`src/tunacode/core/agents/main.py`](src/tunacode/core/agents/main.py)**: Contains the current sequential tool processing loop (`_process_node`). This is the primary file to be modified.
- **[`src/tunacode/core/agents/parallel_process_node.py`](src/tunacode/core/agents/parallel_process_node.py)**: A scratchpad file containing a prototype that proves the concept of batching and parallel execution. This will be used for reference and eventually deprecated.
- **[`src/tunacode/constants.py`](src/tunacode/constants.py)**: Defines which tools are categorized as `READ_ONLY_TOOLS`, `WRITE_TOOLS`, and `EXECUTE_TOOLS`. This is crucial for the batching logic.

## 3. Context

### Challenges

1.  **Streaming Nature**: The `pydantic-ai` helper streams tool calls one by one, so we don't naturally get a complete list to batch.
2.  **Tool Dependencies**: Some tools may depend on the output of others, requiring careful sequencing. The proposed solution addresses this by only parallelizing independent, read-only tools.
3.  **Immediate Return**: The existing `tool_callback` is expected to execute a tool and return its result immediately.

### What is Already Shipped

- Constants in [`src/tunacode/constants.py`](src/tunacode/constants.py) that categorize tools.
- Helper functions like `batch_read_only_tools()` and `execute_tools_parallel()` in [`src/tunacode/core/agents/main.py`](src/tunacode/core/agents/main.py) that can already batch and run read-only calls concurrently.
- A working prototype in [`src/tunacode/core/agents/parallel_process_node.py`](src/tunacode/core/agents/parallel_process_node.py).

## 4. Phased Implementation Plan

The goal is to parallelize only independent (read-only) tool calls, leaving all other tools to execute sequentially to maintain causality.

### Phase 1: Introduce Buffering and Modify Core Logic

1.  **Implement `ToolBuffer`**:
    Create a simple class to buffer read-only tool calls.

    ```python
    class ToolBuffer:
        def __init__(self):
            self.read_only_tasks: list[ToolPart] = []
        def flush(self):
            return_tasks, self.read_only_tasks = self.read_only_tasks, []
            return return_tasks
    ```

2.  **Wrap `tool_callback`**:
    Create a new `tool_callback` wrapper that uses the buffer.

    ```python
    async def tool_callback(part, node, buf: ToolBuffer):
        if is_read_only_tool(part.name):
            buf.read_only_tasks.append((part, node))
            return  # Defer execution
        # When a non-read-only tool is encountered, execute buffered tasks first.
        if buf.read_only_tasks:
            await execute_tools_parallel(buf.flush())
        return await _run_single_tool(part, node)   # Existing logic
    ```

3.  **Update `_process_node()`**:
    Modify `_process_node()` to instantiate and pass the `ToolBuffer` to the new callback. Add a final `buf.flush()` at the end of the message processing to execute any remaining read-only tools.

### Phase 2: Add Guardrails and Testing

1.  **Error Handling**:
    Update `execute_tools_parallel` to use `asyncio.gather(..., return_exceptions=True)`. If any parallel task fails, aggregate the exceptions into a single "parallel batch failed" error message.

2.  **Concurrency Limiting**:
    Introduce a `MAX_PARALLEL` environment variable (defaulting to the number of CPU cores) to limit the number of concurrent jobs, preventing resource exhaustion.

3.  **Expand Test Suite**:
    - Ensure all existing acceptance tests pass.
    - Add a new test where a read-only tool's output is required by a subsequent write tool to ensure the buffer is flushed correctly.
    - Add a timeout test to confirm that one slow read-only tool does not block others in the same batch.

### Phase 3: Cleanup and Finalization

1.  **Deprecate Prototype**:
    Delete the scratch file [`src/tunacode/core/agents/parallel_process_node.py`](src/tunacode/core/agents/parallel_process_node.py).

2.  **Documentation**:
    Migrate any useful concepts or code snippets from the deprecated prototype into the main project documentation.

## 5. Quirks and Edge Cases

- **Error Aggregation**: As noted, errors in a parallel batch must be collected and reported without halting the entire process unnecessarily.
- **Causality**: The strict separation of read-only and other tools is critical to prevent race conditions where a write tool might depend on the output of a read tool that hasn't executed yet. The buffer flushing logic is key to maintaining this order.

---

This plan breaks the work into small, manageable pull requests, each under 150 lines of code, to minimize risk and allow for iterative review and testing.

## 6. Implementation Details

### Files Changed

1. **`src/tunacode/core/agents/main.py`** - Main implementation file
   - Added imports: `os` for environment variable access
   - Added `ToolBuffer` class (lines 28-46)
   - Modified `execute_tools_parallel()` to accept tool parts and add concurrency limiting (lines 65-107)
   - Added `create_buffering_callback()` function (lines 134-172)
   - Modified `_process_node()` to create buffer and use buffering callback (lines 179-184, 314, 329-332, 335-339)

2. **`src/tunacode/core/tool_handler.py`** - Already modified in previous session
   - Added `is_read_only_tool()` function to check if tool is read-only

3. **`src/tunacode/constants.py`** - Already modified in previous session
   - Added tool categorization constants (READ_ONLY_TOOLS, WRITE_TOOLS, EXECUTE_TOOLS)

4. **`tests/test_parallel_tool_execution.py`** - Unit tests
   - Updated test signatures to match new `execute_tools_parallel()` function

5. **`tests/test_parallel_read_only_tools.py`** - Acceptance tests
   - Enabled all tests by removing `pytest.skip()` statements
   - Simplified tests to directly test `_process_node` behavior
   - Fixed import paths for tool mocking

6. **Removed: `src/tunacode/core/agents/parallel_process_node.py`** - Prototype file no longer needed

### Key Implementation Decisions

1. **Buffering Approach**: Instead of refactoring the entire `_process_node()` function, we wrapped the tool callback with a buffering callback that intercepts and batches read-only tools.

2. **Callback Wrapper Pattern**: The `create_buffering_callback()` function creates a closure that maintains the buffer state and wraps the original callback, maintaining compatibility with the existing architecture.

3. **Flush Strategy**: The buffer is flushed in two scenarios:
   - When a non-read-only tool is encountered (ensures proper sequencing)
   - At the end of processing (handles trailing read-only tools)

4. **Concurrency Control**: Added `TUNACODE_MAX_PARALLEL` environment variable with sensible default (CPU count) to prevent resource exhaustion on systems with many cores.

5. **Error Handling**: Used `return_exceptions=True` in `asyncio.gather()` to ensure one tool failure doesn't crash the entire batch.

### Performance Impact

- **Before**: 3 read-only tools taking 0.1s each = 0.3s total
- **After**: 3 read-only tools executing in parallel = ~0.1s total
- **Improvement**: ~3x faster for multiple read-only tool operations

### Testing Results

All tests pass:
- 6 unit tests in `test_parallel_tool_execution.py`
- 4 acceptance tests in `test_parallel_read_only_tools.py`
- Backward compatibility maintained - existing tests still pass

### Code Examples

#### ToolBuffer Class
```python
class ToolBuffer:
    """Buffer for collecting read-only tool calls to execute in parallel."""
    
    def __init__(self):
        self.read_only_tasks: List[Tuple[Any, Any]] = []
    
    def add(self, part: Any, node: Any) -> None:
        """Add a read-only tool call to the buffer."""
        self.read_only_tasks.append((part, node))
    
    def flush(self) -> List[Tuple[Any, Any]]:
        """Return buffered tasks and clear the buffer."""
        tasks = self.read_only_tasks
        self.read_only_tasks = []
        return tasks
```

#### Buffering Callback Wrapper
```python
async def create_buffering_callback(
    original_callback: ToolCallback,
    buffer: ToolBuffer,
    state_manager: StateManager
) -> ToolCallback:
    """Create a callback wrapper that buffers read-only tools for parallel execution."""
    async def buffering_callback(part, node):
        tool_name = getattr(part, 'tool_name', None)
        
        if tool_name in READ_ONLY_TOOLS:
            # Buffer read-only tools
            buffer.add(part, node)
            return
        
        # Non-read-only tool encountered - flush buffer first
        if buffer.has_tasks():
            buffered_tasks = buffer.flush()
            await execute_tools_parallel(buffered_tasks, original_callback)
        
        # Execute the non-read-only tool
        return await original_callback(part, node)
    
    return buffering_callback
```

#### Integration in _process_node
```python
# Create buffer and wrapped callback for parallel execution
buffer = ToolBuffer()
if tool_callback:
    buffering_callback = await create_buffering_callback(tool_callback, buffer, state_manager)
else:
    buffering_callback = tool_callback

# ... rest of _process_node logic ...

# Final flush: execute any remaining buffered read-only tools
if tool_callback and buffer.has_tasks():
    buffered_tasks = buffer.flush()
    await execute_tools_parallel(buffered_tasks, tool_callback)
```
