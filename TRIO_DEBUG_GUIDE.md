# Trio Migration Debug Guide

## 🚀 Live Debug Visualization

The Trio migration includes comprehensive debug visuals for live testing every aspect of the structured concurrency system. This guide shows you how to use and interpret the debug features.

## 🔧 Enabling Debug Mode

### Command Line Option
```bash
tunacode --debug
```
Starts TunaCode with live debug visualization enabled from the beginning.

### Runtime Toggle
```bash
/debug on          # Enable debug display
/debug off         # Disable debug display  
/debug status      # Check if debug is active
/debug summary     # Show session summary
```

## 📊 Debug Dashboard Components

### 1. **Statistics Panel**
Shows real-time counts of active Trio components:

```
Component        Active    Total    Status
Nurseries           2        3     ✅ Running
Tasks               5       12     ✅ Managed  
CancelScopes        3        8     ✅ Protected
AbortControllers    1        2     ✅ Ready
```

### 2. **Event Stream**
Live feed of the last 10 events with timestamps:

```
Time         Component        Event              Details
14:32:15.123 AbortController  ABORT_SIGNAL       abort-a1b2c3d4 triggered by Esc key
14:32:15.089 Input           KEY_PRESS          Esc -> abort_operation
14:32:14.992 Agent           STREAM_START       agent-thinking-001
14:32:14.856 Trio            TASK_SPAWN         agent_processing in root-nursery
```

### 3. **Interactive Controls**
Real-time instructions for testing:
- Press **Esc** to test cancellation
- Press **Ctrl+C** to test signal handling
- Type commands to see agent processing
- Use **`/debug`** to toggle display

## 🎯 What Gets Tracked

### **Nursery Operations**
- ✅ Creation with parent hierarchy
- ✅ Task spawning within nurseries
- ✅ Clean closure and resource cleanup

### **Cancellation System**
- ✅ CancelScope creation and linking
- ✅ AbortController state changes
- ✅ Manual and automatic cancellation triggers
- ✅ Signal handler integration (SIGINT/SIGTERM)

### **User Interactions**
- ✅ Key press events (Enter, Esc, Ctrl+O, etc.)
- ✅ Prompt interruption and recovery
- ✅ Command execution flow

### **Agent Processing**
- ✅ Streaming start/stop events
- ✅ Tool execution lifecycle
- ✅ Background task management

### **Error Conditions**
- ✅ Exception handling and recovery
- ✅ Timeout scenarios
- ✅ Resource cleanup on failures

## 🔍 Event Types Reference

### **Core Trio Events**
- `NURSERY_CREATE` - New nursery opened
- `NURSERY_CLOSE` - Nursery closed with task count
- `TASK_SPAWN` - Task started in nursery
- `CANCEL_SCOPE_CREATE` - CancelScope created
- `CANCEL_SCOPE_CANCEL` - CancelScope cancelled

### **AbortController Events**
- `ABORT_CONTROLLER_CREATE` - New controller instance
- `ABORT_SIGNAL` - Abort triggered with reason
- `ABORT_RESET` - Controller reset for reuse
- `SCOPE_LINKED` - CancelScope associated with controller

### **UI & Input Events**
- `KEY_PRESS` - Key pressed with action taken
- `PROMPT_INTERRUPT` - Prompt interrupted by user
- `PROMPT_RECOVERY` - Prompt recovered with timing
- `SIGNAL_RECEIVED` - OS signal received

### **Agent & Tool Events**
- `STREAM_START` - Agent streaming began
- `STREAM_STOP` - Agent streaming ended
- `TOOL_START` - Tool execution started
- `TOOL_COMPLETE` - Tool execution finished
- `AGENT_CHUNK` - Streaming content chunk

### **System Events**
- `DEBUG_START` - Debug visualization enabled
- `DEBUG_TOGGLE` - Debug display toggled
- `FUNC_ENTER` - Function entered (with decorator)
- `FUNC_EXIT` - Function exited successfully
- `FUNC_ERROR` - Function threw exception

## 🧪 Testing Scenarios

### **Esc Key Cancellation Test**
1. Start a long-running operation (agent thinking)
2. Press **Esc** during processing
3. Watch for:
   - `KEY_PRESS` event for Esc
   - `ABORT_SIGNAL` triggered by "Esc key"
   - `CANCEL_SCOPE_CANCEL` for active scopes
   - `PROMPT_RECOVERY` with timing < 100ms

### **Signal Handling Test**
1. Press **Ctrl+C** during operation
2. Watch for:
   - `SIGNAL_RECEIVED` for SIGINT
   - Same abort flow as Esc key
   - Clean nursery shutdown

### **Streaming Cancellation Test**
1. Start agent with streaming enabled
2. Cancel during streaming
3. Watch for:
   - `STREAM_START` event
   - `STREAM_STOP` with "cancelled" reason
   - Immediate response to cancellation

### **Nursery Lifecycle Test**
1. Execute commands that spawn background tasks
2. Watch for:
   - `NURSERY_CREATE` for new nurseries
   - `TASK_SPAWN` for each background task
   - `NURSERY_CLOSE` when operations complete

## 📈 Performance Metrics

The debug system tracks timing for critical operations:

- **Cancellation Response Time**: How quickly Esc/Ctrl+C triggers abort
- **Prompt Recovery Time**: How fast the prompt returns after cancellation
- **Nursery Lifecycle Duration**: Time from creation to closure
- **Streaming Latency**: Time between stream events

## 🛠️ Debug API Usage

For adding debug points to your own code:

```python
from tunacode.debug.trio_debug import trio_debug, debug_trio_function

# Automatic function tracing
@debug_trio_function("MyComponent")
async def my_async_function():
    # Function entry/exit automatically logged
    pass

# Manual event logging
trio_debug.log_event("CUSTOM_EVENT", "MyComponent", "Details here", "INFO")

# Nursery tracking
trio_debug.nursery_created("my-nursery-id")
trio_debug.task_spawned("my-nursery-id", "task_name", "task-id")

# Cancellation tracking  
trio_debug.cancel_scope_created("scope-id", timeout=5.0)
trio_debug.cancel_scope_cancelled("scope-id", "timeout")

# Stream tracking
trio_debug.streaming_started("stream-id")
trio_debug.streaming_stopped("stream-id", "completed")
```

## 🎨 Visual Indicators

### **Color Coding**
- 🟢 **Green**: Success events (creation, completion)
- 🟡 **Yellow**: Warning events (cancellation, interruption)  
- 🔴 **Red**: Error events (abort signals, failures)
- ⚪ **White**: Info events (normal operations)

### **Status Icons**
- ✅ **Active/Running**: Component is functioning normally
- ⚠️ **Warning**: Component has issues but continues
- ❌ **Error**: Component has failed
- 🔄 **Processing**: Component is actively working
- ⏸️ **Paused**: Component is temporarily suspended

## 🚨 Troubleshooting

### **Debug Display Not Showing**
1. Check if debug system is available: `/debug status`
2. Ensure rich library is installed
3. Try manually enabling: `/debug on`

### **Missing Events**
1. Verify component has debug integration
2. Check import path for debug system
3. Ensure DEBUG_AVAILABLE flag is True

### **Performance Impact**
1. Debug system is optimized for minimal overhead
2. Only keeps last 50 events in memory
3. Visual updates limited to 10 FPS
4. Safe to use in development/testing

## 📝 Summary

The Trio migration debug system provides comprehensive visibility into:

- **Structured Concurrency**: Real-time nursery and task management
- **Cancellation Flow**: Complete abort signal propagation 
- **User Interactions**: Key presses and prompt handling
- **Agent Operations**: Streaming and tool execution
- **Performance Metrics**: Timing for critical operations

This enables confident testing and validation of the Trio migration's core functionality, ensuring Esc key cancellation works reliably within 100ms and all operations are properly structured and cancellable.