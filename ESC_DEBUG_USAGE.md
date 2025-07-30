# ESC Debugging Usage Guide

The ESC debugging system is now fully integrated into TunaCode and can be enabled in several ways to help debug ESC interruption issues.

## 🚀 Quick Start

### Option 1: Environment Variable (Recommended)

```bash
export TUNACODE_ESC_DEBUG=1
python -m tunacode
```

### Option 2: Command Line Flag

```bash
python -m tunacode --debug-esc
```

### Option 3: Using the Standalone Debug Script

```bash
python debug_esc.py
```

## 📋 What Gets Logged

When ESC debugging is enabled, you'll see:

1. **Automatic notification** when debugging starts:
   ```
   🐛 ESC debugging auto-enabled via TUNACODE_ESC_DEBUG environment variable
   📝 Debug log: /path/to/tunacode/esc.log
   ```

2. **Real-time debug events** logged to `esc.log` including:
   - User input detection
   - ESC key monitoring setup
   - ESC key press detection
   - Interrupt event propagation
   - Task cancellation
   - Cleanup operations

3. **Debug summary** when the app exits (with `--debug-esc` flag)

## 🔍 How to Test ESC Interruption

1. **Start TunaCode with debugging**:
   ```bash
   export TUNACODE_ESC_DEBUG=1
   python -m tunacode
   ```

2. **Trigger agent processing** by entering a query that requires thinking:
   ```
   > write a hello world program in python
   ```

3. **Press ESC while the agent is processing** (look for "Thinking..." or streaming output)

4. **Check the debug log**:
   ```bash
   tail -f esc.log
   ```

## 📊 Understanding the Debug Log

### Successful ESC Flow
```
[USER_INPUT     ] User input received: 'write a hello world program'
[THINKING_START ] Agent processing started
[ESC_SETUP      ] ESC monitoring context manager entered
[ESC_ENABLE     ] Enabling ESC monitoring  
[ESC_BINDINGS_CREATE] ESC key bindings created and installed
[ESC_PRESSED    ] ESC key press detected by prompt_toolkit
[ESC_HANDLER    ] ESC handler execution started
[INTERRUPT_SIGNAL] Interrupt event signaled
[TASK_CANCEL_SCHEDULED] Task cancellation scheduled
[INTERRUPT_CHK  ] Interrupt check at agent_iteration_start | interrupted=True
[CANCELLED_ERR  ] asyncio.CancelledError raised
[CLEANUP_START  ] Interrupt cleanup operations started
[CLEANUP_DONE   ] Interrupt cleanup completed
```

### Common Issues and Solutions

#### ESC Not Detected
**Log shows:** `ESC_SETUP_FAIL` or missing `ESC_PRESSED` events
**Solution:** Ensure you're running in a proper terminal environment with prompt_toolkit support

#### Task Not Cancelling
**Log shows:** `INTERRUPT_CHK` always shows `interrupted=False`
**Solution:** Check that interrupt event is being properly signaled (`INTERRUPT_SIGNAL` event)

#### Cleanup Issues
**Log shows:** Missing `CLEANUP_*` events
**Solution:** Check for exceptions in the cleanup process

## 🛠️ Debug Commands

### View Recent Debug Events
```bash
tail -20 esc.log
```

### Filter by Event Type
```bash
grep "ESC_PRESSED" esc.log
grep "INTERRUPT_CHK" esc.log
grep "TASK_CANCEL" esc.log
```

### Monitor Real-time
```bash
tail -f esc.log
```

### Count Event Types
```bash
cut -d'|' -f5 esc.log | cut -d']' -f1 | cut -d'[' -f2 | sort | uniq -c
```

## 🎯 Environment Variables

| Variable | Values | Description |
|----------|--------|-------------|
| `TUNACODE_ESC_DEBUG` | `1`, `true`, `yes`, `on` | Auto-enable ESC debugging |

## 🧪 Testing Integration

You can also test the debugging system without running the full app:

```bash
python test_esc_debug.py
```

This will verify that:
- ✅ Debug logging is working
- ✅ ESC monitoring setup works
- ✅ State manager integration works
- ✅ Event logging is comprehensive

## 📱 Command Line Options

```bash
python -m tunacode --help
```

Look for:
```
--debug-esc    Enable ESC interruption debugging
```

## 🔧 Troubleshooting

### Debug Log Not Created
- Check write permissions in the current directory
- Verify the environment variable is set correctly:
  ```bash
  echo $TUNACODE_ESC_DEBUG
  ```

### No Debug Output
- Ensure debugging is enabled via environment variable or flag
- Check that you're triggering agent processing (not just typing commands)

### ESC Not Working
- Verify terminal supports prompt_toolkit key bindings
- Check that TunaCode is running in interactive mode
- Look for `ESC_SETUP_FAIL` in the debug log

## 📈 Performance Impact

The ESC debugging system:
- ✅ **Minimal overhead**: Only logs when events occur
- ✅ **Async-safe**: All logging is non-blocking
- ✅ **Thread-safe**: Works correctly in multi-threaded environments
- ✅ **Clean shutdown**: Automatically cleans up debug context

## 🎨 Example Debug Session

```bash
# Terminal 1: Start TunaCode with debugging
export TUNACODE_ESC_DEBUG=1
python -m tunacode

# Terminal 2: Monitor debug log
tail -f esc.log

# In TunaCode:
> write a fibonacci function
# Press ESC while it's thinking

# Check terminal 2 for complete ESC flow trace
```

This comprehensive debugging system will help you identify and fix any issues with ESC interruption in TunaCode!