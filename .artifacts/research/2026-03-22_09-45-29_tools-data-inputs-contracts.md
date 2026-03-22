---
title: "tools data inputs and contracts research findings"
link: "tools-data-inputs-contracts-research"
type: research
ontological_relations:
  - relates_to: [[docs/modules/tools/tools.md]]
  - relates_to: [[docs/modules/core/core.md]]
  - relates_to: [[docs/modules/types/types.md]]
tags: [research, tools, contracts, data-inputs]
uuid: "9A81DB61-692E-4BDF-A118-34D68738C54C"
created_at: "2026-03-22T09:45:29-05:00"
---

## Structure

- `src/tunacode/tools/` is the tools package; `src/tunacode/tools/__init__.py:1` lazy-loads submodules and `src/tunacode/tools/__init__.py:7` resolves names through `importlib.import_module`.
- The architecture map places `tools` between `core` and `configuration`/`infrastructure`/`utils` in `docs/modules/index.md:19`.
- Agent assembly imports concrete tool functions in `src/tunacode/core/agents/agent_components/agent_config.py:38`-`src/tunacode/core/agents/agent_components/agent_config.py:44`.
- The runtime tool list is built in `src/tunacode/core/agents/agent_components/agent_config.py:181`-`src/tunacode/core/agents/agent_components/agent_config.py:193` and attached to the tinyagent instance in `src/tunacode/core/agents/agent_components/agent_config.py:476`.
- Tool lifecycle is tracked in `src/tunacode/core/agents/main.py:413`-`src/tunacode/core/agents/main.py:470`.
- Runtime tool state lives on `RuntimeState.tool_registry` in `src/tunacode/core/types/state_structures.py:61`-`src/tunacode/core/types/state_structures.py:73`.
- Tool-related type aliases and canonical records live in `src/tunacode/types/base.py:12`-`src/tunacode/types/base.py:36`, `src/tunacode/types/callbacks.py:57`-`src/tunacode/types/callbacks.py:77`, and `src/tunacode/types/canonical.py:68`-`src/tunacode/types/canonical.py:176`.

## Live Tool Surface

- `_build_tools()` registers six model-exposed tools in this order: `bash`, `discover`, `read_file`, `hashline_edit`, `web_fetch`, `write_file` at `src/tunacode/core/agents/agent_components/agent_config.py:181`-`src/tunacode/core/agents/agent_components/agent_config.py:189`.
- The tool callables are:
  - `src/tunacode/tools/bash.py:23` → `bash(command: str, cwd: str | None = None, env: dict[str, str] | None = None, timeout: int | None = 120, capture_output: bool = True) -> str`
  - `src/tunacode/tools/discover.py:12` → `discover(query: str, directory: str = ".") -> str`
  - `src/tunacode/tools/read_file.py:35` → `read_file(filepath: str, offset: int = 0, limit: int | None = None) -> str`
  - `src/tunacode/tools/hashline_edit.py:127` → `hashline_edit(filepath: str, operation: Literal["replace", "replace_range", "insert_after"], line: str | None = None, start: str | None = None, end: str | None = None, after: str | None = None, new: str = "") -> str`
  - `src/tunacode/tools/web_fetch.py:230` → `web_fetch(url: str, timeout: int = 60) -> str`
  - `src/tunacode/tools/write_file.py:13` → `write_file(filepath: str, content: str) -> str`
- XML prompt files exist for those six tools at:
  - `src/tunacode/tools/prompts/bash_prompt.xml:1`
  - `src/tunacode/tools/prompts/discover_prompt.xml:1`
  - `src/tunacode/tools/prompts/read_file_prompt.xml:1`
  - `src/tunacode/tools/prompts/hashline_edit_prompt.xml:1`
  - `src/tunacode/tools/prompts/web_fetch_prompt.xml:1`
  - `src/tunacode/tools/prompts/write_file_prompt.xml:1`
- `README.md:140`-`README.md:149` and `docs/modules/tools/tools.md:23`-`docs/modules/tools/tools.md:31` document `update_file`, `glob`, `grep`, and `list_dir`; no matching source files were present under `src/tunacode/tools/` in the workspace scan run with `rg --files src/tunacode/tools`.

## Tool Inputs And Outputs

- `bash`
  - Input validation is in `src/tunacode/tools/bash.py:91`-`src/tunacode/tools/bash.py:106`.
  - It executes with `asyncio.create_subprocess_shell(...)` at `src/tunacode/tools/bash.py:54`-`src/tunacode/tools/bash.py:60`.
  - Output is always a formatted text block built by `_format_output()` in `src/tunacode/tools/bash.py:131`-`src/tunacode/tools/bash.py:156`.
  - Output truncation uses `get_command_limit()` from `src/tunacode/configuration/limits.py:59` via `src/tunacode/tools/bash.py:147`.

- `discover`
  - It takes a natural-language `query` plus a `directory` root at `src/tunacode/tools/discover.py:12`-`src/tunacode/tools/discover.py:15`.
  - It offloads to `_discover_sync(query, project_root)` in `src/tunacode/tools/utils/discover_pipeline.py:413`.
  - `_discover_sync()` resolves the root, loads ignore rules, extracts terms, generates patterns, collects candidates, scores prospects, clusters them, and returns `DiscoveryReport(...)` in `src/tunacode/tools/utils/discover_pipeline.py:415`-`src/tunacode/tools/utils/discover_pipeline.py:447`.
  - `DiscoveryReport.to_context()` serializes the report into the string returned to the model in `src/tunacode/tools/utils/discover_types.py:55`-`src/tunacode/tools/utils/discover_types.py:92`.
  - Data classes for discover output are `Relevance`, `FileEntry`, `ConceptCluster`, and `DiscoveryReport` in `src/tunacode/tools/utils/discover_types.py:16`-`src/tunacode/tools/utils/discover_types.py:53`.

- `read_file`
  - Inputs are `filepath`, `offset`, and `limit` at `src/tunacode/tools/read_file.py:35`-`src/tunacode/tools/read_file.py:39`.
  - Files larger than 100KB raise `ToolExecutionError` in `src/tunacode/tools/read_file.py:57`-`src/tunacode/tools/read_file.py:61`.
  - `_read_sync()` reads from `offset`, applies line truncation, computes hashes from original line content, and formats output between `<file>` and `</file>` tags in `src/tunacode/tools/read_file.py:66`-`src/tunacode/tools/read_file.py:120`.
  - Returned hashlines use `HashedLine`, `content_hash()`, and `format_hashline()` from `src/tunacode/tools/hashline.py:19`-`src/tunacode/tools/hashline.py:64`.
  - Returned windows are cached through `_cache_store(filepath, hashed)` at `src/tunacode/tools/read_file.py:130`-`src/tunacode/tools/read_file.py:131`.

- `hashline_edit`
  - Inputs are `filepath`, `operation`, and one of `line`/`start`+`end`/`after`, plus `new`, at `src/tunacode/tools/hashline_edit.py:127`-`src/tunacode/tools/hashline_edit.py:135`.
  - Valid operations are the `Literal` values at `src/tunacode/tools/hashline_edit.py:129`.
  - Reference parsing and cache validation happen in `_validate_ref()` at `src/tunacode/tools/hashline_edit.py:56`-`src/tunacode/tools/hashline_edit.py:87`.
  - Operation handlers are `_apply_replace()` at `src/tunacode/tools/hashline_edit.py:196`, `_apply_replace_range()` at `src/tunacode/tools/hashline_edit.py:220`, and `_apply_insert_after()` at `src/tunacode/tools/hashline_edit.py:261`.
  - The tool reads full file lines, writes the modified file, mutates the line cache, generates a unified diff, and prepends LSP diagnostics at `src/tunacode/tools/hashline_edit.py:168`-`src/tunacode/tools/hashline_edit.py:193`.
  - Cache update helpers are `update_lines()` and `replace_range()` in `src/tunacode/tools/line_cache.py:52`-`src/tunacode/tools/line_cache.py:127`.

- `web_fetch`
  - Inputs are `url` and `timeout` at `src/tunacode/tools/web_fetch.py:230`-`src/tunacode/tools/web_fetch.py:233`.
  - `_validate_url()` accepts only `http`/`https`, rejects empty URLs, blocks localhost hostnames, and blocks private/reserved IPs at `src/tunacode/tools/web_fetch.py:71`-`src/tunacode/tools/web_fetch.py:115`.
  - `_fetch_and_process()` does a HEAD size check, GET request, redirect validation, byte-size limit check, decoding, optional HTML-to-text conversion, and output truncation at `src/tunacode/tools/web_fetch.py:190`-`src/tunacode/tools/web_fetch.py:208`.
  - HTML conversion is `_convert_html_to_text()` in `src/tunacode/tools/web_fetch.py:118`-`src/tunacode/tools/web_fetch.py:135`.
  - Output truncation is `_truncate_output()` in `src/tunacode/tools/web_fetch.py:138`-`src/tunacode/tools/web_fetch.py:153`.

- `write_file`
  - Inputs are `filepath` and `content` at `src/tunacode/tools/write_file.py:13`.
  - Existing files are rejected with `ToolRetryError` at `src/tunacode/tools/write_file.py:23`-`src/tunacode/tools/write_file.py:27`.
  - Parent directories are created if missing at `src/tunacode/tools/write_file.py:29`-`src/tunacode/tools/write_file.py:31`.
  - The success text result is optionally prefixed with LSP diagnostics at `src/tunacode/tools/write_file.py:36`-`src/tunacode/tools/write_file.py:39`.

## Contracts

- Adapter contract
  - `to_tinyagent_tool()` converts an async Python function to a tinyagent `AgentTool` in `src/tunacode/tools/decorators.py:137`-`src/tunacode/tools/decorators.py:219`.
  - The generated `execute(tool_call_id, args, signal, on_update)` coroutine is defined at `src/tunacode/tools/decorators.py:177`-`src/tunacode/tools/decorators.py:209`.
  - `args` are bound into the Python signature with `sig.bind(**args)` at `src/tunacode/tools/decorators.py:190`.
  - When `strict_validation` is enabled, bound arguments are validated through Pydantic `TypeAdapter(...).validate_python(..., strict=True)` in `src/tunacode/tools/decorators.py:194`-`src/tunacode/tools/decorators.py:198` and `src/tunacode/tools/decorators.py:222`-`src/tunacode/tools/decorators.py:236`.
  - Successful tool results must be `str`; non-string results raise `ToolExecutionError` at `src/tunacode/tools/decorators.py:200`-`src/tunacode/tools/decorators.py:207`.
  - Successful results are wrapped as `AgentToolResult(content=[TextContent(text=result)], details={})` at `src/tunacode/tools/decorators.py:209`.

- Schema contract
  - `_build_openai_parameters_schema()` derives OpenAI-style JSON schema from the function signature in `src/tunacode/tools/decorators.py:239`-`src/tunacode/tools/decorators.py:273`.
  - Primitive mappings are defined at `src/tunacode/tools/decorators.py:276`-`src/tunacode/tools/decorators.py:281`.
  - List, dict, union, and literal annotations are mapped in `src/tunacode/tools/decorators.py:284`-`src/tunacode/tools/decorators.py:360`.

- Error contract
  - `base_tool()` passes through `ToolRetryError`, `ToolExecutionError`, and `FileOperationError`, and wraps any other exception as `ToolExecutionError` in `src/tunacode/tools/decorators.py:48`-`src/tunacode/tools/decorators.py:82`.
  - `file_tool()` maps `FileNotFoundError` to `ToolRetryError`, and `PermissionError`, `UnicodeDecodeError`, and `OSError` to `FileOperationError` in `src/tunacode/tools/decorators.py:85`-`src/tunacode/tools/decorators.py:134`.
  - Exception classes are defined at:
    - `src/tunacode/exceptions.py:138` → `ToolExecutionError`
    - `src/tunacode/exceptions.py:208` → `FileOperationError`
    - `src/tunacode/exceptions.py:334` → `ToolRetryError`

- XML prompt contract
  - `load_prompt_from_xml(tool_name)` loads `<description>` text from `src/tunacode/tools/prompts/{tool_name}_prompt.xml` in `src/tunacode/tools/xml_helper.py:13`-`src/tunacode/tools/xml_helper.py:46`.
  - `base_tool()` replaces the wrapped function docstring with XML content when present in `src/tunacode/tools/decorators.py:75`-`src/tunacode/tools/decorators.py:77`.

- Runtime lifecycle contract
  - Tool calls are registered and started from `ToolExecutionStartEvent` in `src/tunacode/core/agents/main.py:413`-`src/tunacode/core/agents/main.py:435`.
  - Tool completion or failure is recorded from `ToolExecutionEndEvent` in `src/tunacode/core/agents/main.py:437`-`src/tunacode/core/agents/main.py:470`.
  - `ToolCallRegistry` stores `CanonicalToolCall` records and status transitions in `src/tunacode/core/types/tool_registry.py:33`-`src/tunacode/core/types/tool_registry.py:186`.
  - Status values are `PENDING`, `RUNNING`, `COMPLETED`, `FAILED`, and `CANCELLED` in `src/tunacode/types/canonical.py:140`-`src/tunacode/types/canonical.py:147`.

- Callback contract
  - `ToolStartCallback` is `Callable[[str], None]` and `ToolResultCallback` is `Callable[[ToolName, str, ToolArgs, str | None, float | None], None]` in `src/tunacode/types/callbacks.py:62`-`src/tunacode/types/callbacks.py:66`.
  - The orchestrator fulfills the result callback with `tool_name`, `status`, registry `args`, `result_text`, and `duration_ms` at `src/tunacode/core/agents/main.py:463`-`src/tunacode/core/agents/main.py:470`.

- File-read/file-edit cache contract
  - `HashedLine` is defined in `src/tunacode/tools/hashline.py:19`-`src/tunacode/tools/hashline.py:24`.
  - Display format is `<line_number>:<hash>|<content>` in `src/tunacode/tools/hashline.py:55`-`src/tunacode/tools/hashline.py:64`.
  - Reference format `<line_number>:<hash>` is parsed in `src/tunacode/tools/hashline.py:81`-`src/tunacode/tools/hashline.py:106`.
  - The in-memory cache shape is `dict[str, dict[int, HashedLine]]` in `src/tunacode/tools/line_cache.py:14`-`src/tunacode/tools/line_cache.py:20`.

## Dependencies And Data Flow

- `process_request(...)` is the public request entry point in `src/tunacode/core/agents/main.py:620`-`src/tunacode/core/agents/main.py:642`.
- `get_or_create_agent(...)` builds the agent, computes config, loads prompts/context, builds tools, and calls `agent.set_tools(tools)` in `src/tunacode/core/agents/agent_components/agent_config.py:428`-`src/tunacode/core/agents/agent_components/agent_config.py:476`.
- The tool concurrency limiter is a shared `asyncio.Semaphore` built in `src/tunacode/core/agents/agent_components/agent_config.py:167`-`src/tunacode/core/agents/agent_components/agent_config.py:178`.
- `tool_strict_validation` is read from session config in `src/tunacode/core/agents/agent_components/agent_session_config.py:100`-`src/tunacode/core/agents/agent_components/agent_session_config.py:109` and passed into `_build_tools(...)` at `src/tunacode/core/agents/agent_components/agent_config.py:464`.
- Core extracts only `TextContent` from tool results through `extract_tool_result_text()` at `src/tunacode/core/agents/helpers.py:85`-`src/tunacode/core/agents/helpers.py:96`.
- Session persistence serializes tinyagent message models in `src/tunacode/core/session/state.py:170`-`src/tunacode/core/session/state.py:218`.
- Resume sanitization removes dangling tool calls from persisted history in `src/tunacode/core/agents/resume/sanitize.py:442`-`src/tunacode/core/agents/resume/sanitize.py:463`.
- Compaction serializes assistant tool calls and tool results in `src/tunacode/core/compaction/summarizer.py:274`-`src/tunacode/core/compaction/summarizer.py:312`.
- LSP diagnostics are loaded from `settings.lsp` in `src/tunacode/tools/lsp/diagnostics.py:17`-`src/tunacode/tools/lsp/diagnostics.py:43` and prepended by `write_file` and `hashline_edit` in `src/tunacode/tools/write_file.py:38` and `src/tunacode/tools/hashline_edit.py:192`.
- Ignore handling for discovery is provided by `IgnoreManager` in `src/tunacode/tools/ignore_manager.py:73`-`src/tunacode/tools/ignore_manager.py:143`, exposed through `src/tunacode/tools/ignore.py:14`-`src/tunacode/tools/ignore.py:41`, and cached by `src/tunacode/tools/cache_accessors/ignore_manager_cache.py:21`.

## User-Provided MiniMax Example Contract Surface

- The user-provided script from chat on `2026-03-22` defines three `AgentTool` instances named `add_numbers`, `convert_temperature`, and `build_trip_budget`; each tool declares an OpenAI-style JSON schema in `parameters={...}` and an async `execute` function with the four-argument tinyagent signature `(tool_call_id, args, signal, on_update) -> AgentToolResult`.
- In the user-provided script, all three tool implementations return `AgentToolResult(content=[TextContent(...)], details={...})`; the returned `details` payloads include nested objects such as `"input"`, `"output"`, `"breakdown"`, and `"contract"`.
- In the user-provided script, `build_trip_budget(...)` invokes `on_update(...)` before returning its final `AgentToolResult`, emitting a partial tool result with `content=[TextContent(text="budget_calculation_started")]` and `details={"stage": "costs_aggregated", "fixed_cost_count": ...}`.
- In the user-provided script, `_run_example(...)` subscribes to runtime events with `agent.subscribe(on_event)`, inspects `ToolResultMessage` objects from `agent.state.messages`, and records `tool_result.details`, `assistant_stream_event_types`, `agent_event_types`, and message/content-type names for the report.
- The installed local tinyagent package defines the same tool/result surface used by the user-provided script:
  - `.venv/lib/python3.12/site-packages/tinyagent/agent_types.py:227`-`.venv/lib/python3.12/site-packages/tinyagent/agent_types.py:231` → `AgentToolResult(content: list[TextContent | ImageContent], details: JsonObject)`
  - `.venv/lib/python3.12/site-packages/tinyagent/agent_types.py:234` → `AgentToolUpdateCallback = Callable[[AgentToolResult], None]`
  - `.venv/lib/python3.12/site-packages/tinyagent/agent_types.py:247`-`.venv/lib/python3.12/site-packages/tinyagent/agent_types.py:251` → `AgentTool(..., execute: Callable[..., Awaitable[AgentToolResult]] | None = None)`
  - `.venv/lib/python3.12/site-packages/tinyagent/agent_types.py:187`-`.venv/lib/python3.12/site-packages/tinyagent/agent_types.py:195` → `ToolResultMessage(..., content, details, is_error, ...)`
  - `.venv/lib/python3.12/site-packages/tinyagent/agent_types.py:409`-`.venv/lib/python3.12/site-packages/tinyagent/agent_types.py:415` → `ToolExecutionUpdateEvent(..., partial_result: AgentToolResult | None = None)`
- The local tinyagent execution path forwards partial and final structured tool results:
  - `.venv/lib/python3.12/site-packages/tinyagent/agent_tool_execution.py:116`-`.venv/lib/python3.12/site-packages/tinyagent/agent_tool_execution.py:124` defines `on_update(partial_result)` and pushes `ToolExecutionUpdateEvent(..., partial_result=partial_result)` into the event stream.
  - `.venv/lib/python3.12/site-packages/tinyagent/agent_tool_execution.py:149`-`.venv/lib/python3.12/site-packages/tinyagent/agent_tool_execution.py:160` builds `ToolResultMessage(content=result.content, details=result.details, is_error=is_error, ...)`.
  - `.venv/lib/python3.12/site-packages/tinyagent/agent.py:323`-`.venv/lib/python3.12/site-packages/tinyagent/agent.py:327` exposes `Agent.subscribe(...)`.
  - `.venv/lib/python3.12/site-packages/tinyagent/agent.py:351`-`.venv/lib/python3.12/site-packages/tinyagent/agent.py:352` assigns tools with `set_tools(...)`.

## Current Tunacode Narrowing Of The Tinyagent Tool Contract

- TunaCode builds six runtime tools through `_build_tools()` in `src/tunacode/core/agents/agent_components/agent_config.py:181`-`src/tunacode/core/agents/agent_components/agent_config.py:193`, and the concurrency wrapper preserves the tinyagent four-argument execute shape in `src/tunacode/core/agents/agent_components/agent_config.py:93`-`src/tunacode/core/agents/agent_components/agent_config.py:96` and `src/tunacode/core/agents/agent_components/agent_config.py:151`-`src/tunacode/core/agents/agent_components/agent_config.py:160`.
- TunaCode's adapter-generated tool coroutine in `src/tunacode/tools/decorators.py:177`-`src/tunacode/tools/decorators.py:209` receives `tool_call_id`, `args`, `signal`, and `on_update`, then discards `tool_call_id` and `on_update` at `src/tunacode/tools/decorators.py:183`-`src/tunacode/tools/decorators.py:184`.
- The same adapter awaits the wrapped tool function, requires the wrapped tool to return `str`, and constructs `AgentToolResult(content=[TextContent(text=result)], details={})` at `src/tunacode/tools/decorators.py:200`-`src/tunacode/tools/decorators.py:209`.
- TunaCode's base type alias `ToolResult = str` is defined in `src/tunacode/types/base.py:35`-`src/tunacode/types/base.py:36`.
- TunaCode's stream dispatcher branches for tool start and tool end events in `src/tunacode/core/agents/main.py:516`-`src/tunacode/core/agents/main.py:529`; no `ToolExecutionUpdateEvent` branch appears in that dispatch sequence.
- TunaCode's end-of-tool handler converts `event_obj.result` to text with `extract_tool_result_text(...)` in `src/tunacode/core/agents/main.py:446`-`src/tunacode/core/agents/main.py:455`.
- `extract_tool_result_text(...)` reads only `TextContent` items from `result.content` and concatenates their `.text` values in `src/tunacode/core/agents/helpers.py:85`-`src/tunacode/core/agents/helpers.py:96`.
- The UI/tool callback surface accepts `tool_name`, `status`, `args`, `result`, and `duration_ms` in `src/tunacode/types/callbacks.py:63`-`src/tunacode/types/callbacks.py:65`, and `src/tunacode/ui/repl_support.py:188`-`src/tunacode/ui/repl_support.py:215` renders that same five-field payload.
- Session serialization and resume code can carry `ToolResultMessage.details`:
  - `src/tunacode/core/session/state.py:170`-`src/tunacode/core/session/state.py:200` serializes and deserializes `ToolResultMessage` through Pydantic model dumps/validation.
  - `src/tunacode/core/agents/resume/sanitize.py:79`-`src/tunacode/core/agents/resume/sanitize.py:83` defines `ToolResultResumeMessage.details`
  - `src/tunacode/core/agents/resume/sanitize.py:198`-`src/tunacode/core/agents/resume/sanitize.py:206` parses persisted `details`
  - `src/tunacode/core/agents/resume/sanitize.py:278`-`src/tunacode/core/agents/resume/sanitize.py:283` serializes persisted `details`
- In the current live adapter path documented above, the generated `AgentToolResult` sets `details={}` and the runtime/UI handlers cited above read only text content.

## Type And Symbol Index

- `src/tunacode/types/base.py:35` → `ToolArgs = dict[str, Any]`
- `src/tunacode/types/base.py:36` → `ToolResult = str`
- `src/tunacode/types/canonical.py:68` → `ToolCallPart`
- `src/tunacode/types/canonical.py:78` → `ToolReturnPart`
- `src/tunacode/types/canonical.py:140` → `ToolCallStatus`
- `src/tunacode/types/canonical.py:151` → `CanonicalToolCall`
- `src/tunacode/types/callbacks.py:27` → `ToolCallPartProtocol`
- `src/tunacode/types/callbacks.py:58` → `ToolCallback`
- `src/tunacode/types/callbacks.py:62` → `ToolStartCallback`
- `src/tunacode/types/callbacks.py:63` → `ToolResultCallback`
- `src/tunacode/core/types/tool_registry.py:33` → `ToolCallRegistry`
- `src/tunacode/tools/hashline.py:19` → `HashedLine`
- `src/tunacode/tools/utils/discover_types.py:21` → `FileEntry`
- `src/tunacode/tools/utils/discover_types.py:35` → `ConceptCluster`
- `src/tunacode/tools/utils/discover_types.py:44` → `DiscoveryReport`
