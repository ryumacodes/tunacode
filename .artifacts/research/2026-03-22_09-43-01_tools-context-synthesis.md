---
title: "tools context synthesis research findings"
link: "tools-context-synthesis-research"
type: research
ontological_relations:
  - relates_to: [[docs/modules/tools/tools]]
  - relates_to: [[docs/modules/core/core]]
  - relates_to: [[docs/modules/configuration/configuration]]
  - relates_to: [[docs/modules/types/types]]
tags: [research, tools, core, configuration, types]
uuid: "612143E1-7FEC-414F-8CB3-1AEF84112E2A"
created_at: "2026-03-22T14:43:01Z"
---

## Structure

- Tool entrypoints live under `src/tunacode/tools/`. The package uses lazy submodule loading in `src/tunacode/tools/__init__.py:1-10`.
- Tool wrappers and the tinyagent adapter live in `src/tunacode/tools/decorators.py:48-219`.
- Core tool registration lives in `src/tunacode/core/agents/agent_components/agent_config.py:181-198` and agent attachment happens in `src/tunacode/core/agents/agent_components/agent_config.py:464-476`.
- Runtime tool-call state lives in `src/tunacode/core/types/state_structures.py:60-72` and `src/tunacode/core/types/tool_registry.py:32-186`.
- Canonical tool-call/message contracts live in `src/tunacode/types/canonical.py:67-174`.
- Tool callback contracts live in `src/tunacode/types/callbacks.py:6-10` and `src/tunacode/types/callbacks.py:57-66`.
- Session-side config coercion for tool execution lives in `src/tunacode/core/agents/agent_components/agent_session_config.py:15-152`.
- Config-backed limits used by tools and agent construction live in `src/tunacode/configuration/limits.py:19-79`.

## Key Files

- `src/tunacode/tools/decorators.py:48-82` → `base_tool` wraps async tools, preserves signature, and replaces docstrings with XML prompt content loaded by `src/tunacode/tools/xml_helper.py:13-46`.
- `src/tunacode/tools/decorators.py:85-134` → `file_tool` adds file-specific exception translation and then delegates to `base_tool`.
- `src/tunacode/tools/decorators.py:137-219` → `to_tinyagent_tool` converts a TunaCode async tool into a tinyagent `AgentTool`, binds JSON args into the Python signature, optionally performs strict validation, requires a `str` return value, and emits `TextContent`.
- `src/tunacode/core/agents/agent_components/agent_config.py:181-193` → `_build_tools` registers `bash`, `discover`, `read_file`, `hashline_edit`, `web_fetch`, and `write_file`.
- `src/tunacode/core/agents/agent_components/agent_config.py:145-178` → all registered `AgentTool` objects are wrapped with a shared semaphore-based concurrency limit.
- `src/tunacode/core/agents/main.py:413-470` → the request loop records tool execution start/end events into `runtime.tool_registry` and invokes callback hooks.
- `src/tunacode/core/types/tool_registry.py:39-115` → `ToolCallRegistry` creates and updates `CanonicalToolCall` records with pending/running/completed/failed/cancelled status.
- `src/tunacode/core/agents/resume/sanitize.py:182-208` and `src/tunacode/core/agents/resume/sanitize.py:297-305` → resume sanitization parses assistant `tool_call` content and `tool_result` messages, then computes dangling tool call IDs.
- `src/tunacode/core/compaction/summarizer.py:274-311` → compaction serializes assistant tool calls and tool results back into summary text.

## Patterns Found

### Tool definition → adapter → agent registration

- Tool functions are defined as async functions and decorated with `@base_tool` or `@file_tool` in:
  - `src/tunacode/tools/bash.py:22-29`
  - `src/tunacode/tools/discover.py:11-15`
  - `src/tunacode/tools/read_file.py:34-39`
  - `src/tunacode/tools/hashline_edit.py:126-135`
  - `src/tunacode/tools/web_fetch.py:229-233`
  - `src/tunacode/tools/write_file.py:12-13`
- `_build_tools` imports those functions directly and passes each through `to_tinyagent_tool` in `src/tunacode/core/agents/agent_components/agent_config.py:181-198`.
- `get_or_create_agent` then calls `agent.set_tools(tools)` in `src/tunacode/core/agents/agent_components/agent_config.py:464-476`.

### Signature-driven schema and validation

- `to_tinyagent_tool` builds the OpenAI-style JSON parameter schema from the Python signature in `src/tunacode/tools/decorators.py:173-175` and `src/tunacode/tools/decorators.py:239-273`.
- Strict argument validation is optional and is driven by `strict_validation` inside the generated `execute` function in `src/tunacode/tools/decorators.py:194-199`.
- Session config exposes `tool_strict_validation` through `AgentSettings` in `src/tunacode/core/agents/agent_components/agent_session_config.py:15-21`, populates it in `src/tunacode/core/agents/agent_components/agent_session_config.py:100-110`, and hashes it into the agent version in `src/tunacode/core/agents/agent_components/agent_session_config.py:136-152`.
- Agent creation passes that setting into `_build_tools(strict_validation=config.settings.tool_strict_validation)` in `src/tunacode/core/agents/agent_components/agent_config.py:433-465`.

### Text-only tool result contract

- `to_tinyagent_tool` rejects non-`str` tool return values and converts successful results into `AgentToolResult(content=[TextContent(text=result)], details={})` in `src/tunacode/tools/decorators.py:200-209`.
- Core result extraction only reads `TextContent` items from `AgentToolResult.content` in `src/tunacode/core/agents/helpers.py:85-96`.
- The orchestrator uses that extracted text for registry completion/failure and for `ToolResultCallback` invocation in `src/tunacode/core/agents/main.py:448-470`.

### Tool lifecycle tracked twice: event stream + canonical registry

- Tinyagent emits `ToolExecutionStartEvent` / `ToolExecutionEndEvent`, and `RequestOrchestrator` handles them in `src/tunacode/core/agents/main.py:413-470`.
- `RuntimeState` owns a `ToolCallRegistry` field in `src/tunacode/core/types/state_structures.py:61-70`.
- `ToolCallRegistry` stores `CanonicalToolCall` records defined in `src/tunacode/types/canonical.py:150-174`, keyed by `ToolCallId`, `ToolName`, and `ToolArgs` aliases from `src/tunacode/types/base.py:12-16` and `src/tunacode/types/base.py:34-36`.
- The registry also exposes recent calls, latest call, and legacy-record serialization in `src/tunacode/core/types/tool_registry.py:128-177`.

### Message/persistence path preserves tool-call identifiers

- Session persistence serializes tinyagent message models directly with `model_dump()` in `src/tunacode/core/session/state.py:170-175`.
- Session load validates role-specific tinyagent message models, including `ToolResultMessage` when `role == "tool_result"`, in `src/tunacode/core/session/state.py:176-220`.
- Resume sanitization parses assistant `tool_call` items with fields `id`, `name`, `arguments`, and `partial_json` in `src/tunacode/core/agents/resume/sanitize.py:128-153`.
- Resume sanitization parses `tool_result` messages with `tool_call_id`, `content`, `details`, and `is_error` in `src/tunacode/core/agents/resume/sanitize.py:194-207`.
- Cleanup removes dangling tool-call IDs from both message content and `ToolCallRegistry` in `src/tunacode/core/agents/resume/sanitize.py:394-411` and `src/tunacode/core/agents/resume/sanitize.py:442-483`.

### Tool-call history reused for retry/summary UX

- `get_recent_tools_context` formats recent `CanonicalToolCall` records into retry context in `src/tunacode/core/agents/agent_components/agent_helpers.py:56-67`.
- `handle_empty_response` reads those recent calls from `state.sm.session.runtime.tool_registry.recent_calls(...)` in `src/tunacode/core/agents/agent_components/agent_helpers.py:100-108`.
- Compaction serializes assistant `ToolCallContent` and `ToolResultMessage` records into summary lines in `src/tunacode/core/compaction/summarizer.py:274-311`.

### File-read/file-edit shared cache contract

- `read_file` documents that it populates cache state for `hashline_edit` in `src/tunacode/tools/read_file.py:50-55`.
- `read_file` stores hashed lines in `src/tunacode/tools/line_cache.py` via `_cache_store(filepath, hashed)` in `src/tunacode/tools/read_file.py:122-131`.
- `hashline_edit` validates `line:hash` references against that cache in `src/tunacode/tools/hashline_edit.py:56-87`.
- Cache mutation after edits uses `update_lines` / `replace_range` in `src/tunacode/tools/hashline_edit.py:214-215`, `src/tunacode/tools/hashline_edit.py:251-252`, and `src/tunacode/tools/hashline_edit.py:279-285`, implemented by `src/tunacode/tools/line_cache.py:52-127`.

### Config-backed tool behavior

- `bash` truncates formatted output using `get_command_limit()` from `src/tunacode/configuration/limits.py:59-63`, imported in `src/tunacode/tools/bash.py:8` and applied in `src/tunacode/tools/bash.py:147-154`.
- `write_file` and `hashline_edit` prepend LSP diagnostics through `maybe_prepend_lsp_diagnostics(...)` in `src/tunacode/tools/write_file.py:38-39` and `src/tunacode/tools/hashline_edit.py:190-193`.
- LSP diagnostics read `settings.lsp` from user config through `load_config()` in `src/tunacode/tools/lsp/diagnostics.py:9`, `src/tunacode/tools/lsp/diagnostics.py:17-25`, `src/tunacode/tools/lsp/diagnostics.py:28-43`.
- Agent creation reads response-token overrides from `get_max_tokens()` in `src/tunacode/core/agents/agent_components/agent_config.py:27` and `src/tunacode/core/agents/agent_components/agent_config.py:437`.
- `get_max_tokens()` reads `settings.max_tokens` from config in `src/tunacode/configuration/limits.py:71-79`.
- Session state initializes `conversation.max_tokens` from model registry context-window data with `get_model_context_window(...)` in `src/tunacode/core/session/state.py:83-101`; compaction uses `session.conversation.max_tokens` in `src/tunacode/core/agents/main.py:220-223` and `src/tunacode/core/agents/agent_components/agent_config.py:342-350`.

### Tool-name sets in configuration vs runtime registration

- `ToolName` enum includes `READ_FILE`, `WRITE_FILE`, `HASHLINE_EDIT`, `BASH`, `GREP`, `LIST_DIR`, `GLOB`, and `WEB_FETCH` in `src/tunacode/constants.py:57-68`.
- `ApplicationSettings.internal_tools` lists `BASH`, `GLOB`, `GREP`, `LIST_DIR`, `READ_FILE`, `HASHLINE_EDIT`, and `WRITE_FILE` in `src/tunacode/configuration/settings.py:20-33`.
- `_build_tools` registers `bash`, `discover`, `read_file`, `hashline_edit`, `web_fetch`, and `write_file` in `src/tunacode/core/agents/agent_components/agent_config.py:181-193`.

## Dependencies

- `src/tunacode/tools/decorators.py` imports:
  - `tunacode.exceptions` in `src/tunacode/tools/decorators.py:32-37`
  - `tunacode.tools.xml_helper` in `src/tunacode/tools/decorators.py:39`
- `src/tunacode/tools/xml_helper.py` imports the tool-cache accessor boundary in `src/tunacode/tools/xml_helper.py:10`, which delegates to infrastructure cache registration in `src/tunacode/tools/cache_accessors/xml_prompts_cache.py:5-16`.
- `src/tunacode/core/agents/agent_components/agent_config.py` imports:
  - configuration limits/models in `src/tunacode/core/agents/agent_components/agent_config.py:27-34`
  - tool entrypoints in `src/tunacode/core/agents/agent_components/agent_config.py:38-44`
  - state protocols in `src/tunacode/core/agents/agent_components/agent_config.py:51`
  - session config coercion in `src/tunacode/core/agents/agent_components/agent_config.py:61-70`
- `src/tunacode/core/types/tool_registry.py` imports base aliases and canonical tool-call types in `src/tunacode/core/types/tool_registry.py:10-11`.
- `src/tunacode/core/agents/main.py` imports tool callback contracts from `src/tunacode/types/callbacks.py` via `tunacode.types` in `src/tunacode/core/agents/main.py:40-47`, stream-state helpers in `src/tunacode/core/agents/helpers.py:63-72`, and state protocols in `src/tunacode/core/agents/main.py:58-60`.
- `src/tunacode/core/ui_api/shared_types.py:5-16` re-exports `ToolArgs`, `ToolName`, `ToolResultCallback`, and `ToolStartCallback` from `tunacode.types` for UI-facing imports.

## Symbol Index

- `src/tunacode/tools/decorators.py:48` → `base_tool`
- `src/tunacode/tools/decorators.py:85` → `file_tool`
- `src/tunacode/tools/decorators.py:137` → `to_tinyagent_tool`
- `src/tunacode/core/agents/agent_components/agent_config.py:181` → `_build_tools`
- `src/tunacode/core/agents/agent_components/agent_config.py:428` → `get_or_create_agent`
- `src/tunacode/core/agents/main.py:117` → `RequestOrchestrator`
- `src/tunacode/core/types/tool_registry.py:33` → `ToolCallRegistry`
- `src/tunacode/types/canonical.py:68` → `ToolCallPart`
- `src/tunacode/types/canonical.py:78` → `ToolReturnPart`
- `src/tunacode/types/canonical.py:140` → `ToolCallStatus`
- `src/tunacode/types/canonical.py:151` → `CanonicalToolCall`
- `src/tunacode/types/callbacks.py:27` → `ToolCallPartProtocol`
- `src/tunacode/types/callbacks.py:63` → `ToolResultCallback`
