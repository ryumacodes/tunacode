# 🚀 Trio Migration Debug Usage Guide

## Quick Start

The Trio migration includes comprehensive debug visuals for live testing. Due to a CLI configuration issue, use these alternative methods to access debug features:

### Method 1: Debug Launcher Script (Recommended)

```bash
python debug_tunacode.py
```

This launches TunaCode with full debug visualization enabled from startup.

### Method 2: Runtime Debug Commands

1. Start TunaCode normally:
   ```bash
   python -m tunacode.cli.main
   ```

2. Enable debug visualization:
   ```bash
   /debug on
   ```

3. Test cancellation features:
   - Press **Esc** during any operation
   - Press **Ctrl+C** for signal handling
   - Type commands to see agent processing

4. Control debug display:
   ```bash
   /debug off      # Disable debug display
   /debug status   # Check if debug is active  
   /debug summary  # Show session statistics
   ```

### Method 3: Environment Variable

```bash
export TUNACODE_DEBUG=1
python -m tunacode.cli.main
```

## 🎯 What You'll See

### Live Debug Dashboard

```
🚀 Trio Migration Live Debug
┌─────────────────────────────────────────────────┐
│ Component        Active    Total    Status      │
├─────────────────────────────────────────────────┤
│ Nurseries           2        3     ✅ Running   │
│ Tasks               5       12     ✅ Managed   │
│ CancelScopes        3        8     ✅ Protected │
│ AbortControllers    1        2     ✅ Ready     │
└─────────────────────────────────────────────────┘

📋 Recent Events
┌──────────────┬───────────────┬──────────────┬──────────────────┐
│ Time         │ Component     │ Event        │ Details          │
├──────────────┼───────────────┼──────────────┼──────────────────┤
│ 14:32:15.123 │ Input         │ KEY_PRESS    │ Esc -> abort     │
│ 14:32:15.089 │ AbortController│ ABORT_SIGNAL │ Esc key trigger  │
│ 14:32:14.992 │ Agent         │ STREAM_START │ agent-thinking   │
│ 14:32:14.856 │ Trio          │ TASK_SPAWN   │ agent_processing │
└──────────────┴───────────────┴──────────────┴──────────────────┘

🔧 Live Debug Controls:
• Press Esc to test cancellation
• Press Ctrl+C to test signal handling
• Type commands to see agent processing
• Use /debug to toggle this display
```

## 🧪 Testing Scenarios

### 1. **Esc Key Cancellation** (Primary Goal)

**Test Steps:**
1. Enable debug: `/debug on`
2. Start a long-running operation (e.g., ask a complex question)
3. Press **Esc** during "Thinking..." phase
4. Watch the debug events:

**Expected Debug Output:**
```
14:32:15.089 │ Input         │ KEY_PRESS      │ Esc -> abort_operation
14:32:15.092 │ AbortController│ ABORT_SIGNAL   │ abort-a1b2c3d4 triggered by Esc key  
14:32:15.095 │ Trio          │ CANCEL_SCOPE_CANCEL │ scope-12345 (AbortController Esc key)
14:32:15.112 │ UI            │ PROMPT_RECOVERY │ Recovered in 0.023s
```

**Success Criteria:**
- ✅ KEY_PRESS event logged immediately
- ✅ ABORT_SIGNAL triggered by "Esc key"
- ✅ CANCEL_SCOPE_CANCEL shows scope cancellation
- ✅ PROMPT_RECOVERY < 100ms
- ✅ Prompt returns immediately

### 2. **Signal Handling** (Ctrl+C)

**Test Steps:**
1. Start an operation
2. Press **Ctrl+C**
3. Verify same flow as Esc

**Expected Debug Output:**
```
14:33:20.456 │ Signal        │ SIGNAL_RECEIVED │ SIGINT -> abort_controller.abort
14:33:20.459 │ AbortController│ ABORT_SIGNAL   │ abort-a1b2c3d4 triggered by Signal SIGINT
14:33:20.462 │ Trio          │ CANCEL_SCOPE_CANCEL │ scope-12345 (AbortController Signal SIGINT)
```

### 3. **Streaming Cancellation**

**Test Steps:**
1. Enable streaming in settings
2. Ask a question to trigger streaming
3. Press **Esc** during streaming
4. Watch for immediate stop

**Expected Debug Output:**
```
14:34:10.123 │ Agent         │ STREAM_START   │ agent-stream-001
14:34:12.456 │ Input         │ KEY_PRESS      │ Esc -> abort_operation
14:34:12.459 │ Agent         │ STREAM_STOP    │ agent-stream-001 (cancelled)
```

### 4. **Nursery Lifecycle**

**Test Steps:**
1. Execute various commands
2. Watch nursery creation/closure
3. Monitor task spawning

**Expected Debug Output:**
```
14:35:05.789 │ Trio          │ NURSERY_CREATE │ Nursery #1
14:35:05.823 │ Trio          │ TASK_SPAWN     │ agent_processing in root-nursery
14:35:08.456 │ Trio          │ NURSERY_CLOSE  │ root-nursery (3 tasks)
```

## 📊 Performance Validation

### Cancellation Response Time

The debug system tracks critical timing metrics:

```bash
/debug summary
```

**Key Metrics:**
- **Esc Response**: < 100ms from key press to cancellation
- **Prompt Recovery**: < 100ms to return interactive prompt  
- **Signal Handling**: < 50ms for SIGINT/SIGTERM processing
- **Stream Cancellation**: Immediate (next chunk)

### Real-time Monitoring

Watch the live counters to verify:
- **Active Nurseries**: Should return to baseline after operations
- **Active Tasks**: Should not accumulate (no leaks)
- **Active CancelScopes**: Should be created/cancelled properly
- **Active AbortControllers**: Should reset after use

## 🔍 Event Reference

### Critical Events for Trio Migration

| Event Type | Component | Meaning | Success Indicator |
|------------|-----------|---------|-------------------|
| `KEY_PRESS` | Input | User pressed key | Esc logged immediately |
| `ABORT_SIGNAL` | AbortController | Abort triggered | Shows trigger source |
| `CANCEL_SCOPE_CANCEL` | Trio | Scope cancelled | References AbortController |
| `PROMPT_RECOVERY` | UI | Prompt restored | Time < 100ms |
| `SIGNAL_RECEIVED` | Signal | OS signal handled | Shows signal type |
| `NURSERY_CREATE` | Trio | New nursery opened | Shows hierarchy |
| `NURSERY_CLOSE` | Trio | Nursery closed cleanly | Shows task count |
| `STREAM_START` | Agent | Streaming began | Shows stream ID |
| `STREAM_STOP` | Agent | Streaming ended | Shows reason |

## 🚨 Troubleshooting

### Debug Display Not Showing

1. **Check availability:**
   ```bash
   /debug status
   ```

2. **Manual enable:**
   ```bash
   /debug on
   ```

3. **Environment override:**
   ```bash
   export TUNACODE_DEBUG=1
   ```

### Missing Events

- Verify module imports are working
- Check if component has debug integration
- Ensure `DEBUG_AVAILABLE` flag is `True`

### CLI Issues

If `tunacode --debug` doesn't work:
1. Use `python debug_tunacode.py` instead
2. Or use runtime `/debug on` command
3. Or set `TUNACODE_DEBUG=1` environment variable

## 🎉 Success Criteria

**The Trio migration is working correctly when:**

✅ **Esc Cancellation**: Pressing Esc during any operation returns to prompt within 100ms  
✅ **Signal Handling**: Ctrl+C triggers the same abort flow as Esc  
✅ **Streaming Response**: Streaming stops immediately when cancelled  
✅ **Resource Cleanup**: No leaked nurseries, tasks, or scopes  
✅ **Structured Concurrency**: All operations run under managed nurseries  
✅ **Prompt Recovery**: Interactive prompt returns cleanly after any cancellation  

**Debug visualization confirms:**
- All abort signals are properly propagated
- CancelScopes are created and cancelled correctly  
- Nursery lifecycle is managed properly
- No deadlocks or hanging operations
- Performance targets are met (< 100ms response)

The debug system provides complete transparency into the Trio migration's operation, ensuring the core goal of **instant Esc key cancellation** is achieved with structured concurrency.