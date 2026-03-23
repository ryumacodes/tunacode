# User Query Data Flow

**Date:** 2026-03-22
**Topic:** Data when a user enters a query

## Data Flow: User Query Entry

When a user enters a query, here's what happens to the data:

### 1. Raw Input (`str`)

User types in the editor and hits Enter. The raw text comes in as `EditorSubmitRequested.text`.

### 2. Normalization (`normalize_agent_message_text()`)

At `src/tunacode/ui/repl_support.py:119`, the text is normalized - resolving `@path` mentions against the current working directory.

### 3. Queued (`request_queue.put()`)

The normalized string is put on a request queue at `src/tunacode/ui/app.py:336`.

### 4. Core Entry Point (`process_request()`)

At `src/tunacode/core/agents/main.py:667`, the function signature is:

```python
process_request(message: str, ...)
```

### 5. Tinyagent Handoff (`agent.stream()`)

The string is passed to tinyagent's `Agent.stream(input_data: str | AgentMessage | list[AgentMessage])`.

### 6. First Structured Message (`UserMessage`)

Inside tinyagent at `Agent._build_input_messages()`, the string becomes:

```python
UserMessage(content=[TextContent(text=input_data)])
```

### 7. Runtime Message Types (from tinyagent)

- `UserMessage` - user input
- `AssistantMessage` - model responses
- `ToolResultMessage` - tool execution results
- `CustomAgentMessage` - custom messages

### 8. Session Persistence (stored as `list[dict]`)

Messages are serialized to JSON dicts via `model_dump(exclude_none=True)` and saved to disk.

### 9. Canonical Types (internal abstraction)

TunaCode projects messages into canonical types defined in `src/tunacode/types/canonical.py`:

| Type | Purpose |
|------|---------|
| `CanonicalMessage` | Message with `role: MessageRole` and `parts: tuple[CanonicalPart]` |
| `TextPart` | Plain text content |
| `ToolCallPart` | Tool invocation (`tool_name`, `args`, `tool_call_id`) |
| `ToolReturnPart` | Tool result wrapped in `CanonicalToolResult` |
| `CanonicalToolResult` | Structured result with `content`, `details`, `is_error` |

## Data Flow Diagram

```
User Input (str)
  │
  ▼
normalize_agent_message_text() → resolved str
  │
  ▼
process_request(message: str, ...)
  │
  ▼
agent.stream(input_data: str) → UserMessage(content=[TextContent(...)])
  │
  ▼
agent.state.messages ↔ session.conversation.messages
  │
  ▼
Serialized: list[dict[str, Any]] → disk
```

## Key Files

| File | Function |
|------|----------|
| `src/tunacode/ui/app.py:330` | `on_editor_submit_requested()` - entry point |
| `src/tunacode/ui/repl_support.py:119` | `normalize_agent_message_text()` - path resolution |
| `src/tunacode/ui/app.py:336` | `request_queue.put()` - queue for processing |
| `src/tunacode/ui/app.py:255` | `_process_request()` - UI to core bridge |
| `src/tunacode/core/agents/main.py:667` | `process_request()` - public core entry point |
| `src/tunacode/core/agents/main.py:162` | `RequestOrchestrator._run_impl()` - orchestration |
| `src/tunacode/types/canonical.py` | Canonical message type definitions |
| `src/tunacode/core/session/state.py:319` | `save_session()` - persistence |
| `tinyagent/agent.py:400` | `Agent._build_input_messages()` - first structured message |
| `tinyagent/agent.py:462` | `Agent.stream()` - tinyagent handoff |
