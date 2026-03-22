---
title: "tool result adapter runtime research findings"
link: "tool-result-adapter-runtime-research"
type: research
ontological_relations:
  - relates_to: [[docs/modules/tools/tools]]
tags: [research, tools, runtime, adapter]
uuid: "1897731E-0B75-4872-B374-3A1067445EA8"
created_at: "2026-03-22T09:53:07-0500"
---

## Key Files
- `src/tunacode/tools/decorators.py:177-209` → generated tool adapter `execute(tool_call_id, args, signal, on_update) -> AgentToolResult`
- `src/tunacode/core/agents/agent_components/agent_config.py:151-160` → concurrency wrapper forwards `tool_call_id`, `args`, `signal`, and `on_update` to the underlying tool execute function
- `src/tunacode/core/agents/helpers.py:85-96` → runtime extracts only concatenated `TextContent.text` from `AgentToolResult.content`
- `src/tunacode/core/agents/main.py:437-470` → runtime consumes `event_obj.result`, derives `result_text`, updates tool registry, and invokes `tool_result_callback`
- `src/tunacode/types/callbacks.py:62-65` → `ToolResultCallback` payload shape excludes `details`
- `src/tunacode/core/agents/resume/sanitize.py:78-84` → resume model for tool result messages includes `details: dict[str, object]`
- `src/tunacode/core/agents/resume/sanitize.py:194-206` → resume parse path reads `message.get("details", {})`
- `src/tunacode/core/agents/resume/sanitize.py:278-283` → resume serialize path writes `"details": message.details`

## Execute Signature and Forwarding
- `src/tunacode/tools/decorators.py:177-182` defines:
  - `async def execute(tool_call_id: str, args: JsonObject, signal: asyncio.Event | None, on_update: AgentToolUpdateCallback) -> AgentToolResult`
- `src/tunacode/tools/decorators.py:183-184` explicitly assigns:
  - `_ = tool_call_id`
  - `_ = on_update`
- `src/tunacode/core/agents/agent_components/agent_config.py:151-156` defines the concurrency-limited wrapper with the same four parameters
- `src/tunacode/core/agents/agent_components/agent_config.py:157-160` forwards all four parameters unchanged to `typed_execute_fn(tool_call_id, args, signal, on_update)`

## AgentToolResult Creation
- `src/tunacode/tools/decorators.py:200-209` awaits the underlying tool function, checks `isinstance(result, str)`, and returns:
  - `AgentToolResult(content=[TextContent(text=result)], details={})`
- `src/tunacode/tools/decorators.py:163-168` imports `AgentToolResult` and `TextContent`

## Runtime Consumption of Tool Results
- `src/tunacode/core/agents/main.py:446-449` reads:
  - `tool_call_id = event_obj.tool_call_id`
  - `tool_name = event_obj.tool_name`
  - `result_text = extract_tool_result_text(event_obj.result)`
- `src/tunacode/core/agents/helpers.py:85-96` implements `extract_tool_result_text(result: AgentToolResult | None) -> str | None`
- `src/tunacode/core/agents/helpers.py:89-95` iterates only `result.content`, filters `TextContent`, and concatenates `item.text`
- `src/tunacode/core/agents/main.py:452-455` writes only `result_text` into `tool_registry.fail(..., error=result_text)` or `tool_registry.complete(..., result=result_text)`
- `src/tunacode/core/agents/main.py:463-469` passes only `(tool_name, status, callback_args, result_text, duration_ms)` to `tool_result_callback`
- `src/tunacode/types/callbacks.py:63-65` defines `ToolResultCallback` as `Callable[[ToolName, str, ToolArgs, str | None, float | None], None]`
- `src/tunacode/ui/repl_support.py:188-215` consumes the same callback shape and uses only `tool_name`, `status`, `args`, `result`, and `duration_ms`

## Details Propagation
- `src/tunacode/tools/decorators.py:209` constructs every adapter result with `details={}`
- `src/tunacode/core/agents/helpers.py:85-96` does not read `result.details`
- `src/tunacode/core/agents/main.py:437-470` does not read `event_obj.result.details`
- `src/tunacode/types/callbacks.py:63-65` does not include `details` in the runtime callback payload
- `src/tunacode/core/agents/resume/sanitize.py:79-83` defines `ToolResultResumeMessage.details: dict[str, object]`
- `src/tunacode/core/agents/resume/sanitize.py:198-206` parses `details` from persisted tool result messages
- `src/tunacode/core/agents/resume/sanitize.py:278-283` serializes `details` back into persisted tool result messages
- `src/tunacode/core/agents/resume/sanitize.py:303-304` type-check path identifies `ToolResultResumeMessage` during sanitization

## on_update Locations
- `src/tunacode/tools/decorators.py:149` tool adapter docstring states tinyagent expects `execute(tool_call_id, args, signal, on_update)`
- `src/tunacode/tools/decorators.py:181` adapter signature includes `on_update: AgentToolUpdateCallback`
- `src/tunacode/tools/decorators.py:184` adapter body discards `on_update`
- `src/tunacode/core/agents/agent_components/agent_config.py:17` imports `AgentToolUpdateCallback`
- `src/tunacode/core/agents/agent_components/agent_config.py:94-95` includes `AgentToolUpdateCallback` in the `ToolExecute` type alias
- `src/tunacode/core/agents/agent_components/agent_config.py:155` wrapper signature includes `on_update`
- `src/tunacode/core/agents/agent_components/agent_config.py:159` wrapper forwards `on_update` to the underlying execute function
