# TunaCode Performance Improvement Plan

## Executive Summary
Current startup time: 3-5 seconds
Target startup time: < 1 second
Main bottleneck: Heavy synchronous imports and network I/O during startup

## Performance Analysis

### Startup Time Breakdown
- Total import time: ~0.813s
- Major contributors:
  - `pydantic_ai`: 359ms (44% of import time)
  - `typer`: 130ms (16% of import time)
  - `pydantic`: 37ms (5% of import time)
  - `prompt_toolkit`: 36ms (4% of import time)
- Additional overhead:
  - Update checking (network I/O): 1-3 seconds
  - Multiple setup steps running synchronously
  - Banner/UI rendering

## MVP Implementation

### Core Files to Modify

1. **Entry Point Optimization**
   - `/home/tuna/tunacode/src/tunacode/cli/main.py`
   - `/home/tuna/tunacode/src/tunacode/cli/repl.py`

2. **Lazy Loading Implementation**
   - `/home/tuna/tunacode/src/tunacode/core/agents/main.py`
   - `/home/tuna/tunacode/src/tunacode/tools/__init__.py`
   - `/home/tuna/tunacode/src/tunacode/services/mcp.py`

3. **Async/Background Operations**
   - `/home/tuna/tunacode/src/tunacode/utils/system.py`
   - `/home/tuna/tunacode/src/tunacode/core/setup/coordinator.py`

4. **Configuration Optimization**
   - `/home/tuna/tunacode/src/tunacode/core/setup/config_setup.py`
   - `/home/tuna/tunacode/src/tunacode/utils/user_configuration.py`

## Three-Phase Implementation Plan

### Phase 1: Quick Wins (1-2 days)
**Goal: Reduce startup by 50% with minimal changes**

1. **Defer Update Checking**
   - Move `check_for_updates()` to background thread
   - Only show update notification after REPL is ready
   - File: `/home/tuna/tunacode/src/tunacode/cli/main.py:41-43`

2. **Lazy Import Heavy Dependencies**
   - Import `pydantic_ai` only when creating agent
   - Import tool modules on-demand
   - Files: 
     - `/home/tuna/tunacode/src/tunacode/core/agents/main.py`
     - `/home/tuna/tunacode/src/tunacode/tools/__init__.py`

3. **Optimize Banner Display**
   - Pre-render banner as string constant
   - Remove async/await for simple prints
   - File: `/home/tuna/tunacode/src/tunacode/ui/console.py`

### Phase 2: Structural Improvements (3-5 days)
**Goal: Achieve < 1.5s startup time**

1. **Implement Import Caching**
   - Create import cache mechanism for heavy modules
   - Use `importlib.util.LazyLoader` for non-critical imports
   - New file: `/home/tuna/tunacode/src/tunacode/utils/import_cache.py`

2. **Parallelize Setup Steps**
   - Run independent setup steps concurrently
   - Use `asyncio.gather()` for parallel execution
   - File: `/home/tuna/tunacode/src/tunacode/core/setup/coordinator.py`

3. **Configuration Fast Path**
   - Cache parsed configuration in memory
   - Skip validation for known-good configs
   - Add config fingerprinting
   - Files:
     - `/home/tuna/tunacode/src/tunacode/core/setup/config_setup.py`
     - `/home/tuna/tunacode/src/tunacode/utils/user_configuration.py`

### Phase 3: Advanced Optimizations (1 week)
**Goal: Achieve < 1s startup time**

1. **Progressive Loading**
   - Load only essential components for REPL
   - Load tools/features on first use
   - Implement module-level `__getattr__` for lazy loading
   - New pattern across all tool modules

2. **Startup Profiling & Monitoring**
   - Add startup timing instrumentation
   - Create performance regression tests
   - New file: `/home/tuna/tunacode/src/tunacode/utils/performance.py`

3. **Pre-compilation & Bundling**
   - Use `py_compile` to pre-compile all modules
   - Consider using `Nuitka` or `mypyc` for critical paths
   - Update build process in `Makefile`

## Implementation Best Practices

### 1. Lazy Loading Pattern
```python
# Instead of:
from pydantic_ai import Agent

# Use:
def get_agent():
    from pydantic_ai import Agent
    return Agent
```

### 2. Background Tasks Pattern
```python
async def main():
    # Start background tasks
    update_task = asyncio.create_task(check_for_updates_async())
    
    # Continue with startup
    await quick_startup()
    
    # Check results later
    if update_task.done():
        handle_update_result(await update_task)
```

### 3. Import Caching Pattern
```python
_import_cache = {}

def lazy_import(module_name):
    if module_name not in _import_cache:
        _import_cache[module_name] = importlib.import_module(module_name)
    return _import_cache[module_name]
```

## Success Metrics

1. **Startup Time Targets**
   - Phase 1: < 2.5 seconds
   - Phase 2: < 1.5 seconds
   - Phase 3: < 1.0 second

2. **Performance Regression Prevention**
   - Automated startup time tests
   - CI/CD performance gates
   - Regular profiling reports

## Risk Mitigation

1. **Lazy Loading Risks**
   - Ensure error handling for deferred imports
   - Test all code paths thoroughly
   - Maintain import order dependencies

2. **Async Complexity**
   - Keep synchronous fallbacks
   - Handle race conditions
   - Proper error propagation

3. **Backward Compatibility**
   - Maintain existing CLI interface
   - Version configuration changes
   - Provide migration paths

## Conclusion

This plan provides a systematic approach to reducing TunaCode's startup time from 3-5 seconds to under 1 second. The phased approach allows for incremental improvements while maintaining stability and code quality.