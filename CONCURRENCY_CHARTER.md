# TunaCode Concurrency Charter

## Mission Statement
All concurrent operations in TunaCode must run under Trio's structured concurrency model to ensure predictable cancellation, resource cleanup, and deadlock-free execution.

## Core Principles

### 1. Nursery-First Architecture
- **All background work must run under a Trio nursery**
- Every concurrent operation gets a managed task scope
- No orphaned tasks or unmanaged threads
- Clean resource teardown guaranteed

### 2. Cancellation Discipline
- **Timeouts and cancellations use `trio.CancelScope`**
- All operations respect cancellation requests
- Graceful degradation on interrupt signals (SIGINT/Esc)
- No blocking operations that ignore cancellation

### 3. Thread Boundary Management
- **Blocking calls live in `trio.to_thread.run_sync()`**
- File I/O, subprocess execution, and network calls properly isolated
- Main trio context remains responsive during blocking operations
- Thread pool automatically managed by trio

### 4. Signal Integration
- SIGINT and Esc key trigger the same `AbortController.abort()` flow
- Global interrupt handling integrated with trio's run loop
- Consistent user experience for operation cancellation

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     REPL Root Task                         │
│  ┌─────────────────────────────────────────────────────────┤
│  │                 UI Nursery                              │
│  │  ┌─────────────┬─────────────┬─────────────────────────┤
│  │  │   Prompt    │   Spinner   │   Streaming Panel      │
│  │  │    Task     │    Task     │        Task             │
│  │  └─────────────┴─────────────┴─────────────────────────┤
│  └─────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────┤
│  │              Agent "Thinking" Task                      │
│  │  ┌─────────────────────────────────────────────────────┤
│  │  │         Tool Execution Nursery                      │
│  │  │  ┌───────────┬───────────┬──────────────────────────┤
│  │  │  │Subprocess │ File I/O  │   HTTP Streaming         │
│  │  │  │   Task    │   Task    │       Task               │
│  │  │  └───────────┴───────────┴──────────────────────────┤
│  │  └─────────────────────────────────────────────────────┤
│  └─────────────────────────────────────────────────────────┤
└─────────────────────────────────────────────────────────────┘
```

## Implementation Guidelines

### AbortController Pattern
```python
class AbortController:
    def __init__(self):
        self.abort_event = trio.Event()
    
    def abort(self):
        self.abort_event.set()
    
    async def check_abort(self):
        if self.abort_event.is_set():
            raise trio.Cancelled
```

### Nursery Task Structure
```python
async def main_repl_loop():
    async with trio.open_nursery() as nursery:
        nursery.start_soon(ui_task)
        nursery.start_soon(agent_task)
        # All tasks auto-cancelled on exit
```

### Thread Integration
```python
# Blocking operations
result = await trio.to_thread.run_sync(
    subprocess.run, 
    ["git", "status"], 
    capture_output=True
)
```

## Migration Commitments

1. **Zero asyncio imports** in new code
2. **All timeouts** converted to `trio.CancelScope`
3. **No threading.Thread** - only `trio.to_thread`
4. **Esc key cancellation** works within 100ms
5. **Prompt recovery** after any cancellation

This charter ensures TunaCode's concurrency model is simple, predictable, and user-friendly.