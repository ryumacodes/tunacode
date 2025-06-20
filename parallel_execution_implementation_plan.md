# Implementation Plan: Parallel Execution Optimization

## Overview

This plan outlines the steps to optimize TunaCode's parallel execution system to achieve better performance through true async I/O and improved resource management.

## Phase 1: Foundation (Quick Wins)

### 1.1 Create Shared Thread Pool Infrastructure

**File**: `src/tunacode/core/thread_pool.py`
```python
"""Shared thread pool for I/O operations."""

import os
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

_IO_THREAD_POOL: Optional[ThreadPoolExecutor] = None
_CPU_THREAD_POOL: Optional[ThreadPoolExecutor] = None


def get_io_thread_pool() -> ThreadPoolExecutor:
    """Get or create the shared I/O thread pool."""
    global _IO_THREAD_POOL
    if _IO_THREAD_POOL is None:
        max_workers = min(32, (os.cpu_count() or 1) * 4)
        _IO_THREAD_POOL = ThreadPoolExecutor(
            max_workers=max_workers,
            thread_name_prefix="tunacode-io"
        )
    return _IO_THREAD_POOL


def get_cpu_thread_pool() -> ThreadPoolExecutor:
    """Get or create the shared CPU-bound thread pool."""
    global _CPU_THREAD_POOL
    if _CPU_THREAD_POOL is None:
        max_workers = os.cpu_count() or 1
        _CPU_THREAD_POOL = ThreadPoolExecutor(
            max_workers=max_workers,
            thread_name_prefix="tunacode-cpu"
        )
    return _CPU_THREAD_POOL
```

### 1.2 Update read_file Tool

**File**: `src/tunacode/tools/read_file.py`

Add async I/O support:
```python
import asyncio
from tunacode.core.thread_pool import get_io_thread_pool

async def _read_file_async(self, filepath: str) -> str:
    """Read file contents without blocking the event loop."""
    
    def _read_sync():
        with open(filepath, "r", encoding="utf-8") as file:
            return file.read()
    
    loop = asyncio.get_event_loop()
    executor = get_io_thread_pool()
    return await loop.run_in_executor(executor, _read_sync)
```

### 1.3 Update list_dir Tool

**File**: `src/tunacode/tools/list_dir.py`

Make directory scanning async:
```python
async def _scan_directory_async(self, dir_path: Path) -> List[Tuple[str, bool, str]]:
    """Scan directory without blocking the event loop."""
    
    def _scan_sync():
        entries = []
        with os.scandir(dir_path) as scanner:
            for entry in scanner:
                # ... existing processing logic
                entries.append((entry.name, is_directory, type_indicator))
        return entries
    
    loop = asyncio.get_event_loop()
    executor = get_io_thread_pool()
    return await loop.run_in_executor(executor, _scan_sync)
```

### 1.4 Update grep Tool

**File**: `src/tunacode/tools/grep.py`

Replace instance thread pool with shared pool:
```python
from tunacode.core.thread_pool import get_cpu_thread_pool

class ParallelGrep(BaseTool):
    def __init__(self, ui_logger=None):
        super().__init__(ui_logger)
        # Remove: self._executor = ThreadPoolExecutor(max_workers=8)
    
    @property
    def _executor(self):
        """Use shared CPU thread pool."""
        return get_cpu_thread_pool()
```

## Phase 2: Enhanced Parallel Execution

### 2.1 Implement Semaphore-based Concurrency Control

**File**: `src/tunacode/core/agents/main.py`

Update `execute_tools_parallel`:
```python
async def execute_tools_parallel_enhanced(
    tool_calls: List[Tuple[Any, Any]], 
    callback: ToolCallback,
    return_exceptions: bool = True
) -> List[Any]:
    """
    Execute multiple tool calls in parallel with better resource management.
    
    Uses semaphores to control concurrency and prevent resource exhaustion.
    """
    # Get max parallel from environment or default to CPU count
    max_parallel = int(os.environ.get("TUNACODE_MAX_PARALLEL", os.cpu_count() or 4))
    
    # Create semaphore for concurrency control
    semaphore = asyncio.Semaphore(max_parallel)
    
    async def execute_with_control(part, node):
        """Execute tool with semaphore control and error handling."""
        async with semaphore:
            try:
                # Add timing for performance monitoring
                start_time = asyncio.get_event_loop().time()
                result = await callback(part, node)
                elapsed = asyncio.get_event_loop().time() - start_time
                
                # Log slow operations
                if elapsed > 1.0:
                    import logging
                    logging.debug(f"Slow tool execution: {part.tool_name} took {elapsed:.2f}s")
                
                return result
            except Exception as e:
                if return_exceptions:
                    return e
                raise
    
    # Create all tasks at once (more efficient than batching)
    tasks = [
        asyncio.create_task(execute_with_control(part, node), name=f"tool_{part.tool_name}")
        for part, node in tool_calls
    ]
    
    # Wait for all to complete
    return await asyncio.gather(*tasks, return_exceptions=return_exceptions)
```

### 2.2 Add Performance Monitoring

**File**: `src/tunacode/core/performance.py`
```python
"""Performance monitoring utilities."""

import asyncio
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Dict, List

@dataclass
class ToolMetrics:
    tool_name: str
    execution_time: float
    timestamp: float
    success: bool
    
class PerformanceMonitor:
    def __init__(self):
        self.metrics: List[ToolMetrics] = []
        
    @asynccontextmanager
    async def measure_tool(self, tool_name: str):
        """Context manager to measure tool execution time."""
        start_time = time.time()
        success = True
        
        try:
            yield
        except Exception:
            success = False
            raise
        finally:
            execution_time = time.time() - start_time
            self.metrics.append(ToolMetrics(
                tool_name=tool_name,
                execution_time=execution_time,
                timestamp=start_time,
                success=success
            ))
    
    def get_summary(self) -> Dict[str, any]:
        """Get performance summary."""
        if not self.metrics:
            return {}
            
        tool_times = {}
        for metric in self.metrics:
            if metric.tool_name not in tool_times:
                tool_times[metric.tool_name] = []
            tool_times[metric.tool_name].append(metric.execution_time)
        
        summary = {}
        for tool, times in tool_times.items():
            summary[tool] = {
                'count': len(times),
                'total_time': sum(times),
                'avg_time': sum(times) / len(times),
                'max_time': max(times),
                'min_time': min(times)
            }
        
        return summary
```

## Phase 3: Advanced Optimizations

### 3.1 Implement Result Caching

**File**: `src/tunacode/core/cache.py`
```python
"""Simple LRU cache for read-only tool results."""

import time
import os
from typing import Dict, Tuple, Optional
from dataclasses import dataclass

@dataclass
class CacheEntry:
    value: any
    timestamp: float
    file_stat: Optional[os.stat_result] = None

class ToolResultCache:
    def __init__(self, max_size: int = 128, ttl_seconds: int = 300):
        self.cache: Dict[str, CacheEntry] = {}
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.access_order: List[str] = []
    
    def get(self, key: str, filepath: Optional[str] = None) -> Optional[any]:
        """Get cached value if valid."""
        if key not in self.cache:
            return None
            
        entry = self.cache[key]
        
        # Check TTL
        if time.time() - entry.timestamp > self.ttl_seconds:
            del self.cache[key]
            self.access_order.remove(key)
            return None
        
        # Check file modification for file-based tools
        if filepath and entry.file_stat:
            try:
                current_stat = os.stat(filepath)
                if (current_stat.st_mtime != entry.file_stat.st_mtime or
                    current_stat.st_size != entry.file_stat.st_size):
                    del self.cache[key]
                    self.access_order.remove(key)
                    return None
            except OSError:
                del self.cache[key]
                self.access_order.remove(key)
                return None
        
        # Move to end (most recently used)
        self.access_order.remove(key)
        self.access_order.append(key)
        
        return entry.value
    
    def put(self, key: str, value: any, filepath: Optional[str] = None):
        """Store value in cache."""
        # Remove oldest if at capacity
        if len(self.cache) >= self.max_size and key not in self.cache:
            oldest = self.access_order[0]
            del self.cache[oldest]
            self.access_order.pop(0)
        
        # Get file stat if filepath provided
        file_stat = None
        if filepath:
            try:
                file_stat = os.stat(filepath)
            except OSError:
                pass
        
        # Store entry
        self.cache[key] = CacheEntry(
            value=value,
            timestamp=time.time(),
            file_stat=file_stat
        )
        
        if key in self.access_order:
            self.access_order.remove(key)
        self.access_order.append(key)

# Global cache instance
_tool_cache = ToolResultCache()

def get_tool_cache() -> ToolResultCache:
    return _tool_cache
```

### 3.2 Update Tools to Use Caching

Example for read_file:
```python
from tunacode.core.cache import get_tool_cache

async def _execute(self, filepath: str) -> ToolResult:
    # Check cache first
    cache = get_tool_cache()
    cache_key = f"read_file:{filepath}"
    cached_content = cache.get(cache_key, filepath)
    
    if cached_content is not None:
        return cached_content
    
    # ... existing read logic ...
    content = await self._read_file_async(filepath)
    
    # Cache the result
    cache.put(cache_key, content, filepath)
    
    return content
```

## Testing Plan

### Unit Tests

1. **Thread Pool Tests** (`tests/test_thread_pool.py`)
   - Test singleton behavior
   - Test thread pool size limits
   - Test concurrent access

2. **Async Tool Tests** (`tests/test_async_tools.py`)
   - Test async file reading
   - Test async directory listing
   - Test error handling in async context

3. **Cache Tests** (`tests/test_tool_cache.py`)
   - Test LRU eviction
   - Test TTL expiration
   - Test file modification detection

### Integration Tests

1. **Parallel Execution Tests** (`tests/test_parallel_execution_enhanced.py`)
   - Test semaphore-based concurrency
   - Test mixed read/write operations
   - Test error propagation

2. **Performance Tests** (`tests/test_performance.py`)
   - Benchmark async vs sync tools
   - Test scaling with many files
   - Memory usage tests

### Load Tests

Create `tests/load_test_parallel.py`:
```python
import asyncio
import tempfile
import time

async def load_test_parallel_reads():
    """Test system under heavy parallel load."""
    
    # Create 100 test files
    files = []
    with tempfile.TemporaryDirectory() as tmpdir:
        for i in range(100):
            filepath = f"{tmpdir}/test_{i}.txt"
            with open(filepath, 'w') as f:
                f.write(f"Content {i}\n" * 100)
            files.append(filepath)
        
        # Test parallel reads
        from tunacode.tools.read_file import read_file_async
        
        start_time = time.time()
        tasks = [read_file_async(f) for f in files]
        results = await asyncio.gather(*tasks)
        elapsed = time.time() - start_time
        
        print(f"Read 100 files in {elapsed:.2f}s")
        print(f"Average: {elapsed/100:.3f}s per file")
        print(f"Throughput: {100/elapsed:.1f} files/second")
```

## Rollout Strategy

### Phase 1: Foundation (Week 1)
- Implement shared thread pools
- Update read_file and list_dir tools
- Basic testing

### Phase 2: Enhanced Execution (Week 2)
- Implement semaphore-based concurrency
- Add performance monitoring
- Integration testing

### Phase 3: Advanced Features (Week 3)
- Implement caching
- Performance optimization
- Load testing and benchmarking

### Phase 4: Production Readiness (Week 4)
- Documentation updates
- Migration guide
- Performance tuning based on test results

## Configuration Options

Add to environment variables:
```bash
# Maximum parallel operations (default: CPU count)
export TUNACODE_MAX_PARALLEL=8

# I/O thread pool size (default: CPU count * 4, max 32)
export TUNACODE_IO_THREADS=16

# CPU thread pool size (default: CPU count)
export TUNACODE_CPU_THREADS=4

# Enable/disable result caching (default: true)
export TUNACODE_ENABLE_CACHE=true

# Cache TTL in seconds (default: 300)
export TUNACODE_CACHE_TTL=300

# Performance monitoring (default: false)
export TUNACODE_PERF_MONITORING=true
```

## Success Metrics

1. **Performance**: 
   - 5x improvement for multiple file reads
   - <10ms overhead for cache hits
   - Linear scaling up to 100 parallel operations

2. **Reliability**:
   - No increase in error rates
   - Graceful degradation under load
   - Proper cleanup of resources

3. **Resource Usage**:
   - Memory usage <100MB for thread pools
   - CPU usage scales with operations
   - No thread leaks

## Risk Mitigation

1. **Backward Compatibility**:
   - Keep existing interfaces unchanged
   - Add feature flags for new behavior
   - Provide migration documentation

2. **Resource Exhaustion**:
   - Implement semaphore limits
   - Monitor thread pool sizes
   - Add circuit breakers for overload

3. **Error Handling**:
   - Comprehensive error propagation
   - Detailed logging for debugging
   - Graceful fallback to sync mode