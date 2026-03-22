---
title: "codebase-locator tool system research findings"
link: "codebase-locator-tool-system-research"
type: research
ontological_relations:
  - relates_to: [[tools-layer]]
tags: [research, codebase-locator, tools]
uuid: "96487375-E914-4E32-A0AB-EBBCE9F2C896"
created_at: "2026-03-22T09:43:03-0500"
---

## Structure

- `src/tunacode/tools/` contains the concrete tool entry functions, tool decorators/adapters, XML prompt loading, prompt files, and supporting subsystems.
- `src/tunacode/core/agents/agent_components/agent_config.py` imports the concrete tools, converts them to tinyagent `AgentTool` objects, and attaches them to the agent.
- `src/tunacode/core/agents/main.py` records tool lifecycle start/end events into the runtime registry.
- `src/tunacode/core/types/tool_registry.py` stores runtime tool call state.
- `src/tunacode/types/` defines tool argument aliases, callback protocols, and canonical tool-call structures.
- `src/tunacode/ui/repl_support.py` forwards tool results to the UI, and `src/tunacode/ui/renderers/tools/` registers per-tool renderers.
- `README.md` and `docs/modules/*.md` document the tool layer and tool list.

## Key Files

- `src/tunacode/ui/main.py:1` defines the CLI entry module; `pyproject.toml:47-48` exposes `tunacode = "tunacode.ui.main:app"`.
- `src/tunacode/tools/__init__.py:1-10` is the tools package entry and lazy-loads submodules through `__getattr__`.
- `src/tunacode/tools/decorators.py:48-82` defines `base_tool`; `src/tunacode/tools/decorators.py:85-134` defines `file_tool`; `src/tunacode/tools/decorators.py:137-219` defines `to_tinyagent_tool`; `src/tunacode/tools/decorators.py:239-362` builds JSON schema from Python signatures.
- `src/tunacode/tools/xml_helper.py:13-46` loads XML prompt descriptions by tool name; `src/tunacode/tools/xml_helper.py:49-59` resolves prompt file paths.
- `src/tunacode/tools/bash.py:22-29` defines `bash(...)`.
- `src/tunacode/tools/discover.py:11-15` defines `discover(...)`.
- `src/tunacode/tools/read_file.py:34-39` defines `read_file(...)`.
- `src/tunacode/tools/hashline_edit.py:126-135` defines `hashline_edit(...)`.
- `src/tunacode/tools/web_fetch.py:229-233` defines `web_fetch(...)`.
- `src/tunacode/tools/write_file.py:12-13` defines `write_file(...)`.
- `src/tunacode/tools/hashline.py:19-24` defines `HashedLine`; `src/tunacode/tools/hashline.py:27-33` defines `content_hash`; `src/tunacode/tools/hashline.py:81-106` defines `parse_line_ref`.
- `src/tunacode/tools/line_cache.py:18-20` defines `store`; `src/tunacode/tools/line_cache.py:23-28` defines `get`; `src/tunacode/tools/line_cache.py:52-72` defines `update_lines`; `src/tunacode/tools/line_cache.py:75-126` defines `replace_range`.
- `src/tunacode/tools/utils/discover_pipeline.py:31-67` extracts search terms; `src/tunacode/tools/utils/discover_pipeline.py:124-153` collects candidate files; `src/tunacode/tools/utils/discover_pipeline.py:169-214` evaluates candidate relevance.
- `src/tunacode/tools/utils/discover_types.py:16-18` defines `Relevance`; `src/tunacode/tools/utils/discover_types.py:21-31` defines `FileEntry`; `src/tunacode/tools/utils/discover_types.py:34-40` defines `ConceptCluster`; `src/tunacode/tools/utils/discover_types.py:43-92` defines `DiscoveryReport` and `to_context()`.
- `src/tunacode/tools/lsp/diagnostics.py:46-65` defines `maybe_prepend_lsp_diagnostics`, used by file-edit tools.
- `src/tunacode/tools/ignore.py:14-17` exposes cached `get_ignore_manager`; `src/tunacode/tools/ignore_manager.py:73-144` defines `IgnoreManager` and `create_ignore_manager`.
- `src/tunacode/tools/cache_accessors/xml_prompts_cache.py:13-46` caches XML tool descriptions.
- `src/tunacode/tools/cache_accessors/ignore_manager_cache.py:16-60` caches `IgnoreManager` instances.
- `src/tunacode/tools/cache_accessors/ripgrep_cache.py:7-59` caches ripgrep binary metadata.

## Registration And Exposure

- `src/tunacode/core/agents/agent_components/agent_config.py:38-44` imports `bash`, `discover`, `hashline_edit`, `read_file`, `web_fetch`, and `write_file`.
- `src/tunacode/core/agents/agent_components/agent_config.py:145-178` wraps tools with a shared concurrency limiter.
- `src/tunacode/core/agents/agent_components/agent_config.py:181-193` assembles the tool list in `_build_tools()`.
- `src/tunacode/core/agents/agent_components/agent_config.py:196-197` converts one callable through `_to_agent_tool()`.
- `src/tunacode/core/agents/agent_components/agent_config.py:428-477` creates the agent and calls `agent.set_tools(tools)`.
- `src/tunacode/core/agents/main.py:413-435` handles `ToolExecutionStartEvent`, registers the tool call, and marks it running.
- `src/tunacode/core/agents/main.py:437-471` handles `ToolExecutionEndEvent`, marks the tool call completed/failed, and invokes the result callback.
- `src/tunacode/core/types/tool_registry.py:39-59` registers tool calls; `src/tunacode/core/types/tool_registry.py:61-115` updates status; `src/tunacode/core/types/tool_registry.py:165-177` exports legacy `tool_calls` records.
- `src/tunacode/ui/main.py:166-181` serializes `runtime.tool_registry.to_legacy_records()` into headless trajectory JSON.
- `src/tunacode/ui/repl_support.py:142-149` defines the textual tool callback stub; `src/tunacode/ui/repl_support.py:187-218` defines `build_tool_result_callback()`.
- `src/tunacode/ui/renderers/tools/base.py:136-180` maintains the renderer registry with `tool_renderer`, `get_renderer`, and `list_renderers`.
- `src/tunacode/ui/renderers/tools/__init__.py:24-37` imports renderer modules so decorator registration executes at import time.
- `src/tunacode/ui/renderers/tools/bash.py:248`, `src/tunacode/ui/renderers/tools/discover.py:346`, `src/tunacode/ui/renderers/tools/read_file.py:270`, `src/tunacode/ui/renderers/tools/hashline_edit.py:434`, `src/tunacode/ui/renderers/tools/web_fetch.py:185`, and `src/tunacode/ui/renderers/tools/write_file.py:162` register tool renderers.
- `src/tunacode/ui/renderers/panels.py:486-523` routes completed tool results through `get_renderer(name.lower())`.

## Inputs And Contracts

- `src/tunacode/types/base.py:13-16` defines `ToolName` and `ToolCallId`; `src/tunacode/types/base.py:35-36` defines `ToolArgs` and `ToolResult`.
- `src/tunacode/types/callbacks.py:27-38` defines `ToolCallPartProtocol`; `src/tunacode/types/callbacks.py:58-66` defines `ToolCallback`, `ToolStartCallback`, and `ToolResultCallback`; `src/tunacode/types/callbacks.py:76` defines `AsyncToolFunc`.
- `src/tunacode/types/canonical.py:68-74` defines `ToolCallPart`; `src/tunacode/types/canonical.py:78-83` defines `ToolReturnPart`; `src/tunacode/types/canonical.py:140-147` defines `ToolCallStatus`; `src/tunacode/types/canonical.py:150-174` defines `CanonicalToolCall`.
- `src/tunacode/types/__init__.py:34-37`, `src/tunacode/types/__init__.py:45-58`, and `src/tunacode/types/__init__.py:61-79` re-export the tool-related aliases and canonical types.
- `src/tunacode/core/ui_api/shared_types.py:5-16` re-exports tool-related types for UI consumers.

## Tool Prompt Files

- `src/tunacode/tools/prompts/bash_prompt.xml:1-11`
- `src/tunacode/tools/prompts/discover_prompt.xml:1-39`
- `src/tunacode/tools/prompts/hashline_edit_prompt.xml:1-16`
- `src/tunacode/tools/prompts/read_file_prompt.xml:1-11`
- `src/tunacode/tools/prompts/web_fetch_prompt.xml:1-11`
- `src/tunacode/tools/prompts/write_file_prompt.xml:1-7`

## Documentation

- `README.md:134-149` lists the user-facing tool table.
- `docs/modules/index.md:19-20` places `tools` in the architecture stack; `docs/modules/index.md:36-43` links the tools module doc.
- `docs/modules/tools/tools.md:15` states each tool is an async function decorated with `@base_tool` or `@file_tool` and converted through `to_tinyagent_tool()`.
- `docs/modules/tools/tools.md:21-31` lists documented tool implementation files.
- `docs/modules/tools/tools.md:35-38` documents `decorators.py` and `xml_helper.py`.
- `docs/modules/tools/tools.md:42-47` documents the hashline subsystem.
- `docs/modules/tools/tools.md:49-87` documents discover, grep, LSP, utility, and cache-accessor support modules.
- `docs/modules/tools/tools.md:91-97` documents the tool registration flow.
- `docs/modules/core/core.md:151-160` lists the tool descriptions used in the core architecture doc.
- `docs/modules/ui/ui.md:63` documents the UI tool-renderer directory.
- `docs/modules/types/types.md:22-24` documents the tool-related type modules.

## Validation Files

- `tests/integration/tools/test_tool_conformance.py:18-57` discovers tool modules from `src/tunacode/tools/*.py`; `tests/integration/tools/test_tool_conformance.py:76-143` validates async signatures, docstrings, filepath-first file tools, and string return types.
- `tests/unit/tools/test_tinyagent_tool_adapter.py:13-103` validates `to_tinyagent_tool()` execution, argument binding, strict validation, and abort behavior.
- `tests/unit/tools/test_tool_decorators.py:13-98` validates `base_tool`; `tests/unit/tools/test_tool_decorators.py:99-204` validates `file_tool`.

## Files Mentioned In Docs But Not Present In `src/tunacode/tools/`

- The documentation tool tables reference `glob.py`, `grep.py`, `list_dir.py`, and `update_file.py` at `README.md:142-148` and `docs/modules/tools/tools.md:23-31`.
- A repository scan under `src/tunacode/` found no source files matching those module names.
