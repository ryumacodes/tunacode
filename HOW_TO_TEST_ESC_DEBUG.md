# How to Test ESC Debugging - Step by Step

The ESC debugging system is working, but you need to run it correctly. Here are the exact steps:

## ✅ Method 1: Environment Variable (Recommended)

1. **Set the environment variable** in your terminal:
   ```bash
   export TUNACODE_ESC_DEBUG=1
   ```

2. **Navigate to the TunaCode directory**:
   ```bash
   cd "/Users/affan/Projects/untitled folder/tunacode"
   ```

3. **Run TunaCode however you normally run it**. This could be:
   ```bash
   # If you have it installed:
   tunacode
   
   # Or if you run it directly:
   python3 -m tunacode
   
   # Or if you run it from src:
   PYTHONPATH=src python3 -m tunacode.cli.main
   ```

4. **You should see this message** when TunaCode starts:
   ```
   🐛 ESC debugging auto-enabled via TUNACODE_ESC_DEBUG environment variable
   📝 Debug log: /path/to/tunacode/esc.log
   ```

5. **Test ESC interruption**:
   - Enter a query that makes the agent think: `"write a hello world program"`
   - While it's processing, press **ESC**
   - Check `esc.log` for the debug trace

## ✅ Method 2: Command Line Flag

If you can run TunaCode with command line arguments:

```bash
tunacode --debug-esc
# or
python3 -m tunacode.cli.main --debug-esc
```

## ✅ Method 3: Quick Test to Verify It's Working

Run this test to confirm the debugging system is working:

```bash
cd "/Users/affan/Projects/untitled folder/tunacode"
TUNACODE_ESC_DEBUG=1 python3 test_real_flow.py
```

You should see:
- Debug notification messages
- A debug summary at the end
- Events logged to `esc.log`

## 🐛 Troubleshooting

### Issue: "No prompt_toolkit app found"
This is normal when testing outside of the actual TunaCode REPL. The ESC monitoring will only work when TunaCode is running interactively.

### Issue: Environment variable not working
Check that it's set correctly:
```bash
echo $TUNACODE_ESC_DEBUG
```
Should output: `1`

### Issue: esc.log is empty
- Make sure you set `TUNACODE_ESC_DEBUG=1` BEFORE running TunaCode
- Make sure you're running the actual TunaCode app, not just test scripts
- The log only populates when debug events occur (user input, agent processing, ESC presses)

## 📋 What You Should See in esc.log

When working correctly, you'll see events like:

```
[INPUT_SETUP    ] Setting up multiline input with key bindings
[USER_INPUT     ] Input received: 'write a hello world program'
[THINKING_START ] Agent processing started
[ESC_SETUP      ] ESC monitoring context manager entered
[ESC_ENABLE     ] Enabling ESC monitoring
[ESC_PRESSED    ] ESC key press detected by prompt_toolkit  <-- This is the key event!
[INTERRUPT_SIGNAL] Interrupt event signaled
[TASK_CANCEL_SCHEDULED] Task cancellation scheduled
[CANCELLED_ERR  ] asyncio.CancelledError raised
```

## 🎯 The Most Important Step

**The key is that you must run the actual TunaCode application with the environment variable set.** The debug system only logs events when they actually happen in the real app flow.

If you're still having issues, let me know:
1. How do you normally run TunaCode?
2. What do you see when you run the test commands above?
3. Is the `esc.log` file being created at all?