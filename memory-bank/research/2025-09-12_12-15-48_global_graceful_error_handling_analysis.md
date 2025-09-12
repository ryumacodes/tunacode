# Research – Global Graceful Error Handling Analysis
**Date:** 2025-09-12
**Owner:** context-engineer:research
**Phase:** Research

## Goal
Summarize all *existing knowledge* before any new work. Analyze current error handling flows and identify issues with the existing global graceful error handling system.

## Additional Search
- `grep -ri "global.*error.*handling\|graceful.*error\|exception.*handling" .claude/`

## Findings

### Relevant files & why they matter:
- **`src/tunacode/exceptions.py`** → Defines comprehensive exception hierarchy with actionable error messages and suggested fixes
- **`src/tunacode/cli/repl.py`** → Main REPL with global exception handling in request processing loop, includes tool recovery attempts
- **`src/tunacode/utils/retry.py`** → Sophisticated retry system with exponential backoff for JSON parsing failures
- **`src/tunacode/utils/json_utils.py`** → Advanced JSON parsing with concatenated object recovery and safety validation
- **`src/tunacode/cli/repl_components/error_recovery.py`** → Two-level recovery system for malformed tool arguments and tool calling failures
- **`src/tunacode/core/agents/main.py`** → Agent loop error handling with structured exception management and tool message patching
- **`src/tunacode/core/agents/agent_components/state_transition.py`** → Enum-based state machine with thread-safe transitions and completion detection
- **`src/tunacode/core/agents/agent_components/node_processor.py`** → Tool execution processing with identified error handling gaps
- **`src/tunacode/core/agents/utils.py`** → Parallel tool execution with error collection and message patching for orphaned tools
- **`src/tunacode/core/logging/handlers.py`** → Structured logging with safe string coercion and rich formatting

## Key Patterns / Solutions Found

### **1. Hierarchical Exception System**
- **`TunaCodeError`** base class with comprehensive subtypes
- **Enhanced error messages** with suggested fixes, help URLs, and actionable guidance
- **Structured error categories**: Configuration, Tool Execution, Agent, Validation, Service, File Operation errors
- **Recovery-oriented design** with specific error types for different failure modes

### **2. Multi-Layer JSON Recovery System**
- **Exponential backoff retry** (max 10 retries, 0.1-5.0s delays)
- **Concatenated JSON object handling** with brace counting and validation
- **Safety validation** for read-only vs write tools to prevent dangerous executions
- **Fallback parsing strategies** when primary methods fail

### **3. Tool Recovery Mechanisms**
- **JSON args recovery** for malformed tool arguments
- **Tool extraction from text** when structured calling fails
- **Message patching** for orphaned tool calls to maintain conversation integrity
- **Parallel tool execution** with individual error collection using `return_exceptions=True`

### **4. State Machine Integration**
- **Enum-based state management** with `AgentStateMachine` class
- **Thread-safe state transitions** with validation rules
- **Completion detection** tied to RESPONSE state and `TUNACODE DONE:` markers
- **Legacy integration** maintaining backward compatibility

### **5. Graceful Degradation Patterns**
- **Fallback responses** when agent processing fails
- **Directory caching** with graceful filesystem fallback (50-500x performance improvement)
- **User-friendly error display** with enhanced formatting and actionable guidance

## Knowledge Gaps

### **Critical Issues Identified:**

#### **1. Inconsistent Tool-Level Error Handling**
**Location**: `src/tunacode/core/agents/agent_components/node_processor.py:450-451`
**Issue**: Individual tool execution lacks try-catch blocks
**Impact**: Unhandled tool exceptions can crash entire node processing
**Current code**: `await tool_callback(part, node)` without error handling

#### **2. Missing Global Exception Handlers**
**Issue**: No global exception handlers for unhandled async exceptions
**Impact**: Can cause silent failures or crashes in async contexts
**Current state**: Relies on per-function try-catch blocks

#### **3. Limited Error Context Propagation**
**Issue**: Error context (request ID, iteration count) not consistently included
**Impact**: Difficult debugging and error correlation
**Evidence**: Some error logs lack request context

#### **4. Inconsistent Recovery Strategy Application**
**Issue**: Recovery mechanisms scattered and not uniformly applied
**Impact**: Some components have robust recovery, others have minimal
**Example**: JSON parsing has excellent recovery, tool execution has minimal

#### **5. State Machine Error Handling Gaps**
**Location**: `src/tunacode/core/agents/agent_components/response_state.py:73-75`
**Issue**: State transition errors handled inconsistently
**Impact**: Can leave system in undefined state

### **Historical Context:**
- **Major JSON Recovery Incident (August 2025)**: CLI agent failures with "Invalid JSON … Extra data" errors led to comprehensive JSON recovery system implementation
- **Commit `287d7d6`**: Major performance optimizations and JSON recovery system deployment

## Current Error Handling Architecture Strengths

1. **Comprehensive Exception Hierarchy**: Well-structured with actionable guidance
2. **Robust JSON Recovery**: Excellent concatenated JSON handling with multiple fallbacks
3. **Sophisticated Retry Logic**: Exponential backoff for transient failures
4. **Tool Message Patching**: Graceful orphaned tool call handling
5. **State-Aware Processing**: Enum-based state machine prevents invalid transitions
6. **User-Friendly Error Messages**: Enhanced display with suggested fixes

## References

### **Key Implementation Files:**
- `src/tunacode/exceptions.py` - Exception hierarchy definitions
- `src/tunacode/cli/repl.py` - Main REPL global exception handling
- `src/tunacode/utils/retry.py` - JSON retry system
- `src/tunacode/utils/json_utils.py` - JSON concatenation recovery
- `src/tunacode/cli/repl_components/error_recovery.py` - Tool recovery mechanisms
- `src/tunacode/core/agents/main.py` - Agent loop error handling
- `src/tunacode/core/agents/agent_components/state_transition.py` - State machine

### **Documentation Files:**
- `.claude/patterns/json_retry_implementation.md` - JSON recovery system details
- `.claude/development/cli-json-recovery-incident.md` - Historical incident analysis
- `documentation/agent/main-agent-architecture.md` - Architecture documentation

### **Configuration:**
- `src/tunacode/configuration/defaults.py` - Error handling configuration defaults
- JSON_PARSE_MAX_RETRIES = 10
- JSON_PARSE_BASE_DELAY = 0.1s
- JSON_PARSE_MAX_DELAY = 5.0s

### **Test Coverage:**
- `test_json_concatenation_recovery.py` - JSON recovery tests
- `test_json_retry.py` - Retry logic tests
- `test_tool_batching_retry.py` - Tool batching tests
- `test_error_handling.py` - Characterization error handling tests
