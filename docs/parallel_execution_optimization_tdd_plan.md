# Parallel Execution Optimization: TDD Implementation Plan

## Overview

This document outlines a phased, test-driven development (TDD) approach to optimize TunaCode's parallel execution system. Each phase follows the TDD cycle: Red → Green → Refactor.

## Core TDD Principles

1. **Write the test first** - Define expected behavior before implementation
2. **Make it fail** - Ensure the test fails initially (Red)
3. **Make it pass** - Write minimal code to pass the test (Green)
4. **Refactor** - Improve code quality while keeping tests green
5. **Small iterations** - Each phase delivers measurable improvement

## Phase 1: Async I/O Foundation (Week 1)

### 1.1 Test Infrastructure Setup

```python
# tests/test_async_file_operations.py

import asyncio
import pytest
from unittest.mock import patch, mock_open

class TestAsyncFileOperations:
    @pytest.mark.asyncio
    async def test_read_file_is_truly_async(self):
        """Verify multiple file reads execute concurrently"""
        # GIVEN: 3 files that each take 100ms to read
        read_delays = []

        async def mock_read_with_delay(filepath):
            read_delays.append(filepath)
            await asyncio.sleep(0.1)  # Simulate 100ms read
            return f"content of {filepath}"

        # WHEN: Reading 3 files in parallel
        start_time = asyncio.get_event_loop().time()
        results = await read_files_parallel([
            "file1.txt", "file2.txt", "file3.txt"
        ])
        elapsed = asyncio.get_event_loop().time() - start_time

        # THEN: Total time should be ~100ms, not 300ms
        assert elapsed < 0.15  # Allow some overhead
        assert len(results) == 3
        assert all(filepath in read_delays for filepath in ["file1.txt", "file2.txt", "file3.txt"])
```

### 1.2 Implementation Steps

1. **Red Phase**: Write tests for async file operations
   - Test concurrent execution timing
   - Test error handling in async context
   - Test resource cleanup

2. **Green Phase**: Implement async wrappers
   ```python
   # src/tunacode/tools/async_io.py
   async def read_file_async(filepath: str) -> str:
       """True async file read using thread pool"""
       return await asyncio.to_thread(
           lambda: open(filepath, 'r').read()
       )
   ```

3. **Refactor Phase**: Extract common patterns
   - Create `AsyncFileHandler` class
   - Implement proper error handling
   - Add logging and metrics

### 1.3 Acceptance Criteria

- [ ] All file operations use async I/O
- [ ] 3x performance improvement verified by tests
- [ ] No blocking operations in event loop
- [ ] Backward compatibility maintained

## Phase 2: Shared Thread Pool Management (Week 2)

### 2.1 Thread Pool Tests

```python
# tests/test_thread_pool_manager.py

class TestThreadPoolManager:
    @pytest.mark.asyncio
    async def test_shared_pool_resource_efficiency(self):
        """Verify shared pool uses fewer resources than multiple pools"""
        # GIVEN: A shared thread pool manager
        manager = ThreadPoolManager(max_workers=5)

        # WHEN: Executing 10 concurrent operations
        tasks = [
            manager.run_io_task(lambda: expensive_io_operation(i))
            for i in range(10)
        ]
        results = await asyncio.gather(*tasks)

        # THEN: Only 5 threads should be active at peak
        assert manager.peak_thread_count <= 5
        assert len(results) == 10
        assert manager.total_tasks_executed == 10
```

### 2.2 Implementation Steps

1. **Red Phase**: Define thread pool behavior tests
   - Test pool size limits
   - Test task queueing
   - Test graceful shutdown

2. **Green Phase**: Implement ThreadPoolManager
   ```python
   class ThreadPoolManager:
       def __init__(self, io_workers=10, cpu_workers=4):
           self.io_pool = ThreadPoolExecutor(max_workers=io_workers)
           self.cpu_pool = ThreadPoolExecutor(max_workers=cpu_workers)

       async def run_io_task(self, func, *args):
           loop = asyncio.get_event_loop()
           return await loop.run_in_executor(self.io_pool, func, *args)
   ```

3. **Refactor Phase**: Optimize pool usage
   - Add pool selection logic (I/O vs CPU)
   - Implement pool warming
   - Add metrics collection

### 2.3 Acceptance Criteria

- [ ] Single shared pool for all I/O operations
- [ ] Separate pool for CPU-bound tasks
- [ ] Resource usage reduced by 50%
- [ ] No thread pool exhaustion under load

## Phase 3: Smart Caching Layer (Week 3)

### 3.1 Cache Behavior Tests

```python
# tests/test_smart_cache.py

class TestSmartCache:
    @pytest.mark.asyncio
    async def test_cache_hit_performance(self):
        """Verify cached reads are 100x faster"""
        cache = SmartCache(max_size=100)

        # GIVEN: A file read that takes 100ms
        @cache.cached
        async def read_slow_file(filepath):
            await asyncio.sleep(0.1)
            return f"content of {filepath}"

        # WHEN: Reading the same file twice
        start1 = asyncio.get_event_loop().time()
        result1 = await read_slow_file("test.txt")
        time1 = asyncio.get_event_loop().time() - start1

        start2 = asyncio.get_event_loop().time()
        result2 = await read_slow_file("test.txt")
        time2 = asyncio.get_event_loop().time() - start2

        # THEN: Second read should be nearly instant
        assert time1 > 0.09  # First read takes ~100ms
        assert time2 < 0.001  # Cached read < 1ms
        assert result1 == result2
```

### 3.2 Implementation Steps

1. **Red Phase**: Write cache requirement tests
   - Test cache hits/misses
   - Test TTL expiration
   - Test file modification detection
   - Test memory limits

2. **Green Phase**: Implement SmartCache
   ```python
   class SmartCache:
       def __init__(self, max_size=100, ttl=300):
           self._cache = {}
           self._access_times = {}
           self._file_mtimes = {}

       async def get_or_compute(self, key, compute_func):
           if self._is_valid_cache_entry(key):
               return self._cache[key]

           value = await compute_func()
           self._store(key, value)
           return value
   ```

3. **Refactor Phase**: Add intelligence
   - LRU eviction policy
   - Predictive prefetching
   - Cache warming strategies

### 3.3 Acceptance Criteria

- [ ] 100x faster for cached reads
- [ ] Automatic invalidation on file changes
- [ ] Memory usage stays under limit
- [ ] Cache hit rate > 80% in typical usage

## Phase 4: Enhanced Parallel Executor (Week 4)

### 4.1 Advanced Execution Tests

```python
# tests/test_enhanced_executor.py

class TestEnhancedExecutor:
    @pytest.mark.asyncio
    async def test_semaphore_prevents_overload(self):
        """Verify semaphore limits concurrent operations"""
        executor = EnhancedParallelExecutor(max_concurrent=3)

        # GIVEN: 10 tasks submitted simultaneously
        active_count = 0
        max_active = 0

        async def tracked_task(task_id):
            nonlocal active_count, max_active
            active_count += 1
            max_active = max(max_active, active_count)
            await asyncio.sleep(0.1)
            active_count -= 1
            return task_id

        # WHEN: Executing all tasks
        tasks = [executor.execute(tracked_task, i) for i in range(10)]
        results = await asyncio.gather(*tasks)

        # THEN: Never more than 3 active at once
        assert max_active <= 3
        assert len(results) == 10
```

### 4.2 Implementation Steps

1. **Red Phase**: Define advanced execution tests
   - Test concurrency limits
   - Test priority scheduling
   - Test failure isolation
   - Test progress reporting

2. **Green Phase**: Build EnhancedExecutor
   ```python
   class EnhancedParallelExecutor:
       def __init__(self, max_concurrent=4):
           self._semaphore = asyncio.Semaphore(max_concurrent)
           self._queue = PriorityQueue()

       async def execute(self, func, *args, priority=1):
           async with self._semaphore:
               return await func(*args)
   ```

3. **Refactor Phase**: Add sophisticated features
   - Dynamic concurrency adjustment
   - Execution time prediction
   - Smart batching algorithms

### 4.3 Acceptance Criteria

- [ ] Predictable performance under load
- [ ] No resource exhaustion
- [ ] Graceful degradation
- [ ] Progress visibility

## Phase 5: Performance Monitoring & Optimization (Week 5)

### 5.1 Monitoring Tests

```python
# tests/test_performance_monitor.py

class TestPerformanceMonitor:
    @pytest.mark.asyncio
    async def test_metrics_collection(self):
        """Verify accurate performance metrics"""
        monitor = PerformanceMonitor()

        # GIVEN: Monitored operations
        @monitor.track
        async def slow_operation():
            await asyncio.sleep(0.1)
            return "done"

        # WHEN: Executing operations
        for _ in range(5):
            await slow_operation()

        # THEN: Metrics should be accurate
        stats = monitor.get_stats("slow_operation")
        assert stats.count == 5
        assert 0.09 < stats.avg_duration < 0.11
        assert stats.p95 < 0.12
```

### 5.2 Implementation Steps

1. **Red Phase**: Define monitoring requirements
   - Test metric accuracy
   - Test overhead is minimal
   - Test metric aggregation

2. **Green Phase**: Implement monitoring
   ```python
   class PerformanceMonitor:
       def track(self, func):
           @functools.wraps(func)
           async def wrapper(*args, **kwargs):
               start = time.perf_counter()
               try:
                   result = await func(*args, **kwargs)
                   self._record_success(func.__name__, time.perf_counter() - start)
                   return result
               except Exception as e:
                   self._record_failure(func.__name__, time.perf_counter() - start, e)
                   raise
           return wrapper
   ```

3. **Refactor Phase**: Add analytics
   - Anomaly detection
   - Trend analysis
   - Auto-optimization hints

### 5.3 Acceptance Criteria

- [ ] < 1% performance overhead
- [ ] Real-time metrics available
- [ ] Historical trend analysis
- [ ] Actionable optimization suggestions

## Integration Test Suite

### End-to-End Performance Tests

```python
# tests/test_e2e_performance.py

class TestE2EPerformance:
    @pytest.mark.asyncio
    async def test_full_system_performance(self):
        """Verify complete system meets performance targets"""
        # GIVEN: A typical workload
        workload = [
            ("read_file", "src/main.py"),
            ("read_file", "src/config.py"),
            ("grep", "TODO", "src/"),
            ("list_dir", "tests/"),
        ]

        # WHEN: Executing with optimized system
        start = time.perf_counter()
        results = await execute_parallel_optimized(workload)
        duration = time.perf_counter() - start

        # THEN: Should be 5-10x faster than baseline
        baseline_duration = await execute_sequential(workload)
        speedup = baseline_duration / duration

        assert speedup >= 5.0
        assert duration < 0.2  # All 4 operations < 200ms
        assert len(results) == 4
```

## Rollout Strategy

### Week 1-2: Foundation
- Implement async I/O and shared thread pools
- Target: 2x additional performance gain

### Week 3: Intelligence
- Add smart caching layer
- Target: 100x improvement for repeated operations

### Week 4: Sophistication
- Enhanced parallel executor
- Target: Predictable performance at scale

### Week 5: Polish
- Performance monitoring and optimization
- Target: Data-driven continuous improvement

## Success Metrics

1. **Performance**: 5-10x overall improvement vs current implementation
2. **Reliability**: Zero regressions, 100% backward compatibility
3. **Observability**: Full visibility into performance characteristics
4. **Maintainability**: Clean, tested, documented code

## Risk Mitigation

1. **Feature Flags**: Each optimization behind a flag
2. **Gradual Rollout**: Test with small % of operations first
3. **Rollback Plan**: Easy disable for any optimization
4. **Monitoring**: Detect issues before users notice

## Conclusion

This TDD approach ensures each optimization is:
- Properly tested before implementation
- Measurably improving performance
- Not breaking existing functionality
- Easy to understand and maintain

By following this plan, we'll deliver a 5-10x performance improvement while maintaining code quality and reliability.
