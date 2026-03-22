---
title: "tools implementation research findings"
link: "tools-implementation-research"
type: research
ontological_relations:
  - relates_to: [[docs/modules/tools/tools]]
tags: [research, tools, agent]
uuid: "4F28A5ED-1776-49BC-8CAE-DC4DB191DE27"
created_at: "2026-03-22T09:42:58-0500"
---

## Structure
- Model-exposed tool functions are imported and assembled in `src/tunacode/core/agents/agent_components/agent_config.py:38-45` and `src/tunacode/core/agents/agent_components/agent_config.py:181-197`.
- Tool adapters and JSON-schema generation live in `src/tunacode/tools/decorators.py:48-362`.
- Tool lifecycle state is tracked in `src/tunacode/core/types/tool_registry.py:32-186` and attached to runtime state in `src/tunacode/core/types/state_structures.py:60-73`.
- Stream-event handling for tool start/end lives in `src/tunacode/core/agents/main.py:413-471` and the event loop that dispatches those handlers lives in `src/tunacode/core/agents/main.py:485-577`.

## Key Files
- `src/tunacode/core/agents/agent_components/agent_config.py:181-193` → builds the six `AgentTool` objects from `bash`, `discover`, `read_file`, `hashline_edit`, `web_fetch`, and `write_file`.
- `src/tunacode/core/agents/agent_components/agent_config.py:145-178` → wraps each tool `execute` handler with a shared semaphore limit; default maximum is `3` parallel calls.
- `src/tunacode/core/agents/agent_components/agent_config.py:428-477` → creates the `Agent`, sets the system prompt, model, and tool list.
- `src/tunacode/tools/decorators.py:137-219` → converts each async Python tool into a tinyagent `AgentTool`.
- `src/tunacode/tools/decorators.py:239-362` → derives the tool `parameters` JSON schema from Python annotations.
- `src/tunacode/core/agents/main.py:422-455` → receives tool execution start/end events, stores args in the registry, and records success/failure text.
- `src/tunacode/core/agents/helpers.py:85-96` → extracts string output from `AgentToolResult.content`.

## Tool Surface
- `src/tunacode/tools/bash.py:22-29` → `async def bash(command: str, cwd: str | None = None, env: dict[str, str] | None = None, timeout: int | None = DEFAULT_TIMEOUT_SECONDS, capture_output: bool = True) -> str`
- `src/tunacode/tools/discover.py:11-15` → `async def discover(query: str, directory: str = ".") -> str`
- `src/tunacode/tools/read_file.py:34-39` → `async def read_file(filepath: str, offset: int = 0, limit: int | None = None) -> str`
- `src/tunacode/tools/hashline_edit.py:126-135` → `async def hashline_edit(filepath: str, operation: Literal["replace", "replace_range", "insert_after"], line: str | None = None, start: str | None = None, end: str | None = None, after: str | None = None, new: str = "") -> str`
- `src/tunacode/tools/web_fetch.py:229-233` → `async def web_fetch(url: str, timeout: int = DEFAULT_TIMEOUT) -> str`
- `src/tunacode/tools/write_file.py:12-13` → `async def write_file(filepath: str, content: str) -> str`

## Invocation Flow
1. `get_or_create_agent()` builds the tool list with `_build_tools()` and installs it on the tinyagent `Agent` via `agent.set_tools(tools)` in `src/tunacode/core/agents/agent_components/agent_config.py:428-477`.
2. `_build_tools()` converts each async tool function to `AgentTool` via `_to_agent_tool()` and `to_tinyagent_tool()` in `src/tunacode/core/agents/agent_components/agent_config.py:181-197`.
3. `to_tinyagent_tool()` reads the Python function signature with `inspect.signature(func)`, derives a JSON-schema object via `_build_openai_parameters_schema(func)`, and creates `AgentTool(name, label, description, parameters, execute)` in `src/tunacode/tools/decorators.py:170-217`.
4. The generated `execute(tool_call_id, args, signal, on_update)` function binds `args` into the Python function signature, optionally validates bound arguments strictly with Pydantic, awaits the original tool, and wraps the returned string as `AgentToolResult(content=[TextContent(text=result)], details={})` in `src/tunacode/tools/decorators.py:177-209`.
5. During streaming execution, `RequestOrchestrator._run_stream()` iterates `async for event in agent.stream(self.message)` in `src/tunacode/core/agents/main.py:539-577`.
6. On `ToolExecutionStartEvent`, the orchestrator reads `event_obj.tool_call_id`, `event_obj.tool_name`, and `event_obj.args or {}`, registers them in `runtime.tool_registry`, and marks the call running in `src/tunacode/core/agents/main.py:413-435`.
7. On `ToolExecutionEndEvent`, the orchestrator calls `extract_tool_result_text(event_obj.result)`, marks the registry entry failed or completed, then invokes `tool_result_callback(tool_name, status, callback_args, result_text, duration_ms)` in `src/tunacode/core/agents/main.py:437-471`.

## Request / Response Shapes
- Base aliases define `ToolArgs = dict[str, Any]`, `ToolResult = str`, `ToolCallId = str`, and `ToolName = str` in `src/tunacode/types/base.py:12-17` and `src/tunacode/types/base.py:34-37`.
- The adapter-layer execute signature is `Callable[[str, JsonObject, asyncio.Event | None, AgentToolUpdateCallback], Awaitable[AgentToolResult]]` in `src/tunacode/core/agents/agent_components/agent_config.py:93-96`.
- The registry record is `CanonicalToolCall(tool_call_id: str, tool_name: str, args: dict[str, Any], status: ToolCallStatus = ..., result: str | None = None, error: str | None = None, started_at: datetime | None = None, completed_at: datetime | None = None)` in `src/tunacode/types/canonical.py:150-175`.
- `ToolCallPart` and `ToolReturnPart` carry `tool_call_id`, `tool_name`, `args`, and returned `content` in `src/tunacode/types/canonical.py:67-95`.
- `ToolResultCallback` is `Callable[[ToolName, str, ToolArgs, str | None, float | None], None]` and `ToolStartCallback` is `Callable[[str], None]` in `src/tunacode/types/callbacks.py:62-67`.
- The JSON-schema builder emits an object of the form `{"type": "object", "properties": {...}, "required": [...]}` in `src/tunacode/tools/decorators.py:239-273`.
- Type-to-schema mapping supports primitives, `list[T]`, `dict[str, T]`, unions / optionals, and `Literal[...]` via `type`, `items`, `additionalProperties`, `anyOf`, and `enum` fields in `src/tunacode/tools/decorators.py:276-362`.

## Tool Data Inputs
- Tool descriptions can be replaced by XML prompt text loaded from `src/tunacode/tools/prompts/{tool_name}_prompt.xml` through `load_prompt_from_xml()` in `src/tunacode/tools/xml_helper.py:13-46`; the prompt files currently present are:
  - `src/tunacode/tools/prompts/bash_prompt.xml:1-11`
  - `src/tunacode/tools/prompts/discover_prompt.xml:1-39`
  - `src/tunacode/tools/prompts/hashline_edit_prompt.xml:1-16`
  - `src/tunacode/tools/prompts/read_file_prompt.xml:1-11`
  - `src/tunacode/tools/prompts/web_fetch_prompt.xml:1-11`
  - `src/tunacode/tools/prompts/write_file_prompt.xml:1-7`
- `tool_strict_validation` is read from `session.user_config["settings"]` and normalized into `AgentSettings.tool_strict_validation` in `src/tunacode/core/agents/agent_components/agent_session_config.py:15-27` and `src/tunacode/core/agents/agent_components/agent_session_config.py:79-115`.
- Default settings include `max_retries: 3`, `max_iterations: 40`, `request_delay: 0.0`, and `global_request_timeout: 600.0` in `src/tunacode/configuration/defaults.py:11-39`.

## Per-Tool Inputs and Outputs
- `bash()` validates non-empty `command`, optional directory existence, and timeout range `1..600` in `src/tunacode/tools/bash.py:91-106`; it merges `env` into `os.environ`, optionally sets `cwd`, executes a subprocess shell, and returns a formatted text block containing command, exit code, working directory, stdout, and stderr in `src/tunacode/tools/bash.py:42-88` and `src/tunacode/tools/bash.py:131-156`. Output truncation uses `get_command_limit()` from `src/tunacode/configuration/limits.py:59-62`.
- `discover()` passes `query` and `directory` to `_discover_sync()` on a worker thread in `src/tunacode/tools/discover.py:11-30`. `_discover_sync()` resolves the root path, obtains an `IgnoreManager`, extracts search terms, detects dominant extensions, generates glob-like patterns, collects candidate files, evaluates relevance, clusters results, and returns a `DiscoveryReport` in `src/tunacode/tools/utils/discover_pipeline.py:413-447`. `DiscoveryReport.to_context()` serializes the result as a string with a summary, optional tree, clusters, file entries, symbols, imports, and excerpts in `src/tunacode/tools/utils/discover_types.py:43-92`.
- `read_file()` accepts `filepath`, `offset`, and `limit` in `src/tunacode/tools/read_file.py:34-39`, rejects files larger than `100KB` in `src/tunacode/tools/read_file.py:57-61`, reads lines on a worker thread, tags each returned line with `line_number:hash|content`, includes either a "more lines" or EOF footer, stores the full untruncated returned window in the line cache, and returns a `<file>...</file>` text block in `src/tunacode/tools/read_file.py:66-133`. Hash generation and formatting are implemented in `src/tunacode/tools/hashline.py:19-106`.
- `hashline_edit()` accepts a `filepath`, an `operation` literal, and one of `line`, `start`/`end`, or `after`, plus `new` text in `src/tunacode/tools/hashline_edit.py:126-163`. It validates `line:hash` references against the in-memory cache in `_validate_ref()` (`src/tunacode/tools/hashline_edit.py:56-87`), reads the current file, applies one of `_apply_replace`, `_apply_replace_range`, or `_apply_insert_after` (`src/tunacode/tools/hashline_edit.py:196-292`), writes the new file, mutates the cache via `update_lines()` or `replace_range()` from `src/tunacode/tools/line_cache.py:52-127`, builds a unified diff string, and returns `<diagnostics if any>\n\n<description>\n\n<diff>` in `src/tunacode/tools/hashline_edit.py:164-193`.
- `web_fetch()` validates `url` scheme and host in `_validate_url()` (`src/tunacode/tools/web_fetch.py:71-115`), blocks localhost and private/reserved IPs using `_is_private_ip()` and `BLOCKED_HOSTNAMES` (`src/tunacode/tools/web_fetch.py:31-69`), constrains timeout to `5..120` in `src/tunacode/tools/web_fetch.py:243-244`, performs `HEAD` and `GET` requests with `httpx.AsyncClient`, re-validates redirect targets, enforces a `5MB` maximum response size, decodes bytes to text, converts HTML through `html2text`, truncates output to `100KB`, and returns the processed text in `src/tunacode/tools/web_fetch.py:164-208` and `src/tunacode/tools/web_fetch.py:229-264`.
- `write_file()` accepts `filepath` and `content` in `src/tunacode/tools/write_file.py:12-13`, rejects existing files in `src/tunacode/tools/write_file.py:23-27`, creates parent directories as needed in `src/tunacode/tools/write_file.py:29-31`, writes UTF-8 text in `src/tunacode/tools/write_file.py:33-34`, and returns a success string, optionally prefixed with LSP diagnostics, in `src/tunacode/tools/write_file.py:36-39`.

## Shared Error and Diagnostics Paths
- `base_tool()` passes through `ToolRetryError`, `ToolExecutionError`, and `FileOperationError`, wraps other exceptions as `ToolExecutionError`, and preserves the original function signature in `src/tunacode/tools/decorators.py:48-82`.
- `file_tool()` adds file-specific conversions: `FileNotFoundError -> ToolRetryError`, `PermissionError` / `UnicodeDecodeError` / `OSError -> FileOperationError`, then passes the wrapper through `base_tool()` in `src/tunacode/tools/decorators.py:85-134`.
- `ToolExecutionError`, `FileOperationError`, `UserAbortError`, and `ToolRetryError` are defined in `src/tunacode/exceptions.py:110-160`, `src/tunacode/exceptions.py:208-221`, and `src/tunacode/exceptions.py:334-347`.
- File-writing tools prepend diagnostics through `maybe_prepend_lsp_diagnostics(result: str, filepath: Path) -> str` in `src/tunacode/tools/lsp/diagnostics.py:46-65`. That function reads `settings.lsp.enabled` and `settings.lsp.timeout` from user config in `src/tunacode/tools/lsp/diagnostics.py:17-43`, then uses `get_diagnostics()` / `format_diagnostics()` from `src/tunacode/tools/lsp/__init__.py:41-107`.
