# TunaCode Parallelization Analysis

## Overview

This document analyzes the feasibility and approaches for parallelizing agents and tools within TunaCode's architecture.

## Current Architecture Constraints

### Sequential Processing Model
- **Single Agent Active**: Only one agent processes requests at a time
- **Sequential Tool Execution**: Tools execute one after another via `async for node in agent_run`
- **Pydantic-AI Framework**: Built for sequential processing, not concurrent execution
- **Shared State**: Single `StateManager` instance manages all session state

### Code Evidence
```python
# core/agents/main.py:118-121
async with agent.iter(message, message_history=mh) as agent_run:
    async for node in agent_run:
        await _process_node(node, tool_callback, state_manager)
    return agent_run
```

## Parallelization Approaches

### 1. Tool-Level Parallelization ⭐ (RECOMMENDED)

**Difficulty**: Easy  
**Risk**: Low  
**Impact**: High

Parallelize operations **within** individual tools while maintaining the single-agent architecture.

#### Implementation Strategy
```python
async def _execute(self, query: str) -> str:
    # Run multiple search strategies concurrently within one tool
    tasks = [
        self._ripgrep_search(query),
        self._ast_search(query), 
        self._semantic_search(query),
        self._file_content_search(query)
    ]
    results = await asyncio.gather(*tasks)
    return self._merge_results(results)
```

#### Benefits
- ✅ No changes to agent flow required
- ✅ Fits existing architecture perfectly
- ✅ Immediate performance gains for I/O operations
- ✅ Maintains state consistency
- ✅ No UI coordination issues

#### Use Cases
- **File Operations**: Parallel file reading for search results
- **External APIs**: Concurrent API calls within tools
- **Search Strategies**: Multiple search algorithms simultaneously
- **Validation**: Parallel syntax/type checking

### 2. Background Processing ⚡ (PRACTICAL)

**Difficulty**: Medium  
**Risk**: Low  
**Impact**: Medium

Pre-compute expensive operations in background tasks.

#### Implementation Strategy
```python
class SearchTool(BaseTool):
    def __init__(self):
        self._index_task = None
        self._cached_index = None
        
    async def _execute(self, query: str):
        # Start background indexing if not running
        if not self._index_task and not self._cached_index:
            self._index_task = asyncio.create_task(self._build_code_index())
        
        # Use cached index or wait for completion
        if self._cached_index:
            index = self._cached_index
        else:
            index = await self._index_task
            self._cached_index = index
            
        return self._search(index, query)
```

#### Benefits
- ✅ Expensive operations happen once
- ✅ Subsequent searches are instant
- ✅ No architectural changes needed
- ✅ Graceful degradation if indexing fails

### 3. Agent-Level Parallelization ⚠️ (NOT RECOMMENDED)

**Difficulty**: Hard  
**Risk**: High  
**Impact**: Uncertain

Multiple agents processing different requests simultaneously.

#### Major Challenges

**State Conflicts**
```python
# Multiple agents modifying shared state simultaneously
state_manager.session.messages.append(...)  # Race condition!
state_manager.session.total_cost += cost     # Data corruption risk
```

**UI Coordination Issues**
- Multiple tool confirmation dialogs
- Concurrent spinner states
- Message output ordering

**Pydantic-AI Limitations**
- Framework designed for sequential processing
- No built-in coordination mechanisms
- Complex error handling across agents

**External Constraints**
- Model API rate limits
- Token budget management
- Conversation context confusion

#### Why It's Problematic
```python
# Hypothetical - would cause issues
async def parallel_agents():
    agent1_task = process_request("task 1", state_manager)
    agent2_task = process_request("task 2", state_manager)  # Same state!
    
    # Both modify state_manager.session.messages simultaneously
    results = await asyncio.gather(agent1_task, agent2_task)  # 💥
```

## Recommendations

### Immediate Implementation: Enhanced Search Tool

Create a powerful search tool that internally parallelizes operations:

```python
class CodeSearchTool(BaseTool):
    async def _execute(self, query: str, search_types: list = None) -> str:
        search_types = search_types or ["content", "files", "symbols", "imports"]
        
        # Parallel search strategies
        search_tasks = []
        if "content" in search_types:
            search_tasks.append(self._content_search(query))
        if "files" in search_types:
            search_tasks.append(self._file_search(query))
        if "symbols" in search_types:
            search_tasks.append(self._symbol_search(query))
        if "imports" in search_types:
            search_tasks.append(self._import_search(query))
            
        # Execute all searches concurrently
        results = await asyncio.gather(*search_tasks, return_exceptions=True)
        
        # Merge and rank results
        return self._format_search_results(results, query)
```

### Future Considerations

1. **Agent Pool**: Cache multiple agent instances per model
2. **Tool Chaining**: Sequential tools with parallel sub-operations
3. **Streaming Results**: Display results as they arrive
4. **Smart Caching**: Persistent caches across sessions

## Performance Benefits

### Tool Parallelization Gains
- **File I/O**: 3-5x faster for multi-file operations
- **Search Operations**: 2-4x faster with parallel strategies
- **External APIs**: Near-linear scaling with concurrent calls

### Background Processing Gains
- **First Search**: Standard speed (building index)
- **Subsequent Searches**: 10-100x faster (cached index)
- **Code Intelligence**: Real-time symbol/import resolution

## Implementation Priority

1. **Phase 1**: Enhanced search tool with parallel file operations
2. **Phase 2**: Background indexing for code intelligence
3. **Phase 3**: Advanced caching and streaming results

## Conclusion

**Tool-level parallelization is the sweet spot** - easy to implement, low risk, high impact. Agent-level parallelization introduces unnecessary complexity without clear benefits in TunaCode's use case.

Focus on making individual tools more powerful rather than running multiple agents concurrently.