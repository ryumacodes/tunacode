# Research – Core Module Reorganization Map

**Date:** 2025-12-02
**Owner:** Claude Agent
**Phase:** Research
**Branch:** textual_repl
**Commit:** ee2945387f42098027c8e5d04d7401e1a69594d5

## Goal

Map the logical structure of `src/tunacode/core/` to identify reorganization opportunities based on cohesion, coupling, and Single Responsibility Principle.

## Current Structure

```
core/
├── __init__.py                    # Empty
├── state.py                       # StateManager, SessionState (193 lines)
├── tool_authorization.py          # AuthorizationPolicy, Rules (345 lines)
├── tool_handler.py                # ToolHandler facade (126 lines)
├── code_index.py                  # CodeIndex singleton (534 lines)
├── agents/
│   ├── __init__.py               # Public exports
│   ├── main.py                   # RequestOrchestrator + 4 managers (557 lines)
│   ├── prompts.py                # Intervention templates (67 lines)
│   ├── delegation_tools.py       # research_codebase factory (110 lines)
│   ├── research_agent.py         # create_research_agent (118 lines)
│   └── agent_components/         # 12 tightly-coupled modules
│       ├── __init__.py
│       ├── agent_config.py       # GOD OBJECT - 388 lines, 5 responsibilities
│       ├── agent_helpers.py      # TOO BROAD - 283 lines
│       ├── message_handler.py    # 101 lines
│       ├── node_processor.py     # 394 lines
│       ├── response_state.py     # 131 lines
│       ├── result_wrapper.py     # ~60 lines
│       ├── state_transition.py   # ~100 lines
│       ├── streaming.py          # ~400 lines
│       ├── task_completion.py    # 42 lines
│       ├── tool_buffer.py        # 45 lines
│       ├── tool_executor.py      # ~80 lines
│       └── truncation_checker.py # ~80 lines
└── logging/
    ├── __init__.py               # THOUGHT log level, setup_logging
    ├── config.py                 # LogConfig (71 lines)
    ├── formatters.py             # Simple/Detailed/JSON (49 lines)
    └── logger.py                 # get_logger (9 lines)
```

## Findings

### 1. Dependency Analysis (Import Frequency)

| Module | Import Count | Dependents |
|--------|--------------|------------|
| `state.StateManager` | **13** | cli/, agents/, tools/, core/ |
| `logging.get_logger` | 5 | agents/, utils/ |
| `tool_handler.ToolHandler` | 3 | cli/, core/state |
| `code_index.CodeIndex` | 3 | tools/glob, tools/list_dir |
| `tool_authorization` | 1 | tool_handler only |

**StateManager is the central coupling hub** - changes ripple across 13+ files.

### 2. Circular Dependencies Detected

```
StateManager (state.py) ←→ ToolHandler (tool_handler.py)
├── state.py:26 imports ToolHandler (TYPE_CHECKING only)
└── tool_handler.py:14 imports StateManager (runtime)

tool_authorization.py ←→ agent_helpers.py
├── tool_authorization.py:32 imports StateManager (TYPE_CHECKING)
└── tool_authorization.py:267 imports create_user_message (lazy, in function)
```

**Mitigation:** TYPE_CHECKING guards prevent runtime circular imports, but this is a design smell.

### 3. Identified Logical Domains

| Domain | Current Location | Responsibility | Cohesion |
|--------|------------------|----------------|----------|
| **State Management** | `state.py` | Session lifecycle, config | LOW (30 fields, 6 concerns) |
| **Tool Authorization** | `tool_authorization.py`, `tool_handler.py` | Rule-based auth, confirmation | HIGH |
| **Agent Orchestration** | `agents/main.py` | Request loop coordination | MEDIUM |
| **Response Pipeline** | `agents/agent_components/` | Node processing, streaming | HIGH (but hidden) |
| **Infrastructure** | `logging/`, `code_index.py` | Logging, file indexing | HIGH |

### 4. Critical Issues

#### 4.1 God Object: SessionState (`state.py:30-97`)

**30 fields spanning 6 unrelated concerns:**

| Concern | Fields |
|---------|--------|
| Session basics | user_config, session_id, device_id, messages |
| Agent state | agents, agent_versions, current_model |
| **UI state (LAYER VIOLATION)** | spinner, streaming_panel, show_thoughts, is_streaming_active |
| Tool authorization | tool_ignore, yolo |
| React tooling | react_scratchpad, react_forced_calls, react_guidance |
| Recursion tracking | current_recursion_depth, parent_task_id, task_hierarchy |
| Token tracking | total_tokens, max_tokens, last_call_usage, session_total_usage |
| Iteration state | current_iteration, iteration_count, files_in_context, tool_calls |

#### 4.2 God Object: agent_config.py (388 lines)

**5 separate responsibilities in one file:**
1. Agent factory (`get_or_create_agent`)
2. Model creation (`_create_model_with_retry`)
3. Prompt loading (`load_system_prompt`, `load_tunacode_context`)
4. HTTP retry config (lines 356-370)
5. Request delay handling (lines 61-129)

#### 4.3 Misleading Name: `agent_components/`

**Name suggests:** Reusable, loosely-coupled components
**Reality:** Tightly-coupled sequential processing pipeline

Evidence of pipeline nature:
- `node_processor.py` imports from `response_state`, `task_completion`, `tool_buffer`, `truncation_checker`
- All share `StateManager` reference
- Execution order is enforced

#### 4.4 Too Broad: agent_helpers.py (283 lines)

Mixed responsibilities:
- Message creation (lines 42-51)
- Tool metadata extraction (lines 54-131)
- Empty response templates (lines 134-165)
- Fallback response building (lines 180-246)

#### 4.5 Misplaced: code_index.py

- 534 lines of specialized file indexing
- Zero dependencies on core modules
- Only used by `tools/glob.py` and `tools/list_dir.py`
- Doesn't belong in core/

## Key Patterns Found

| Pattern | Description | Relevance |
|---------|-------------|-----------|
| **TYPE_CHECKING guards** | Used to break circular imports | Essential for current structure |
| **Singleton pattern** | StateManager, CodeIndex | Creates hidden coupling |
| **Facade pattern** | ToolHandler wraps authorization | Good separation |
| **Strategy pattern** | AuthorizationPolicy + Rules | Clean SRP compliance |
| **Pipeline pattern** | agent_components (hidden) | Should be made explicit |

## Proposed Reorganization

### Option A: Minimal Changes (Rename + Relocate)

```
core/
├── state.py                      # No change (defer god object fix)
├── tools/                        # NEW - group tool-related
│   ├── authorization.py          # from tool_authorization.py
│   └── handler.py                # from tool_handler.py
├── agents/
│   ├── main.py                   # No change
│   ├── prompts.py                # Move to prompts/ or keep
│   ├── delegation/               # NEW - group delegation
│   │   ├── tools.py              # from delegation_tools.py
│   │   └── research.py           # from research_agent.py
│   └── pipeline/                 # RENAME from agent_components
│       └── ... (all 12 files)
├── logging/                      # No change
└── indexing/                     # NEW - relocate code_index
    └── code_index.py
```

### Option B: Full Refactor (Decompose God Objects)

```
core/
├── state/                        # Decompose SessionState
│   ├── session.py                # Core: user_config, session_id, messages
│   ├── execution.py              # Recursion, iterations
│   ├── react.py                  # React scratchpad, guidance
│   ├── metrics.py                # Token/usage tracking
│   └── manager.py                # Facade coordinating sub-states
├── tools/
│   ├── authorization.py
│   └── handler.py
├── agents/
│   ├── orchestration/            # From agents/main.py
│   │   ├── orchestrator.py       # RequestOrchestrator
│   │   ├── iteration.py          # IterationManager
│   │   ├── empty_response.py     # EmptyResponseHandler
│   │   └── react_snapshot.py     # ReactSnapshotManager
│   ├── pipeline/                 # From agent_components
│   │   ├── node_processor.py
│   │   ├── state_machine.py      # response_state + state_transition
│   │   ├── completion.py         # task_completion + truncation_checker
│   │   ├── execution.py          # tool_buffer + tool_executor
│   │   ├── streaming.py
│   │   └── result.py             # result_wrapper
│   ├── factory/                  # From agent_config.py
│   │   ├── agent.py              # Agent creation
│   │   ├── model.py              # Model creation
│   │   └── retry.py              # HTTP retry config
│   ├── delegation/
│   │   ├── research.py
│   │   └── tools.py
│   └── helpers/                  # From agent_helpers.py
│       ├── messages.py           # Message creation
│       ├── metadata.py           # Tool summaries
│       └── templates.py          # Response templates
├── prompts/
│   ├── loader.py                 # Prompt loading (from agent_config)
│   └── intervention.py           # From agents/prompts.py
├── indexing/
│   └── code_index.py
└── logging/                      # No change
```

## Knowledge Gaps

1. **UI Integration:** How are `spinner` and `streaming_panel` used? Need to trace usage to safely extract from SessionState.

2. **React State Ownership:** Is `react_scratchpad` only used by ReactTool, or shared more broadly?

3. **Agent Caching:** `StateManager.session.agents` caches agent instances - need to understand lifecycle before splitting state.

4. **Test Coverage:** No tests found importing from `tunacode.core` - reorganization risks breaking untested code.

5. **Backward Compatibility:** How many external consumers depend on current import paths?

## Recommended Approach

**Phase 1 - Low Risk (Option A):**
1. Rename `agent_components/` → `pipeline/` (makes purpose explicit)
2. Move `code_index.py` → `indexing/code_index.py`
3. Group `tool_authorization.py` + `tool_handler.py` → `tools/`
4. Group `delegation_tools.py` + `research_agent.py` → `agents/delegation/`

**Phase 2 - Medium Risk:**
1. Split `agent_config.py` into focused modules
2. Split `agent_helpers.py` into focused modules
3. Extract prompts to dedicated location

**Phase 3 - Higher Risk (Option B):**
1. Decompose SessionState into focused state objects
2. Extract UI concerns to presentation layer
3. Split `agents/main.py` into orchestration modules

## References

| File | Lines | Purpose |
|------|-------|---------|
| `src/tunacode/core/state.py` | 1-193 | State management |
| `src/tunacode/core/tool_authorization.py` | 1-345 | Authorization rules |
| `src/tunacode/core/tool_handler.py` | 1-126 | Tool handling facade |
| `src/tunacode/core/code_index.py` | 1-534 | File indexing |
| `src/tunacode/core/agents/main.py` | 1-557 | Request orchestration |
| `src/tunacode/core/agents/prompts.py` | 1-67 | Intervention prompts |
| `src/tunacode/core/agents/agent_components/agent_config.py` | 1-388 | Agent factory (god object) |
| `src/tunacode/core/agents/agent_components/agent_helpers.py` | 1-283 | Helpers (too broad) |
| `src/tunacode/core/agents/agent_components/node_processor.py` | 1-394 | Node processing |
| `src/tunacode/core/logging/` | - | Logging infrastructure |
