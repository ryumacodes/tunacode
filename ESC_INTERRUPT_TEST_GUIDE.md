# ESC Interrupt Testing Guide

This guide documents the comprehensive test suite for ESC interrupt functionality in TunaCode, ensuring that the ESC key behaves exactly like Ctrl-C across every code path.

## Overview

The ESC interrupt functionality allows users to cancel long-running operations (like LLM requests) by pressing the ESC key, providing a responsive user experience even during intensive processing.

### Core Components Tested

1. **AbortController** (`src/tunacode/core/abort_controller.py`) - Centralized cancellation mechanism
2. **Cancellable Processing** (`src/tunacode/utils/cancellable_processing.py`) - Wrapper functions for cancellable operations  
3. **Keyboard Monitor** (`src/tunacode/utils/keyboard_monitor.py`) - Raw keyboard input monitoring during background operations

## Test Architecture

### 1. Unit Tests (`tests/test_esc_interrupt_unit.py`)

**Purpose**: Unit-level sanity checks with deterministic fake operations.

**Key Tests**:
- **Stubbed Agent Test**: 5-second fake agent operation to test cancellation timing
- **Direct CancelScope Test**: Start operation in nursery, abort after 100ms, verify clean exit
- **Repeated Start/Abort**: 20 cycles of random cancellation timing to detect memory leaks
- **Fast Command Edge Case**: Ensure no stray "Cancelled" messages for already-completed operations
- **Double ESC Handling**: Verify only one cancellation path fires for multiple abort signals
- **Memory Leak Detection**: Thread count and resource cleanup validation

**Usage**:
```bash
# Run all unit tests
pytest tests/test_esc_interrupt_unit.py -v

# Run only cancellation-marked tests  
pytest tests/test_esc_interrupt_unit.py -m cancellation -v

# Quick smoke test
python run_esc_tests.py --type quick
```

### 2. Integration Tests (`tests/test_esc_interrupt_integration.py`)

**Purpose**: REPL boundary testing using pexpect-style simulation.

**Key Tests**:
- **pexpect Session**: Spawn tunacode, send long command, ESC after 200ms, expect "Request cancelled" within 300ms
- **REPL Responsiveness**: Verify REPL remains functional after cancellation
- **Double ESC/Ctrl-C**: Test interaction between ESC and Ctrl-C signals
- **Streaming Cancellation**: Cancel during token streaming, verify immediate UI shutdown
- **Subprocess Integration**: Real process spawning with signal handling

**Usage**:
```bash
# Run integration tests (requires pexpect)
pytest tests/test_esc_interrupt_integration.py -v

# Run with integration marker
pytest tests/test_esc_interrupt_integration.py -m integration -v
```

### 3. Concurrency Tests (`tests/test_esc_interrupt_concurrency.py`)

**Purpose**: Stress testing under high concurrency and resource pressure.

**Key Tests**:
- **Parallel Nursery Stress**: 4 nurseries with multiple operations, random cancellation
- **Streaming Response Torture**: Multiple concurrent streams with cancellation
- **Memory Pressure**: Test cancellation behavior under memory constraints  
- **Thread Safety**: Cross-nursery abort controller usage with background threads
- **Resource Cleanup**: Verify proper cleanup during mass cancellation
- **CPU Usage**: Monitor CPU during intensive cancellable operations

**Usage**:
```bash
# Run concurrency tests (slow)
pytest tests/test_esc_interrupt_concurrency.py -v -m "slow and cancellation"

# Run parametrized stress tests
pytest tests/test_esc_interrupt_concurrency.py -k "parametrized" -v
```

## Running Tests

### Local Testing

```bash
# Run all ESC interrupt tests
python run_esc_tests.py --type all

# Quick smoke test (< 1 minute)
python run_esc_tests.py --type quick

# Run specific test type
python run_esc_tests.py --type unit --verbose

# Run with custom timeout
python run_esc_tests.py --type concurrency --timeout 600
```

### CI/CD Integration

The GitHub Actions workflow (`.github/workflows/esc-cancellation-tests.yml`) runs:

- **Unit Tests**: Fast validation across Python 3.9-3.12 on Ubuntu/macOS
- **Integration Tests**: pexpect-based REPL testing  
- **Concurrency Tests**: Stress testing with extended timeouts
- **Timing Validation**: Ensures cancellation < 2 seconds wall-clock time
- **Memory Leak Check**: Resource cleanup verification
- **Fallback Trigger**: Alerts for consecutive failures

### Matrix Testing

Tests run across:
- **OS**: Ubuntu Latest, macOS Latest
- **Python**: 3.9, 3.10, 3.11, 3.12
- **Concurrency Levels**: 5, 10, 20 operations
- **Cancel Rates**: 30%, 50%, 80%

## Test Markers

Use pytest markers to filter tests:

```bash
# Cancellation-specific tests
pytest -m cancellation

# Integration tests only  
pytest -m integration

# Slow/stress tests
pytest -m slow

# Quick essential tests
pytest -m "cancellation and not slow"
```

## Expected Behavior

### Successful Test Run
- All cancellation requests complete within 2 seconds
- No thread count growth across multiple operations  
- UI components shut down immediately on cancellation
- REPL remains responsive after cancellation
- No stray "Cancelled" messages for completed operations

### Failure Scenarios

If tests fail consistently:

1. **Check trio-asyncio Integration**: Cancellation may be lost in async bridge
2. **Terminal/TTY Issues**: Keyboard monitoring may fail on certain platforms
3. **Timing Races**: AbortController state may have race conditions
4. **Resource Leaks**: Memory/thread cleanup may be incomplete

### Fallback Plan

If 2+ consecutive CI runs fail, implement the simpler **pre-emptive cancellation window**:
- Show "Press ESC to cancel" prompt before starting operations
- Give users 2-second window to cancel before proceeding
- Buys time to debug trio-asyncio integration issues

## Debugging

### Enable Debug Logging

```python
# Add to test environment
import logging
logging.basicConfig(level=logging.DEBUG)

# Or use trio debug system
from tunacode.debug.trio_debug import trio_debug
trio_debug.enable()
```

### Common Issues

1. **Test Timeouts**: Increase timeout in conftest.py or CI configuration
2. **pexpect Failures**: May need platform-specific handling for terminal control
3. **Memory Test Flakiness**: GC timing can affect memory measurements
4. **Race Conditions**: Add strategic `await trio.sleep(0.01)` for task yielding

### Instrumentation

Tests include structured logging for debugging:
- **TASK-START/STOP**: Every asyncio task creation/completion
- **CANCELLED**: All cancellation events with trigger information  
- **SCOPE_LINKED**: AbortController/CancelScope associations
- **KEYBOARD_MONITOR**: Raw key detection events

## Performance Expectations

### Timing Requirements
- Cancellation response: < 300ms
- Test suite completion: < 2 minutes (unit), < 5 minutes (integration), < 10 minutes (concurrency)
- CPU usage during cancellation: < 80% average
- Memory growth: < 100MB during stress tests

### Success Criteria
- ✅ Unit tests: 100% pass rate
- ✅ Integration tests: 95% pass rate (pexpect can be flaky)
- ✅ Concurrency tests: 90% pass rate (stress tests may occasionally fail)
- ✅ Timing validation: 100% pass rate with < 2s wall-clock time
- ✅ Memory tests: No significant leaks detected

## Contributing

When modifying ESC interrupt functionality:

1. **Run Tests First**: `python run_esc_tests.py --type quick`
2. **Add Tests**: Cover new cancellation paths
3. **Update Documentation**: Reflect behavior changes
4. **Check CI**: Ensure all platforms pass
5. **Performance Test**: Verify no regression in cancellation timing

The goal is to ensure ESC behaves exactly like Ctrl-C across every code path, providing users with reliable cancellation capabilities during long-running operations.