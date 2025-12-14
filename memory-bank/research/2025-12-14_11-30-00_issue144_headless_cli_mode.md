# Research – Issue #144: Headless CLI Mode for Benchmark Execution

**Date:** 2025-12-14
**Owner:** agent
**Phase:** Research
**Issue:** https://github.com/alchemiststudiosDOTai/tunacode/issues/144

## Goal

Map out the architecture and implementation requirements for adding a non-interactive CLI command (`tunacode run`) to run TunaCode in headless mode for benchmarks and automation (Harbor tbench integration).

## Issue Summary

| Field | Value |
|-------|-------|
| Title | feat: Add headless CLI mode for benchmark execution |
| State | OPEN |
| Series | Issue 1 of 5 (Harbor tbench Integration) |

### Required CLI Interface

```bash
tunacode run "<prompt>" [OPTIONS]
```

**Options:**
- `--model` / `-m` - Model to use (default: from config)
- `--auto-approve` - Skip tool authorization prompts (required for benchmarks)
- `--output-json` - Output trajectory as JSON for Harbor consumption
- `--timeout` - Execution timeout in seconds
- `--cwd` - Working directory for execution

### Acceptance Criteria

- [ ] `tunacode run "hello world"` executes without TUI
- [ ] `--auto-approve` skips all tool confirmations
- [ ] `--output-json` outputs valid JSON trajectory
- [ ] Exit code reflects success/failure
- [ ] Stdout/stderr used for output (no curses/textual)

## Findings

### 1. CLI Entry Point Architecture

**Key File:** [`src/tunacode/ui/main.py`](https://github.com/alchemiststudiosDOTai/tunacode/blob/4033081dc3cd9385a6347513bd4ed7421c9f42ae/src/tunacode/ui/main.py)

| Location | Purpose |
|----------|---------|
| `main.py:15` | Typer app instance creation |
| `main.py:31-85` | Current `main()` command (TUI mode) |
| `main.py:46` | `async_main()` wrapper |
| `main.py:63` | TUI launch via `run_textual_repl()` |
| `pyproject.toml:44` | Entry point: `tunacode = "tunacode.ui.main:app"` |

**Current Flow:**
```
CLI Entry → main() → async_main() → run_textual_repl() → TextualReplApp
```

**What changes:** Add new `@app.command("run")` that bypasses `run_textual_repl()` entirely.

### 2. Core Agent Execution (Headless-Ready)

**Key File:** [`src/tunacode/core/agents/main.py`](https://github.com/alchemiststudiosDOTai/tunacode/blob/4033081dc3cd9385a6347513bd4ed7421c9f42ae/src/tunacode/core/agents/main.py)

| Location | Purpose |
|----------|---------|
| `main.py:526-544` | `process_request()` - Main API entry |
| `main.py:270-307` | `RequestOrchestrator` initialization |
| `main.py:357-453` | Core iteration loop |

**Critical Discovery:** `process_request()` already supports headless execution!

```python
async def process_request(
    message: str,
    model: ModelName,
    state_manager: StateManager,
    tool_callback: ToolCallback | None = None,        # Optional!
    streaming_callback: Callable[...] | None = None,  # Optional!
    tool_result_callback: Callable[...] | None = None, # Optional!
    tool_start_callback: Callable[[str], None] | None = None,
) -> AgentRun
```

All callbacks are already optional - headless mode just needs to:
1. Pass `None` for callbacks (or simple logging callbacks)
2. Set `session.yolo = True` for auto-approve
3. Collect results from `state_manager.session.messages`

### 3. Tool Authorization System

**Key Directory:** [`src/tunacode/tools/authorization/`](https://github.com/alchemiststudiosDOTai/tunacode/tree/4033081dc3cd9385a6347513bd4ed7421c9f42ae/src/tunacode/tools/authorization)

| File | Purpose |
|------|---------|
| `handler.py:42-44` | `should_confirm()` - Main authorization check |
| `policy.py:9-19` | Rule evaluation engine |
| `rules.py:47-54` | `YoloModeRule` - Bypasses ALL confirmations |
| `context.py:13-32` | `AuthContext` - Immutable state snapshot |
| `factory.py:13-20` | Default policy with rule priorities |

**Authorization Rule Priority:**
1. `ReadOnlyToolRule` (200) - Always allows read-only tools
2. `TemplateAllowedToolsRule` (210) - Template-specific allowances
3. `YoloModeRule` (300) - **Bypasses ALL confirmations when `session.yolo=True`**
4. `ToolIgnoreListRule` (310) - Per-tool ignore list

**For `--auto-approve`:** Simply set `state_manager.session.yolo = True`

**State Location:** [`src/tunacode/core/state.py:47`](https://github.com/alchemiststudiosDOTai/tunacode/blob/4033081dc3cd9385a6347513bd4ed7421c9f42ae/src/tunacode/core/state.py#L47)
```python
yolo: bool = False  # Set to True for auto-approve
```

### 4. TUI Callbacks That Need Headless Alternatives

| Callback | TUI Implementation | Headless Alternative |
|----------|-------------------|---------------------|
| `tool_callback` | `app.py:548-565` - Confirmation prompts | `None` (with yolo=True) or auto-approve callback |
| `streaming_callback` | `app.py:397-413` - Widget updates | `None` or `print()` to stdout |
| `tool_result_callback` | `app.py:580-608` - Status bar updates | `None` or simple logger |
| `tool_start_callback` | `node_processor.py:287,299,309` | `None` or simple logger |

## Key Patterns / Solutions Found

### Pattern 1: Existing Yolo Mode
The `/yolo` command (`commands/__init__.py:59-66`) already implements auto-approve:
```python
app.state_manager.session.yolo = not app.state_manager.session.yolo
```

### Pattern 2: Callback Injection
All UI dependencies are injected via optional callbacks - no hardcoded TUI references in core agent.

### Pattern 3: State Manager Isolation
Each execution should create a fresh `StateManager()` instance to avoid state pollution.

### Pattern 4: Result Collection
Final output accessible via:
- `state_manager.session.messages` - Full conversation history
- `state_manager.session.tool_calls` - Tool execution log
- `state_manager.session.session_total_usage` - Token/cost tracking

## Implementation Map

### Files to Modify

| File | Change |
|------|--------|
| `src/tunacode/ui/main.py` | Add `@app.command("run")` function |
| `src/tunacode/core/state.py` | (Optional) Add `auto_approve` flag if separate from yolo |

### Proposed Implementation

```python
# src/tunacode/ui/main.py

@app.command(name="run")
def run_headless(
    prompt: str = typer.Argument(..., help="The prompt/instruction to execute"),
    model: str = typer.Option(None, "--model", "-m", help="Model to use"),
    auto_approve: bool = typer.Option(False, "--auto-approve", help="Skip tool confirmations"),
    output_json: bool = typer.Option(False, "--output-json", help="Output trajectory as JSON"),
    timeout: int = typer.Option(600, "--timeout", help="Execution timeout in seconds"),
    cwd: str = typer.Option(".", "--cwd", help="Working directory"),
) -> None:
    """Run TunaCode in non-interactive headless mode."""

    async def async_run() -> int:
        import os
        os.chdir(cwd)

        # Fresh state manager for isolation
        state = StateManager()

        # Set model if provided
        if model:
            state.session.current_model = model

        # Auto-approve mode (reuses existing yolo infrastructure)
        if auto_approve:
            state.session.yolo = True

        # Initialize tool handler
        tool_handler = ToolHandler(state)
        state.set_tool_handler(tool_handler)

        # Simple stdout streaming callback (optional)
        async def stdout_stream(token: str) -> None:
            if not output_json:
                print(token, end="", flush=True)

        try:
            result = await asyncio.wait_for(
                process_request(
                    message=prompt,
                    model=ModelName(state.session.current_model or "anthropic/claude-sonnet-4-20250514"),
                    state_manager=state,
                    tool_callback=None,  # Yolo mode handles this
                    streaming_callback=stdout_stream if not output_json else None,
                    tool_result_callback=None,
                    tool_start_callback=None,
                ),
                timeout=timeout,
            )

            if output_json:
                # Output trajectory for Harbor
                trajectory = {
                    "messages": [msg.model_dump() for msg in state.session.messages],
                    "tool_calls": state.session.tool_calls,
                    "usage": state.session.session_total_usage,
                    "success": True,
                }
                print(json.dumps(trajectory, indent=2))

            return 0

        except asyncio.TimeoutError:
            if output_json:
                print(json.dumps({"success": False, "error": "timeout"}))
            else:
                print("\nError: Execution timed out", file=sys.stderr)
            return 1
        except Exception as e:
            if output_json:
                print(json.dumps({"success": False, "error": str(e)}))
            else:
                print(f"\nError: {e}", file=sys.stderr)
            return 1

    exit_code = asyncio.run(async_run())
    raise typer.Exit(code=exit_code)
```

## Knowledge Gaps

1. **JSON Trajectory Schema:** Harbor tbench may have specific schema requirements for the trajectory JSON output. Need to verify expected format.

2. **Session Persistence:** Should headless runs save to session history? Currently unclear if `--output-json` should also persist locally.

3. **Progress Indication:** For long-running headless tasks without `--output-json`, should there be progress indicators to stderr?

4. **Error Exit Codes:** Need to define specific exit codes (e.g., 1=timeout, 2=auth failure, 3=model error).

5. **MCP Integration:** Does Harbor tbench need MCP server support in headless mode?

## References

### GitHub Issue
- https://github.com/alchemiststudiosDOTai/tunacode/issues/144

### Key Source Files (Permalinks)
- [main.py - CLI entry](https://github.com/alchemiststudiosDOTai/tunacode/blob/4033081dc3cd9385a6347513bd4ed7421c9f42ae/src/tunacode/ui/main.py)
- [main.py - Agent core](https://github.com/alchemiststudiosDOTai/tunacode/blob/4033081dc3cd9385a6347513bd4ed7421c9f42ae/src/tunacode/core/agents/main.py)
- [handler.py - Authorization](https://github.com/alchemiststudiosDOTai/tunacode/blob/4033081dc3cd9385a6347513bd4ed7421c9f42ae/src/tunacode/tools/authorization/handler.py)
- [rules.py - Auth rules](https://github.com/alchemiststudiosDOTai/tunacode/blob/4033081dc3cd9385a6347513bd4ed7421c9f42ae/src/tunacode/tools/authorization/rules.py)
- [state.py - Session state](https://github.com/alchemiststudiosDOTai/tunacode/blob/4033081dc3cd9385a6347513bd4ed7421c9f42ae/src/tunacode/core/state.py)

### Related Git History
- `8db8eb4` - rollback: pre-benchmark implementation checkpoint
- `5d3b65c` - rollback: pre-benchmark implementation checkpoint

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLI Entry Point                          │
│                      src/tunacode/ui/main.py                    │
├─────────────────────────────┬───────────────────────────────────┤
│    main() [TUI Mode]        │     run() [Headless Mode] NEW     │
│            │                │              │                    │
│            ▼                │              ▼                    │
│    run_textual_repl()       │     process_request()             │
│            │                │         (direct call)             │
│            ▼                │              │                    │
│    TextualReplApp           │              │                    │
│    - UI widgets             │              │                    │
│    - Confirmations          │              │                    │
│            │                │              │                    │
└────────────┼────────────────┴──────────────┼────────────────────┘
             │                               │
             ▼                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                    process_request()                            │
│              src/tunacode/core/agents/main.py:526               │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              RequestOrchestrator.run()                   │   │
│  │                                                          │   │
│  │   ┌──────────────────────────────────────────────────┐  │   │
│  │   │            Iteration Loop                         │  │   │
│  │   │   - Stream tokens (via callback or None)          │  │   │
│  │   │   - Process nodes                                 │  │   │
│  │   │   - Execute tools (with auth check)               │  │   │
│  │   │   - Track productivity                            │  │   │
│  │   └──────────────────────────────────────────────────┘  │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Tool Authorization                            │
│            src/tunacode/tools/authorization/                    │
│                                                                 │
│   ┌───────────────────┐    ┌──────────────────────────────┐    │
│   │   should_confirm()│───▶│   AuthorizationPolicy        │    │
│   │   handler.py:42   │    │   - ReadOnlyToolRule (200)   │    │
│   └───────────────────┘    │   - TemplateAllowedRule(210) │    │
│                            │   - YoloModeRule (300) ◀──┐  │    │
│                            │   - ToolIgnoreRule (310)  │  │    │
│                            └───────────────────────────┼──┘    │
│                                                        │       │
│   session.yolo = True ─────────────────────────────────┘       │
│   (--auto-approve flag sets this)                              │
└─────────────────────────────────────────────────────────────────┘
```

## Complexity Assessment

| Aspect | Complexity | Reason |
|--------|------------|--------|
| CLI Command | Low | Simple Typer command addition |
| Auto-Approve | Low | Existing `yolo` mode reusable |
| JSON Output | Medium | Need to serialize messages/tool_calls |
| Timeout | Low | `asyncio.wait_for()` wrapping |
| CWD | Low | `os.chdir()` before execution |
| Exit Codes | Low | Return codes from async_run |

**Estimated Effort:** This is straightforward - the architecture already supports headless execution. Main work is wiring up the CLI command and JSON serialization.
