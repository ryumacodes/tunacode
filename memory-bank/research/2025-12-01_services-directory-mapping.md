# Research - Services Directory Architecture Mapping

**Date:** 2025-12-01
**Owner:** claude-agent
**Phase:** Research

## Goal

Comprehensively map the `src/tunacode/services/` directory structure, documenting all components, dependencies, usage patterns, and integration points within the TunaCode codebase.

## Directory Structure

```
src/tunacode/services/
├── __init__.py      # Package marker (single comment line)
└── mcp.py           # MCP (Model Context Protocol) server management
```

The services directory is intentionally minimal, containing only MCP-related functionality.

---

## Findings

### Core Module: `mcp.py`

**Location:** `/root/tunacode/src/tunacode/services/mcp.py` (205 lines)

#### Exports

| Function/Class | Line | Purpose |
|----------------|------|---------|
| `QuietMCPServer` | 33 | Subclass of MCPServerStdio that suppresses stderr output |
| `cleanup_mcp_servers()` | 67 | Async function to clean up MCP server connections |
| `register_mcp_agent()` | 130 | Registers an agent for MCP cleanup tracking |
| `get_mcp_servers()` | 141 | Main entry point - loads MCP servers from config with caching |

#### Module-Level State

```python
# Line 26-28
_MCP_SERVER_CACHE: Dict[str, MCPServerStdio] = {}
_MCP_CONFIG_HASH: Optional[int] = None
_MCP_SERVER_AGENTS: Dict[str, "Agent"] = {}
```

---

### Dependencies

#### 1. MCPError Exception

**File:** `src/tunacode/exceptions.py:122-131`

```python
class MCPError(ServiceError):
    def __init__(self, server_name: str, message: ErrorMessage, original_error: OriginalError = None):
        self.server_name = server_name
        self.original_error = original_error
        super().__init__(f"MCP server '{server_name}' error: {message}")
```

**Inheritance:** `MCPError` -> `ServiceError` -> `TunaCodeError` -> `Exception`

#### 2. MCPServers Type

**File:** `src/tunacode/types.py:219-220`

```python
MCPServerConfig = Dict[str, Any]
MCPServers = Dict[str, MCPServerConfig]
```

**Structure:** `Dict[server_name, Dict[config_key, config_value]]`

#### 3. StateManager

**File:** `src/tunacode/core/state.py:100-194`

- Provides access to `session.user_config["mcpServers"]`
- Config loaded from `~/.config/tunacode/config.json`
- Merged with defaults from `configuration/defaults.py:38`

#### 4. pydantic_ai.mcp.MCPServerStdio

**External dependency** - handles MCP protocol over stdio:
- Subprocess management for MCP servers
- JSON-RPC protocol communication
- Context manager for lifecycle management

---

### Import Chain (Re-export Pattern)

```
services/mcp.py (implementation)
        │
        ▼
core/agents/main.py:24-28 (re-exports with comment "re-exported by design")
        │
        ▼
core/agents/__init__.py:19-26 (public API)
        │
        ▼
cli/main.py:119 (consumer - imports cleanup_mcp_servers)
```

**Direct Import (bypasses re-export):**
- `core/agents/agent_components/agent_config.py:21` imports directly from `services.mcp`

---

### Usage Patterns

#### 1. MCP Server Retrieval

**Location:** `agent_config.py:363`

```python
mcp_servers = get_mcp_servers(state_manager)
```

#### 2. Agent Construction with MCP

**Location:** `agent_config.py:384-389`

```python
agent = Agent(
    model=model_instance,
    system_prompt=system_prompt,
    tools=tools_list,
    mcp_servers=mcp_servers,  # Line 388
)
```

#### 3. Agent Registration for Cleanup

**Location:** `agent_config.py:392-394`

```python
mcp_server_names = state_manager.session.user_config.get("mcpServers", {}).keys()
for server_name in mcp_server_names:
    register_mcp_agent(server_name, agent)
```

#### 4. CLI Exit Cleanup

**Location:** `cli/main.py:119-121`

```python
from tunacode.core.agents import cleanup_mcp_servers
await cleanup_mcp_servers()  # Best-effort cleanup
```

---

### Caching Strategy

#### Two-Level Cache with Version Tracking

**MCP Server Cache:**
- Hash-based invalidation: `hash(str(mcp_servers))` at `mcp.py:158`
- Automatic cleanup of removed servers at `mcp.py:166-179`
- Non-blocking cleanup via `asyncio.create_task()` at `mcp.py:176`

**Agent Cache:**
- Version includes MCP config at `agent_config.py:116`
- Cache invalidated when MCP config changes

---

### Lifecycle Management

```
Config Load (StateManager.__init__)
    ↓
get_mcp_servers(state_manager) - Creates MCPServerStdio instances
    ↓
Agent(..., mcp_servers=mcp_servers) - Passes to pydantic-ai
    ↓
register_mcp_agent() - Tracks for cleanup
    ↓
agent.iter() context - pydantic-ai starts MCP subprocesses
    ↓
Context exit - pydantic-ai stops MCP servers
    ↓
cleanup_mcp_servers() - Final cleanup at CLI exit
```

---

## Key Patterns / Solutions Found

### 1. Delegation Pattern
MCP subprocess lifecycle delegated to pydantic-ai's context manager. TunaCode only manages configuration and caching.

### 2. Config-as-Kwargs Pattern
Server config dict unpacked directly: `MCPServerStdio(**conf)` at `mcp.py:192`

### 3. Fail-Fast Error Handling
Wraps low-level exceptions in `MCPError` with server context at `mcp.py:197-202`

### 4. Layered Re-export
Implementation in services -> re-exported through agents -> consumed by CLI

### 5. QuietMCPServer (Unused)
Class defined at `mcp.py:33-64` to suppress stderr, but NOT actually used. Line 192 creates `MCPServerStdio` directly. Setting `MCPServerStdio.log_level = "critical"` at line 185 may be sufficient.

---

## Knowledge Gaps

1. **No Tests:** No test files found for the services module or MCP functionality
2. **QuietMCPServer Unused:** Defined but not instantiated - potential dead code or future feature
3. **Research Agent Isolation:** Research agents at `research_agent.py:112-117` don't receive MCP servers - by design or oversight?

---

## Architectural Notes

### Why Services Module is Minimal

The services directory follows separation of concerns:
- **services/**: External service integrations (MCP protocol)
- **core/**: Internal business logic (agents, state, session)
- **cli/**: User interface layer

MCP is currently the only external service, hence the minimal structure.

### Integration Points Summary

| Component | File | Line | Purpose |
|-----------|------|------|---------|
| Config Load | `state.py` | 126 | Loads `mcpServers` into `session.user_config` |
| Server Creation | `mcp.py` | 192 | Creates `MCPServerStdio` instances |
| Agent Integration | `agent_config.py` | 388 | Passes MCP servers to Agent constructor |
| Registration | `agent_config.py` | 394 | Registers agent for cleanup tracking |
| Cleanup | `cli/main.py` | 121 | Final cleanup on exit |

---

## References

### Source Files
- `src/tunacode/services/mcp.py` - Core MCP implementation
- `src/tunacode/services/__init__.py` - Package marker
- `src/tunacode/core/agents/agent_components/agent_config.py` - Agent creation with MCP
- `src/tunacode/core/agents/main.py` - Re-exports MCP functions
- `src/tunacode/core/state.py` - Configuration loading
- `src/tunacode/exceptions.py` - MCPError definition
- `src/tunacode/types.py` - MCPServers type definition
- `src/tunacode/cli/main.py` - CLI cleanup integration

### Related Research
- `memory-bank/research/2025-11-16_main-agent-architecture-map.md` - Documents re-export pattern
- `memory-bank/research/2025-09-26_10-56-29_main_agent_architecture.md` - MCP usage context

### External Dependencies
- `pydantic-ai` package: `pydantic_ai.mcp.MCPServerStdio`
- `mcp` package: `mcp.client.stdio` for stdio communication
