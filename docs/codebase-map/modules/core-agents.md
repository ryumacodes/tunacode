---
title: Core Agent Orchestration
path: src/tunacode/core/agents
type: directory
depth: 1
description: AI agent creation, execution, and delegation system
exports: [process_request, RequestOrchestrator, AgentConfig, get_or_create_agent]
seams: [M, D]
---

# Core Agent Orchestration

## Purpose
Manages AI agent lifecycle using pydantic-ai framework, including agent creation, request processing, tool execution, and multi-agent delegation.

## Key Components

### Main Entry Point
**process_request()** in `main.py`
- Creates RequestOrchestrator with agent configuration
- Iterates through agent responses until completion
- Handles tool execution and result aggregation
- Manages iteration limits and productivity checks

### Agent Components

#### agent_config.py
- **get_or_create_agent()** - Factory for cached Agent instances
- **_create_model_with_retry()** - Model initialization with fallback
- **load_tunacode_context()** - Loads guide file into system prompt:
  - Standard mode: loads `AGENTS.md` (or `settings.guide_file`)
  - Local mode: loads `local_prompt.md` for minimal tokens

#### node_processor.py
- **_process_node()** - Core response processing loop
- Extracts tool calls from structured and text responses
- Handles empty/truncated response edge cases
- Detects task completion markers (TUNACODE DONE:)

#### tool_executor.py
- **execute_tools_parallel()** - Concurrent read-only tool execution
- Implements exponential backoff retry logic
- Batches tools for efficiency

#### tool_buffer.py
- **ToolBuffer** - Collects and batches read-only tool calls
- Separates read-only from write operations

### Delegation System

#### delegation_tools.py
- **create_research_codebase_tool()** - Creates research delegation tool
- Spawns specialized research_agent for codebase exploration
- Research agent uses read-only tools only

#### research_agent.py
- Specialized agent with focused system prompt
- Limited tool set (glob, grep, read_file, list_dir)
- Returns structured research summaries

### State Management

#### state_transition.py
- **AgentStateMachine** - Tracks processing states
- Valid transitions: USER_INPUT → ASSISTANT → TOOL_EXECUTION → RESPONSE
- Ensures proper state flow

#### iteration_manager.py (in main.py)
- **IterationManager** - Tracks agent productivity
- Forces action after unproductive_limit iterations
- Requests clarification at max_iterations

### ReAct Pattern Support

#### ReactSnapshotManager
- Captures agent thought process snapshots
- Injects structured guidance into context
- Nudges agent toward next logical step

## Configuration

**AgentConfig** dataclass:
- **max_iterations** (default: 15) - Maximum agent loops
- **unproductive_limit** (default: 3) - Unproductive loops before intervention

## Tool Categories

**Standard Mode (11 tools):**
1. **Read-Only Tools** - glob, grep, read_file, list_dir, web_fetch
2. **Write/Execute Tools** - bash, write_file, update_file
3. **Todo Tools** - todowrite, todoread, todoclear
4. **Delegation Tools** - research_codebase

**Local Mode (6 tools):**
Minimal tool set for small context windows (8k-16k tokens):
- bash, read_file, update_file, write_file, glob, list_dir
- Uses 1-word descriptions to save tokens (e.g., "Shell", "Read", "Edit")
- Excludes: grep, web_fetch, todo tools, research_codebase

## Integration Points

- **core/state.py** - Session state access
- **core/limits.py** - `is_local_mode()` for tool set selection
- **core/prompting/** - System prompt composition
- **tools/** - Tool function registry
- **types/** - AgentRun, ModelName types

## Seams (M, D)

**Modification Points:**
- Add new agent types (e.g., code_review_agent)
- Customize iteration limits and productivity thresholds
- Extend tool categorization logic
- Add new delegation patterns

**Extension Points:**
- Implement custom agent factories
- Add specialized tool executors
- Create new state machine transitions
