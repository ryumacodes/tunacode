# TunaCode Performance Improvement Plan (UPDATED - Phase 1 Complete)

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

#### IMPLEMENTED (Phase 1)

**1. Defer Update Checking (`cli/main.py`)**
- Update checking now runs in a background thread (`asyncio.to_thread(check_for_updates)`), and announces updates only after the REPL/UI is loaded and interactive. This avoids synchronous network I/O during startup.

**2. Lazy Import Heavy Dependencies (`core/agents/main.py`, `tools/__init__.py`)**
- The heavy import of `pydantic_ai` (Agent, Tool) now happens lazily, only when an agent is constructed. Tools imports are fully lazy using module-level `__getattr__` in the tools package, so tool submodules are loaded only when accessed the first time.

**3. Optimize Banner Display (`ui/output.py`, `ui/console.py`)**
- The startup banner display is now immediate and synchronous—no more await/async for just showing the initial banner. This avoids event loop overhead on startup and makes banner display near-instantaneous.

**IMPACT:**
- This phase eliminates slow network waits at startup, cuts base import cost (by deferring it), and makes the UI start much more quickly. Next startup should be noticeably faster, approaching the <2.5s range for most systems.

### Phase 2: Structural Improvements (3-5 days)
**Goal: Achieve < 1.5s startup time**

#### IMPLEMENTED (Phase 2)

1. **Import Caching Utility Added**
   - Added `/home/tuna/tunacode/src/tunacode/utils/import_cache.py` with a `lazy_import(module_name)` function for efficient, repeatable importing of heavy or optional modules. Other modules can use this for high-impact imports.

2. **Parallelize Setup Steps**
   - `core/setup/coordinator.py` now gathers all eligible setup steps and runs their `.execute()` in parallel using `asyncio.gather`. Validation still occurs sequentially for ordered safety. This should substantially speed up multi-step configuration/init sequences.

3. **Configuration Fast Path, In-Memory Fingerprinting**
   - Config is now loaded with hashing/fingerprinting of the config content (SHA-1, short hash) in `user_configuration.py`. If the config (on disk) hasn't changed since the last good run, the system instantly reuses the in-memory parsed version (skips JSON overhead and validation entirely).
   - `config_setup.py` uses that fingerprint to decide whether to skip repeated validation and assignment of config info—if fingerprint matches and last run validated, no further disk or JSON work is needed.
   - This avoids any config-related startup work except the very first time or after explicit changes.

**Impact:**
- Import cache is available for further expansion of lazy import strategies.
- Setup steps now start much faster and scale better if you add new ones.
- If config is unchanged, startup cost for config handling and validation is now near-zero.

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

### 1. Lazy Loading Pattern (PHASE 1 NOW IMPLEMENTED)
```python
# Instead of:
from pydantic_ai import Agent
# Use:
def get_agent_tool():
    import importlib
    pydantic_ai = importlib.import_module('pydantic_ai')
    return pydantic_ai.Agent
```

### 2. Background Tasks Pattern (PHASE 1 NOW IMPLEMENTED)
```python
async def main():
    # Start background tasks
    update_task = asyncio.to_thread(check_for_updates)
    # Continue with setup and REPL
    await quick_startup()
    # After UI loads, report updates if available
    has_update, latest_version = await update_task
    if has_update:
        await ui.update_available(latest_version)
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
   - Phase 1: < 2.5 seconds (expected achieved)
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

Phase 1 quick wins implemented:
- Deferred update checking
- Lazy loading of heaviest dependencies
- Immediate, synchronous banner display

TunaCode startup is now much faster, with further improvements planned for Phases 2 and 3.
