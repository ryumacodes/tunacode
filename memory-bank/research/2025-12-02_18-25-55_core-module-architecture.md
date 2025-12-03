# Research – TunaCode Core Module Architecture

**Date:** 2025-12-02
**Owner:** Claude Agent
**Phase:** Research
**Branch:** textual_repl

---

## Goal

Map out the complete `src/tunacode/core/` directory structure, understand component responsibilities, and document integration points to support the ongoing rewrite effort.

---

## Directory Structure

```
src/tunacode/core/
├── __init__.py              # Empty module marker
├── state.py                 # Session state management (singleton)
├── code_index.py            # Fast in-memory file indexing
├── tool_handler.py          # Tool confirmation facade
├── tool_authorization.py    # Declarative authorization rules
├── logging/
│   ├── __init__.py          # THOUGHT level + setup_logging()
│   ├── logger.py            # get_logger() wrapper
│   ├── formatters.py        # Simple/Detailed/JSON formatters
│   └── config.py            # LogConfig.load() + DEFAULT_LOGGING_CONFIG
└── agents/
    ├── __init__.py          # Re-exports all agent components
    ├── main.py              # RequestOrchestrator + iteration loop
    ├── research_agent.py    # Factory for read-only sub-agents
    ├── delegation_tools.py  # create_research_codebase_tool()
    ├── prompts.py           # Intervention message templates
    └── agent_components/
        ├── __init__.py          # Component exports
        ├── agent_config.py      # get_or_create_agent() + caching
        ├── agent_helpers.py     # Message creation + tool summaries
        ├── tool_executor.py     # Parallel tool execution
        ├── node_processor.py    # Core node processing logic
        ├── streaming.py         # Token streaming with instrumentation
        ├── tool_buffer.py       # Read-only tool batching
        ├── response_state.py    # Thread-safe state wrapper
        ├── state_transition.py  # State machine + transition rules
        ├── message_handler.py   # Orphaned tool patching
        ├── task_completion.py   # DONE marker detection
        ├── result_wrapper.py    # AgentRun wrappers
        └── truncation_checker.py # Response truncation heuristics
```

---

## Findings

### 1. State Management (`state.py`)

| Component | Location | Purpose |
|-----------|----------|---------|
| `SessionState` | `state.py:29-97` | Dataclass with 30+ fields for config, messages, tokens, ReAct, recursion |
| `StateManager` | `state.py:99-193` | Singleton wrapper with config loading and context management |

**Key Fields in SessionState:**
- `user_config` → Merged user + default configuration
- `messages` → Conversation history (MessageHistory)
- `tool_calls` → Tool call history list
- `react_scratchpad` → Timeline for ReAct reasoning
- `total_tokens/max_tokens` → Context window tracking
- `last_call_usage/session_total_usage` → Token + cost tracking
- `current_recursion_depth` → Multi-agent recursion tracking

**Entry Point:** Instantiated at `cli/main.py:21`

---

### 2. Agent Architecture (`agents/`)

#### Core Loop (`main.py`)

| Class | Lines | Responsibility |
|-------|-------|----------------|
| `AgentConfig` | 45-53 | Configuration dataclass (max_iterations, limits) |
| `RequestContext` | 56-62 | Per-request immutable context with UUID |
| `EmptyResponseHandler` | 65-96 | Tracks consecutive empty responses, triggers intervention |
| `IterationManager` | 98-167 | Productivity tracking, iteration limits, forced actions |
| `ReactSnapshotManager` | 169-266 | Periodic ReAct snapshots injected into messages |
| `RequestOrchestrator` | 268-467 | **Main loop**: iter nodes → process → track → stream |

**Main Entry:** `process_request()` at line 541

**Flow:**
```
process_request()
  → RequestOrchestrator.run()
    → _run_impl()
      → agent.iter() nodes
        → ac._process_node() for each
        → track empty/productivity
        → capture react snapshots
        → handle limits
      → return AgentRunWithState
```

#### Agent Components (`agent_components/`)

| Component | Key Function | Lines |
|-----------|-------------|-------|
| `agent_config.py` | `get_or_create_agent()` | 288-387 |
| `node_processor.py` | `_process_node()` | 48-230 |
| `node_processor.py` | `_process_tool_calls()` | 233-393 |
| `tool_executor.py` | `execute_tools_parallel()` | 14-59 |
| `streaming.py` | `stream_model_request_node()` | 20-291 |
| `response_state.py` | `ResponseState` class | all |
| `state_transition.py` | `AgentStateMachine` | 40-116 |

**State Machine Transitions:**
```
USER_INPUT → ASSISTANT → TOOL_EXECUTION → RESPONSE → ASSISTANT (loop)
```

**Smart Tool Batching Strategy:**
1. Research agent tools → separate execution
2. Read-only tools → ONE parallel batch
3. Write/execute tools → sequential execution

---

### 3. Tool Handling System

#### Authorization (`tool_authorization.py`)

| Component | Lines | Priority | Purpose |
|-----------|-------|----------|---------|
| `AuthContext` | 41-77 | - | Immutable context (yolo, ignore list, template) |
| `ReadOnlyToolRule` | 122-135 | 200 | Always allow read-only tools |
| `TemplateAllowedToolsRule` | 138-158 | 210 | Template pre-approved tools |
| `YoloModeRule` | 161-174 | 300 | Bypass all confirmations |
| `ToolIgnoreListRule` | 177-190 | 310 | User-configured ignore list |
| `AuthorizationPolicy` | 198-244 | - | Strategy pattern orchestrator |

**Design Patterns:**
- Protocol-based rules (Strategy pattern)
- Priority-based evaluation (lower = higher priority)
- Dependency injection for testability

#### Handler (`tool_handler.py`)

| Method | Lines | Purpose |
|--------|-------|---------|
| `should_confirm()` | 81-91 | Entry point for authorization check |
| `process_confirmation()` | 93-111 | Handle user response, update ignore list |
| `create_confirmation_request()` | 113-125 | Create UI confirmation request |

---

### 4. Code Indexing (`code_index.py`)

| Feature | Lines | Purpose |
|---------|-------|---------|
| Singleton pattern | 136-155 | Thread-safe `get_instance(root_dir)` |
| Basename index | 313-314 | Fast filename → paths lookup |
| Symbol extraction | 342-351 | Class/function definitions (regex-free) |
| Directory cache | 157-204 | 5-second TTL for directory contents |
| Ignore patterns | 26-61 | 30+ patterns (.git, node_modules, etc.) |

**Consumers:**
- `tools/glob.py:79` → Pattern matching
- `tools/list_dir.py:58` → Directory listing

---

### 5. Logging (`logging/`)

| Component | Purpose |
|-----------|---------|
| `LogConfig.load()` | User config → dictConfig |
| `THOUGHT` level (25) | Custom level for agent reasoning |
| `formatters.py` | Simple/Detailed/JSON formatters |

**Default:** Logging disabled (NullHandler), opt-in via config.

---

## Key Patterns / Solutions Found

| Pattern | Location | Description |
|---------|----------|-------------|
| **Singleton Manager** | `state.py:99`, `code_index.py:136` | Thread-safe instance management |
| **State Machine** | `state_transition.py:40-116` | Enum-based with transition validation |
| **Strategy Pattern** | `tool_authorization.py:198` | Composable authorization rules |
| **Facade Pattern** | `tool_handler.py:31` | Coordinates auth + notification + factory |
| **Factory Pattern** | `research_agent.py:77`, `delegation_tools.py:17` | Agent/tool creation with closures |
| **Smart Batching** | `node_processor.py:244-363` | Parallel read-only, sequential write |
| **Module Caching** | `agent_config.py:37-38` | Version-based agent cache invalidation |
| **Dependency Injection** | `tool_handler.py:42-71` | Policy, notifier, factory injection |

---

## Integration Points

```
┌─────────────────────────────────────────────────────────────┐
│                         CLI Layer                           │
│  cli/main.py:21 → StateManager (singleton)                 │
│  cli/textual_repl.py → session state access                │
└────────────────────────────┬────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────┐
│                      Core Layer                             │
│  ┌──────────────┐  ┌──────────────┐                        │
│  │ StateManager │◄─┤ ToolHandler  │                        │
│  │   state.py   │  │tool_handler  │                        │
│  └──────┬───────┘  └──────┬───────┘                        │
│         │                 │                                 │
│         ▼                 ▼                                 │
│  ┌────────────────────────────────────────────────────┐    │
│  │              Agent Orchestration                    │    │
│  │  main.py → RequestOrchestrator                      │    │
│  │    ├── EmptyResponseHandler                         │    │
│  │    ├── IterationManager                             │    │
│  │    └── ReactSnapshotManager                         │    │
│  └────────────────────────┬───────────────────────────┘    │
│                           │                                 │
│  ┌────────────────────────▼───────────────────────────┐    │
│  │              Agent Components                       │    │
│  │  agent_config.py → get_or_create_agent()           │    │
│  │  node_processor.py → _process_node()               │    │
│  │  tool_executor.py → execute_tools_parallel()       │    │
│  │  response_state.py + state_transition.py           │    │
│  └────────────────────────┬───────────────────────────┘    │
│                           │                                 │
│  ┌────────────────────────▼───────────────────────────┐    │
│  │           Multi-Agent Delegation                    │    │
│  │  delegation_tools.py → research_codebase tool       │    │
│  │  research_agent.py → read-only sub-agents           │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────┐
│                       Tools Layer                           │
│  tools/*.py → bash, read_file, write_file, grep, glob, etc │
│  tools/decorators.py → @base_tool, @file_tool              │
└─────────────────────────────────────────────────────────────┘
```

---

## Knowledge Gaps

1. **Template System** - `tool_authorization.py` references `Template` but template loader not analyzed
2. **Prompt Loading** - `prompts/system.xml` and `prompts/research/system.xml` content not examined
3. **Model Registry** - Pricing structure and model definitions not analyzed
4. **Message History** - `MessageHistory` type and message protocol not documented
5. **React Tool** - The actual ReAct tool implementation not in scope

---

## Rewrite Considerations

### High Coupling Areas
- `StateManager` is accessed everywhere → consider interface segregation
- `agent_components` imports are scattered → consolidate public API

### Complexity Hotspots
- `_process_node()` at 180+ lines → candidate for further decomposition
- `_process_tool_calls()` at 160+ lines → complex batching logic
- `streaming.py` at 270+ lines → debug instrumentation interspersed

### Testing Implications
- State machine has clear transition rules → easily unit testable
- Authorization rules use Protocol → mockable
- Singletons need `reset_instance()` for tests

---

## Cleanup (2025-12-02)

The following unused modules were removed:

| File Removed | Reason |
|--------------|--------|
| `token_tracker.py` | Zero references; `TokenUsage` in `types.py` is the active version |
| `agents/utils.py` | Never imported; duplicates agent_components helpers |
| `agent_components/json_tool_parser.py` | Re-exported but never called |
| `logging/handlers.py` | `RichHandler`/`StructuredFileHandler` never wired into config |

Additional pruning:
- `is_tool_blocked()` method removed from `tool_authorization.py` (always returned False)
- Stub `RichHandler` class removed from `logging/__init__.py`

---

## References

- `src/tunacode/core/state.py` → Central state management
- `src/tunacode/core/agents/main.py` → Request orchestration
- `src/tunacode/core/agents/agent_components/node_processor.py` → Node processing
- `src/tunacode/core/tool_authorization.py` → Authorization rules
- `src/tunacode/core/code_index.py` → File indexing
- `src/tunacode/constants.py:61-68` → READ_ONLY_TOOLS definition
