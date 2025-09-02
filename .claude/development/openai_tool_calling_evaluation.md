# OpenAI Tool Calling Evaluation

## Current Architecture Analysis
**Date**: 2025-01-02
**Branches Compared**: secure-tool-testing vs master

## Key Findings

### 1. Framework Used
- **NOT using OpenAI SDK** - The codebase uses `pydantic-ai` for all agent orchestration
- No imports of `openai` or `OpenAI` found in the agents module
- Tool calling is handled through pydantic-ai's native system

### 2. Core Components

#### Agent System (`src/tunacode/core/agents/`)
- **main.py**: Primary orchestration with `process_request()` as entry point
- Uses `pydantic_ai.Agent` for agent creation
- Tools registered via `pydantic_ai.Tool` wrapper

#### Tool Registration (`agent_config.py:244-266`)
```python
tools_list = [
    Tool(bash, max_retries=max_retries),
    Tool(glob, max_retries=max_retries),
    Tool(grep, max_retries=max_retries),
    # ... etc
]
```

### 3. Tool Execution Flow
1. Agent receives request → `process_request()`
2. Iterates through `agent.iter()` responses
3. Processes nodes via `_process_node()`
4. Buffers read-only tools for parallel execution
5. Executes tools through callbacks

### 4. Special Features
- **Parallel Execution**: Read-only tools buffered and executed concurrently
- **Fallback JSON Parsing**: `json_tool_parser.py` for providers without native tool support
- **MCP Integration**: Supports Model Context Protocol servers
- **Plan Mode**: Restricted tool set for planning tasks

### 5. Tool Schema Support
- Base tool class has `get_tool_schema()` method (base.py:229-251)
- Returns OpenAI-compatible function format:
  ```python
  {
      "name": tool_name,
      "description": description,
      "parameters": parameters_schema
  }
  ```
- But this is for compatibility, not actual OpenAI SDK usage

## Master Branch Analysis

### Tool Unification Plan Discovery
Found commit `a3c8342` with "Tool Unification Plan" that aims to:
1. **Create OpenAI-compatible schemas** with stringified arguments
2. **Unify three-layer system**: System prompt + XML schemas + Python implementation
3. **Tool Registry**: New `@tool_definition` decorator system planned
4. **Schema Compatibility**: `schema_assembler.py` already provides OpenAI function format

### Key Differences: Master vs Secure-Tool-Testing
1. **Master Branch**:
   - Has `tool_unification_plan.md` outlining OpenAI compatibility goals
   - `schema_assembler.py` generates OpenAI-compatible function schemas
   - Planning decorator-based unified tool system
   - Still uses pydantic-ai but preparing for OpenAI format

2. **Secure-Tool-Testing Branch**:
   - Pure pydantic-ai implementation
   - No explicit OpenAI compatibility layer
   - Loads prompts from `system.xml` (modified in branch)

## Conclusion
Both branches use **pydantic-ai** as the execution framework. The master branch is planning a unified tool system with OpenAI-compatible schema generation, but actual OpenAI SDK integration is NOT implemented. The system maintains compatibility at the schema level only, not at the execution level.

## Files Examined
- `/src/tunacode/core/agents/main.py`
- `/src/tunacode/core/agents/agent_components/agent_config.py`
- `/src/tunacode/core/agents/agent_components/json_tool_parser.py`
- `/src/tunacode/tools/base.py`
- `/src/tunacode/types.py`
