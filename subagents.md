# TunaCode Subagents Architecture

## Overview

TunaCode implements a subagent system using a delegation pattern that allows the main agent to create specialized subagents for specific tasks. The primary implementation is the **Research Agent**, which is designed for read-only codebase exploration.

## Core Components

### 1. Research Agent (`research_agent.py`)

The research agent is a specialized subagent that:
- Uses read-only tools only (no file modification capabilities)
- Has a hard limit of 3 file reads maximum
- Uses the same model as the main agent
- Returns structured research findings

#### Key Features:
- **File Read Limiting**: Enforces a maximum of 3 file reads through a wrapper function
- **Progress Tracking**: Provides real-time feedback on tool execution
- **Error Handling**: Gracefully handles errors and returns structured error responses
- **Usage Aggregation**: Shares usage tracking with the parent agent

### 2. Delegation Tools (`delegation_tools.py`)

The delegation system is implemented through the `research_codebase` tool:
- Creates specialized research agents on-demand
- Passes the current model and state from the main agent
- Handles progress callbacks for UI integration
- Returns structured research findings with:
  - Relevant files discovered
  - Key findings
  - Code examples with explanations
  - Recommendations

### 3. Agent Configuration (`agent_config.py`)

The main agent is configured with the delegation tool:
- Research codebase tool is added to the main agent's tool list
- Uses the same retry and validation settings as other tools
- Integrates with the agent's HTTP client configuration

## Workflow

### 1. Tool Invocation
1. Main agent calls `research_codebase(query, directories, max_files)`
2. Delegation tool creates a specialized research agent
3. Research agent is configured with read-only tools and file limits

### 2. Research Execution
1. Research agent processes the query using read-only tools:
   - `read_file` (limited to 3 files)
   - `grep` (content search)
   - `list_dir` (directory exploration)
   - `glob` (file pattern matching)
2. Progress is tracked and reported back to the main agent
3. Results are structured into a standardized format

### 3. Result Integration
1. Research findings are returned to the main agent
2. Results are integrated into the main agent's response context
3. Main agent continues processing with the research findings

## Key Design Principles

### Safety
- **Read-Only**: Research agents cannot modify files
- **File Limits**: Hard cap of 3 file reads prevents resource exhaustion
- **Error Isolation**: Research agent errors don't crash the main agent

### Performance
- **Parallel Execution**: Tools are executed in parallel when possible
- **Progress Tracking**: Real-time feedback during long operations
- **Usage Aggregation**: Shared usage tracking with parent agent

### Usability
- **Structured Output**: Consistent format for research findings
- **Error Handling**: Graceful degradation with informative error messages
- **Progress Feedback**: Real-time updates on research progress

## Tool Categories

### Read-Only Tools (Available to Research Agents)
- `read_file`
- `grep`
- `list_dir`
- `glob`
- `web_fetch`

### Write/Execute Tools (NOT available to Research Agents)
- `write_file`
- `update_file`
- `bash`

## Configuration

### File Read Limit
The research agent enforces a hard limit of 3 file reads maximum, which is:
- Configurable via the `max_files` parameter (capped at 3)
- Implemented through a wrapper function that tracks calls
- Returns a warning message when the limit is reached

### Progress Tracking
- Optional progress callback for UI integration
- Tracks tool execution with operation descriptions
- Reports current progress without knowing total operations upfront

## Error Handling

The research agent system handles various error scenarios:
- **Tool Execution Errors**: Wrapped and returned as structured error responses
- **File Read Limits**: Returns informative warning when limit is reached
- **Network Issues**: Uses the same retry logic as the main agent
- **Validation Errors**: Returns structured error information

## Integration Points

### With Main Agent
- Shares the same model configuration
- Aggregates usage statistics
- Integrates results into the main conversation flow
- Handles progress callbacks through the state manager

### With UI
- Progress tracking for long-running research tasks
- Visual feedback during research execution
- Error display for failed research tasks