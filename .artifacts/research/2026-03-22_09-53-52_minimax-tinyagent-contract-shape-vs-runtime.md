---
title: "MiniMax tinyagent contract shape vs tunacode runtime research findings"
link: "minimax-tinyagent-contract-shape-vs-runtime-research"
type: research
ontological_relations:
  - relates_to: [[docs/modules/core/core]]
  - relates_to: [[docs/modules/tools/tools]]
  - relates_to: [[docs/modules/utils/utils]]
  - relates_to: [[docs/modules/configuration/models-registry]]
tags: [research, minimax, tinyagent, tools, runtime]
uuid: "8BDB4B54-9C98-4A63-920A-ED18F7B0400D"
created_at: "2026-03-22T14:53:52Z"
---

## Structure

- External reference used for the MiniMax tool-calling contract shape: [`/Users/tuna/Desktop/tinyAgent/docs/api/minimax-single-tool-example.md`](/Users/tuna/Desktop/tinyAgent/docs/api/minimax-single-tool-example.md#L57).
- TinyAgent type definitions used by that example live in [`/Users/tuna/Desktop/tinyAgent/tinyagent/agent_types.py`](/Users/tuna/Desktop/tinyAgent/tinyagent/agent_types.py#L187) and tool execution/event emission lives in [`/Users/tuna/Desktop/tinyAgent/tinyagent/agent_tool_execution.py`](/Users/tuna/Desktop/tinyAgent/tinyagent/agent_tool_execution.py#L82).
- TunaCode’s tool adapter is in [`src/tunacode/tools/decorators.py`](/Users/tuna/Desktop/tunacode/src/tunacode/tools/decorators.py#L137).
- TunaCode’s stream event orchestration is in [`src/tunacode/core/agents/main.py`](/Users/tuna/Desktop/tunacode/src/tunacode/core/agents/main.py#L376).
- TunaCode’s message canonicalization boundary is in [`src/tunacode/utils/messaging/adapter.py`](/Users/tuna/Desktop/tunacode/src/tunacode/utils/messaging/adapter.py#L188).
- TunaCode’s result-to-UI callback path is in [`src/tunacode/types/callbacks.py`](/Users/tuna/Desktop/tunacode/src/tunacode/types/callbacks.py#L63), [`src/tunacode/ui/repl_support.py`](/Users/tuna/Desktop/tunacode/src/tunacode/ui/repl_support.py#L187), and [`src/tunacode/ui/widgets/messages.py`](/Users/tuna/Desktop/tunacode/src/tunacode/ui/widgets/messages.py#L30).

## Key Files

- External MiniMax example returns `AgentToolResult(content=[TextContent(...)], details={...})` from the tool function in [`minimax-single-tool-example.md`](/Users/tuna/Desktop/tinyAgent/docs/api/minimax-single-tool-example.md#L57).
- External MiniMax example documents assistant stream events including `tool_call_start`, `tool_call_delta`, `tool_call_end`, `text_start`, `text_delta`, `text_end`, `done` in [`minimax-single-tool-example.md`](/Users/tuna/Desktop/tinyAgent/docs/api/minimax-single-tool-example.md#L179).
- External MiniMax example documents agent events including `message_start`, `message_update`, `message_end`, `tool_execution_start`, `tool_execution_end`, `turn_end`, `agent_end` in [`minimax-single-tool-example.md`](/Users/tuna/Desktop/tinyAgent/docs/api/minimax-single-tool-example.md#L189).
- TinyAgent defines `ToolResultMessage` with `tool_call_id`, `tool_name`, `content`, `details`, and `is_error` in [`agent_types.py`](/Users/tuna/Desktop/tinyAgent/tinyagent/agent_types.py#L187).
- TinyAgent defines `AgentToolResult` as `content + details` and defines `AgentToolUpdateCallback` in [`agent_types.py`](/Users/tuna/Desktop/tinyAgent/tinyagent/agent_types.py#L226).
- TinyAgent defines `ToolExecutionUpdateEvent` carrying `partial_result` in [`agent_types.py`](/Users/tuna/Desktop/tinyAgent/tinyagent/agent_types.py#L409).
- TinyAgent tool execution emits `ToolExecutionStartEvent`, `ToolExecutionUpdateEvent`, `ToolExecutionEndEvent`, `MessageStartEvent`, and `MessageEndEvent` in [`agent_tool_execution.py`](/Users/tuna/Desktop/tinyAgent/tinyagent/agent_tool_execution.py#L116) and [`agent_tool_execution.py`](/Users/tuna/Desktop/tinyAgent/tinyagent/agent_tool_execution.py#L175).
- TunaCode’s adapter ignores `on_update`, requires the wrapped tool to return `str`, and always constructs `AgentToolResult(content=[TextContent(text=result)], details={})` in [`decorators.py`](/Users/tuna/Desktop/tunacode/src/tunacode/tools/decorators.py#L177).
- TunaCode extracts tool results by concatenating only `TextContent` items in [`helpers.py`](/Users/tuna/Desktop/tunacode/src/tunacode/core/agents/helpers.py#L85).
- TunaCode’s event dispatcher handles `MessageUpdateEvent`, `MessageEndEvent`, `ToolExecutionStartEvent`, `ToolExecutionEndEvent`, `TurnEndEvent`, and `AgentEndEvent` in [`main.py`](/Users/tuna/Desktop/tunacode/src/tunacode/core/agents/main.py#L485).
- TunaCode’s message adapter reduces tool-result messages to `ToolReturnPart(tool_call_id, content)` in [`adapter.py`](/Users/tuna/Desktop/tunacode/src/tunacode/utils/messaging/adapter.py#L188) and reconstructs tool messages with `details={}` and `is_error=False` in [`adapter.py`](/Users/tuna/Desktop/tunacode/src/tunacode/utils/messaging/adapter.py#L294).

## Patterns Found

### Shared MiniMax provider path

- The external MiniMax example sets `OpenAICompatModel(provider="minimax", api="minimax-completions", base_url="https://api.minimax.io/v1/chat/completions")` in [`minimax-single-tool-example.md`](/Users/tuna/Desktop/tinyAgent/docs/api/minimax-single-tool-example.md#L86).
- TunaCode builds `OpenAICompatModel` in [`agent_config.py`](/Users/tuna/Desktop/tunacode/src/tunacode/core/agents/agent_components/agent_config.py#L355) and its MiniMax integration test asserts `api == "minimax-completions"` and `base_url == "https://api.minimax.io/v1/chat/completions"` in [`test_minimax_execution_path.py`](/Users/tuna/Desktop/tunacode/tests/integration/core/test_minimax_execution_path.py#L20) and [`test_minimax_execution_path.py`](/Users/tuna/Desktop/tunacode/tests/integration/core/test_minimax_execution_path.py#L87).

### `content` / `details` shape mismatch

- The external MiniMax example returns non-empty `details` with structured `input` and `output` keys in [`minimax-single-tool-example.md`](/Users/tuna/Desktop/tinyAgent/docs/api/minimax-single-tool-example.md#L66) and shows the same structure again in the documented typical tool result details in [`minimax-single-tool-example.md`](/Users/tuna/Desktop/tinyAgent/docs/api/minimax-single-tool-example.md#L165).
- TinyAgent’s own contract allows this: `AgentToolResult` has both `content` and `details` in [`agent_types.py`](/Users/tuna/Desktop/tinyAgent/tinyagent/agent_types.py#L226), and `ToolResultMessage` also stores `details` in [`agent_types.py`](/Users/tuna/Desktop/tinyAgent/tinyagent/agent_types.py#L187).
- TunaCode’s adapter always returns `details={}` and never forwards tool-specific structured details in [`decorators.py`](/Users/tuna/Desktop/tunacode/src/tunacode/tools/decorators.py#L209).
- TunaCode’s result callback contract has no `details` field; it accepts `(tool_name, status, args, result, duration_ms)` in [`callbacks.py`](/Users/tuna/Desktop/tunacode/src/tunacode/types/callbacks.py#L63).
- TunaCode’s UI transport `ToolResultDisplay` stores only `tool_name`, `status`, `args`, `result`, and `duration_ms` in [`messages.py`](/Users/tuna/Desktop/tunacode/src/tunacode/ui/widgets/messages.py#L30).
- TunaCode’s canonical message adapter drops tool-result `details` entirely when converting to canonical form in [`adapter.py`](/Users/tuna/Desktop/tunacode/src/tunacode/utils/messaging/adapter.py#L188), and when converting back from canonical it reconstructs tool results with `details={}` in [`adapter.py`](/Users/tuna/Desktop/tunacode/src/tunacode/utils/messaging/adapter.py#L303).

### Tool result content shape mismatch

- TinyAgent’s contract allows `AgentToolResult.content` to contain `TextContent | ImageContent` in [`agent_types.py`](/Users/tuna/Desktop/tinyAgent/tinyagent/agent_types.py#L226), and `ToolResultMessage.content` also allows `TextContent | ImageContent` in [`agent_types.py`](/Users/tuna/Desktop/tinyAgent/tinyagent/agent_types.py#L193).
- TunaCode’s adapter requires the wrapped tool function to return `str`; non-string return values raise `ToolExecutionError` in [`decorators.py`](/Users/tuna/Desktop/tunacode/src/tunacode/tools/decorators.py#L200).
- TunaCode wraps successful tool output as exactly one `TextContent` item in [`decorators.py`](/Users/tuna/Desktop/tunacode/src/tunacode/tools/decorators.py#L209).
- TunaCode’s adapter tests assert a single `TextContent` item in [`test_tinyagent_tool_adapter.py`](/Users/tuna/Desktop/tunacode/tests/unit/tools/test_tinyagent_tool_adapter.py#L21).
- TunaCode’s tool-result extraction only reads `TextContent` items from `AgentToolResult.content` in [`helpers.py`](/Users/tuna/Desktop/tunacode/src/tunacode/core/agents/helpers.py#L85). No repo path reads `event_obj.result.details` during normal request orchestration.

### Streaming update mismatch

- The external MiniMax example tool signature includes `on_update: Callable[[AgentToolResult], None]` in [`minimax-single-tool-example.md`](/Users/tuna/Desktop/tinyAgent/docs/api/minimax-single-tool-example.md#L57).
- TinyAgent emits `ToolExecutionUpdateEvent(partial_result=partial_result)` whenever the tool calls `on_update(...)` in [`agent_tool_execution.py`](/Users/tuna/Desktop/tinyAgent/tinyagent/agent_tool_execution.py#L116), and the event type is defined in [`agent_types.py`](/Users/tuna/Desktop/tinyAgent/tinyagent/agent_types.py#L409).
- TunaCode’s generated `execute(...)` signature includes `on_update`, but the implementation discards it with `_ = on_update` in [`decorators.py`](/Users/tuna/Desktop/tunacode/src/tunacode/tools/decorators.py#L177) and [`decorators.py`](/Users/tuna/Desktop/tunacode/src/tunacode/tools/decorators.py#L184).
- TunaCode’s stream dispatcher does not branch on `ToolExecutionUpdateEvent`; it handles start/end tool events only in [`main.py`](/Users/tuna/Desktop/tunacode/src/tunacode/core/agents/main.py#L516) and [`main.py`](/Users/tuna/Desktop/tunacode/src/tunacode/core/agents/main.py#L523).
- TunaCode’s message update handling only forwards assistant `text_delta` and `thinking_delta` in [`main.py`](/Users/tuna/Desktop/tunacode/src/tunacode/core/agents/main.py#L579).
- TunaCode’s message-update tests show `AssistantMessageEvent(type="done", delta="ignored")` is ignored in [`test_thinking_stream_routing.py`](/Users/tuna/Desktop/tunacode/tests/unit/core/test_thinking_stream_routing.py#L84).

### Event capture mismatch

- The external MiniMax example’s documented agent event sequence includes `message_start`, `message_update`, `message_end`, `tool_execution_start`, `tool_execution_end`, `turn_end`, and `agent_end` in [`minimax-single-tool-example.md`](/Users/tuna/Desktop/tinyAgent/docs/api/minimax-single-tool-example.md#L189).
- TinyAgent’s tool execution implementation emits `MessageStartEvent(message=tool_result_message)` and `MessageEndEvent(message=tool_result_message)` after each tool result in [`agent_tool_execution.py`](/Users/tuna/Desktop/tinyAgent/tinyagent/agent_tool_execution.py#L206).
- TunaCode’s integration contract test also asserts that tool execution emits `ToolExecutionStartEvent`, `ToolExecutionEndEvent`, `MessageStartEvent`, and `MessageEndEvent` in [`test_tinyagent_tool_execution_contract.py`](/Users/tuna/Desktop/tunacode/tests/integration/core/test_tinyagent_tool_execution_contract.py#L67).
- TunaCode’s request-loop dispatcher does not process `MessageStartEvent`; there is no `MessageStartEvent` import or handler in [`main.py`](/Users/tuna/Desktop/tunacode/src/tunacode/core/agents/main.py#L11) and [`main.py`](/Users/tuna/Desktop/tunacode/src/tunacode/core/agents/main.py#L485).
- TunaCode’s dispatcher also does not process `ToolExecutionUpdateEvent`; only start and end tool events are matched in [`main.py`](/Users/tuna/Desktop/tunacode/src/tunacode/core/agents/main.py#L516) and [`main.py`](/Users/tuna/Desktop/tunacode/src/tunacode/core/agents/main.py#L523).
- TunaCode’s `MessageUpdateEvent` handler reads only `assistant_message_event.delta` for assistant text/thinking streaming in [`main.py`](/Users/tuna/Desktop/tunacode/src/tunacode/core/agents/main.py#L580), not `event.message`.

### Result extraction mismatch

- The external MiniMax example contract shape centers the tool return on the full `AgentToolResult`, including `content` and structured `details`, in [`minimax-single-tool-example.md`](/Users/tuna/Desktop/tinyAgent/docs/api/minimax-single-tool-example.md#L66).
- TunaCode’s runtime extracts a plain text summary from `AgentToolResult` using `extract_tool_result_text(...)` in [`helpers.py`](/Users/tuna/Desktop/tunacode/src/tunacode/core/agents/helpers.py#L85), and stores only that text into `ToolCallRegistry.complete(..., result=result_text)` or `.fail(..., error=result_text)` in [`main.py`](/Users/tuna/Desktop/tunacode/src/tunacode/core/agents/main.py#L452).
- `ToolCallRegistry` persists only `result: str | None` and `error: str | None` on `CanonicalToolCall` in [`canonical.py`](/Users/tuna/Desktop/tunacode/src/tunacode/types/canonical.py#L151) and [`tool_registry.py`](/Users/tuna/Desktop/tunacode/src/tunacode/core/types/tool_registry.py#L72).
- TunaCode’s canonical `ToolReturnPart` has only `tool_call_id` and `content` in [`canonical.py`](/Users/tuna/Desktop/tunacode/src/tunacode/types/canonical.py#L77).
- The generic message adapter maps tool results to `ToolReturnPart(tool_call_id, content_text)` in [`adapter.py`](/Users/tuna/Desktop/tunacode/src/tunacode/utils/messaging/adapter.py#L188), which removes `tool_name`, `details`, and `is_error` from the canonical representation.
- Converting canonical tool messages back to tinyagent form recreates `details={}` and `is_error=False` in [`adapter.py`](/Users/tuna/Desktop/tunacode/src/tunacode/utils/messaging/adapter.py#L303).

### Tool-result metadata preservation differs by path

- TinyAgent `ToolResultMessage` includes `tool_name`, `details`, and `is_error` in [`agent_types.py`](/Users/tuna/Desktop/tinyAgent/tinyagent/agent_types.py#L187).
- TunaCode session persistence keeps raw tinyagent message models via `model_dump(exclude_none=True)` in [`state.py`](/Users/tuna/Desktop/tunacode/src/tunacode/core/session/state.py#L170), and load-time validation accepts `ToolResultMessage` when `role == "tool_result"` in [`state.py`](/Users/tuna/Desktop/tunacode/src/tunacode/core/session/state.py#L176).
- TunaCode resume sanitization also preserves `details` and `is_error` on its resume-side `ToolResultResumeMessage` in [`sanitize.py`](/Users/tuna/Desktop/tunacode/src/tunacode/core/agents/resume/sanitize.py#L78) and parses them in [`sanitize.py`](/Users/tuna/Desktop/tunacode/src/tunacode/core/agents/resume/sanitize.py#L194).
- The separate generic canonical adapter path still collapses tool results to text-only `ToolReturnPart` in [`adapter.py`](/Users/tuna/Desktop/tunacode/src/tunacode/utils/messaging/adapter.py#L193).

## Dependencies

- External MiniMax example → TinyAgent contract:
  - [`minimax-single-tool-example.md`](/Users/tuna/Desktop/tinyAgent/docs/api/minimax-single-tool-example.md#L46) imports `Agent`, `AgentOptions`, `AgentTool`, `AgentToolResult`, `TextContent`, `OpenAICompatModel`, and `stream_alchemy_openai_completions`.
- TunaCode tool adapter → TinyAgent contract:
  - [`decorators.py`](/Users/tuna/Desktop/tunacode/src/tunacode/tools/decorators.py#L163) imports `AgentTool`, `AgentToolResult`, `AgentToolUpdateCallback`, and `TextContent`.
- TunaCode stream loop → TinyAgent event contract:
  - [`main.py`](/Users/tuna/Desktop/tunacode/src/tunacode/core/agents/main.py#L10) imports `AgentEndEvent`, `MessageEndEvent`, `MessageUpdateEvent`, `ToolExecutionEndEvent`, `ToolExecutionStartEvent`, and event-type guards.
- TunaCode message canonicalization → internal canonical types:
  - [`adapter.py`](/Users/tuna/Desktop/tunacode/src/tunacode/utils/messaging/adapter.py#L25) imports `CanonicalMessage`, `ToolCallPart`, and `ToolReturnPart`.

## Symbol Index

- External:
  - [`minimax-single-tool-example.md`](/Users/tuna/Desktop/tinyAgent/docs/api/minimax-single-tool-example.md#L57) → `add_numbers`
  - [`agent_types.py`](/Users/tuna/Desktop/tinyAgent/tinyagent/agent_types.py#L187) → `ToolResultMessage`
  - [`agent_types.py`](/Users/tuna/Desktop/tinyAgent/tinyagent/agent_types.py#L226) → `AgentToolResult`
  - [`agent_types.py`](/Users/tuna/Desktop/tinyAgent/tinyagent/agent_types.py#L409) → `ToolExecutionUpdateEvent`
  - [`agent_tool_execution.py`](/Users/tuna/Desktop/tinyAgent/tinyagent/agent_tool_execution.py#L164) → `execute_tool_calls`
- TunaCode:
  - [`decorators.py`](/Users/tuna/Desktop/tunacode/src/tunacode/tools/decorators.py#L137) → `to_tinyagent_tool`
  - [`helpers.py`](/Users/tuna/Desktop/tunacode/src/tunacode/core/agents/helpers.py#L85) → `extract_tool_result_text`
  - [`main.py`](/Users/tuna/Desktop/tunacode/src/tunacode/core/agents/main.py#L117) → `RequestOrchestrator`
  - [`adapter.py`](/Users/tuna/Desktop/tunacode/src/tunacode/utils/messaging/adapter.py#L263) → `to_canonical`
  - [`adapter.py`](/Users/tuna/Desktop/tunacode/src/tunacode/utils/messaging/adapter.py#L373) → `from_canonical`
