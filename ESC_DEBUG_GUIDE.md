# ESC Interruption Debug Guide

This guide explains how to debug the ESC interruption flow in TunaCode, from user input to execution completion.

## Quick Start

### 1. Run the ESC Debug Test Script

```bash
cd /path/to/tunacode
python3 debug_esc.py
```

This will:
- Enable comprehensive ESC debugging 
- Start TunaCode with debug tracing active
- Show instructions for testing ESC interruption
- Generate a detailed `esc.log` file

### 2. Test ESC Interruption

1. Enter a query that triggers agent thinking: `"write a hello world program"`
2. While the agent is processing, press **ESC**
3. Observe the interruption behavior
4. Type `exit` to quit and see debug summary

## Debug Flow Overview

The ESC debugging system traces the complete flow:

```
User Input → Thinking Start → ESC Setup → ESC Press → Task Cancel → Cleanup
     ↓             ↓            ↓          ↓           ↓           ↓
  INPUT_SETUP  THINKING_START  ESC_ENABLE  ESC_PRESSED TASK_CANCEL CLEANUP_DONE
```

## Debug Event Types

### 📥 User Input Events
- `INPUT_SETUP` - Multiline input setup
- `INPUT_WAITING` - Waiting for user input
- `USER_INPUT` - User input received
- `AGENT_REQUEST` - Agent request processing starts

### 🧠 Agent Processing Events  
- `THINKING_START` - Agent processing begins
- `INTERRUPT_CHK` - Interrupt checking during processing
- `CANCELLED_ERR` - CancelledError raised

### ⌨️ ESC Setup Events
- `ESC_SETUP` - ESC monitoring setup
- `INTERRUPT_INIT` - Interrupt event initialization
- `ESC_ENABLE` - ESC monitoring enabled
- `ESC_BINDINGS_CREATE` - ESC key bindings created
- `ESC_BINDINGS_MERGE` - Bindings merged with existing ones

### 🚨 ESC Trigger Events
- `ESC_PRESSED` - ESC key detected by prompt_toolkit
- `ESC_HANDLER` - ESC handler execution starts
- `VISUAL_FB` - Visual feedback shown to user
- `INTERRUPT_SIGNAL` - Interrupt event signaled

### ⚡ Task Cancellation Events
- `TASK_CANCEL_REQ` - Task cancellation requested
- `TASK_CANCEL_SCHEDULED` - Cancellation scheduled in event loop
- `INTERRUPT_SIG` - Interrupt event set
- `STATE_MGR` - State manager actions

### 🧹 Cleanup Events
- `CLEANUP_START` - Cleanup operations start
- `CLEANUP_STREAMING` - Streaming panel cleanup
- `CLEANUP_SPINNER` - Spinner cleanup
- `CLEANUP_DONE` - Cleanup completed

## Log File Format

Each log entry contains:

```
HH:MM:SS.mmm | LEVEL | Thread | Function | [EVENT_TYPE] Context | Message
```

Where:
- **Time**: Precise timestamp with milliseconds
- **Thread**: Thread ID for concurrency tracking
- **Context**: Session ID, async task info, thread name
- **Event Type**: Categorized event type (15 chars, left-aligned)
- **Message**: Detailed event description

### Example Log Entry

```
15:41:49.601 | DEBUG | T:8612241152 | log_event | [ESC_PRESSED    ] S9600 | Task:agent_task | TH:MainThread | ESC key press detected by prompt_toolkit
```

## Debugging Specific Issues

### ESC Not Detected
Look for these events:
- `ESC_SETUP` - Is monitoring being set up?
- `ESC_BINDINGS_CREATE` - Are key bindings created?
- `ESC_PRESSED` - Is the key press detected?

### Task Not Cancelling  
Check these events:
- `TASK_CANCEL_SCHEDULED` - Is cancellation scheduled?
- `INTERRUPT_SIG` - Is interrupt event signaled?
- `INTERRUPT_CHK` - Are interrupt checks happening?

### Cleanup Issues
Monitor these events:
- `CLEANUP_START` - Does cleanup begin?
- `CLEANUP_STREAMING` - Streaming panel cleanup
- `CLEANUP_SPINNER` - Spinner cleanup
- `CLEANUP_DONE` - Full cleanup completion

## Manual Debugging

You can also enable debugging manually in your code:

```python
from tunacode.utils.esc_debug import enable_esc_debugging, log_esc_event

# Enable debugging for a section
with enable_esc_debugging():
    # Your code here
    log_esc_event("CUSTOM_EVENT", "Custom debug message")
    
    # Run TunaCode operations
    await process_request(text, state_manager)
```

## Interpreting Results

### Successful ESC Flow

A successful ESC interruption should show:

1. `ESC_PRESSED` - Key detected
2. `ESC_HANDLER` - Handler executes  
3. `INTERRUPT_SIGNAL` - Event signaled
4. `TASK_CANCEL_SCHEDULED` - Cancellation scheduled
5. `INTERRUPT_CHK` with `interrupted=True` - Check detects interrupt
6. `CANCELLED_ERR` - CancelledError raised
7. `CLEANUP_START` through `CLEANUP_DONE` - Clean shutdown

### Failed ESC Flow

Common failure patterns:

- **No `ESC_PRESSED`**: Key binding not working
- **No `TASK_CANCEL_SCHEDULED`**: Task cancellation failed
- **`INTERRUPT_CHK` always `False`**: Interrupt checking not working
- **No `CANCELLED_ERR`**: Exception not propagating
- **Missing cleanup events**: Cleanup not completing

## Performance Analysis

The debug system tracks:
- **Session duration**: Total time from start to end
- **Event counts**: Number of each event type
- **Thread information**: Which threads events occur on
- **Async task context**: Current async task names

Use this data to identify performance bottlenecks or race conditions in the ESC flow.

## Troubleshooting

### Log File Not Created
- Check write permissions in current directory
- Ensure `esc_debug.py` module imports correctly

### Missing Events  
- Verify debug context is active: `with enable_esc_debugging():`
- Check that the problematic code path includes debug calls

### Too Much Logging
- Filter by event type: `grep "ESC_PRESSED" esc.log`
- Focus on specific time ranges
- Use the event count summary

## Event Type Reference

| Category | Events | Purpose |
|----------|--------|---------|
| Input | `INPUT_*`, `USER_INPUT`, `AGENT_REQUEST` | Track user interaction |
| Setup | `ESC_SETUP`, `INTERRUPT_INIT`, `ESC_ENABLE` | Monitor initialization |
| Bindings | `ESC_BINDINGS_*`, `PROMPT_TK` | Track key binding setup |
| Trigger | `ESC_PRESSED`, `ESC_HANDLER`, `VISUAL_FB` | Monitor ESC detection |
| Interrupt | `INTERRUPT_*`, `STATE_MGR` | Track interrupt propagation |
| Cancel | `TASK_CANCEL_*`, `CANCELLED_ERR` | Monitor task cancellation |
| Cleanup | `CLEANUP_*` | Track cleanup operations |

Use this comprehensive debugging system to identify and fix any issues in the ESC interruption flow!