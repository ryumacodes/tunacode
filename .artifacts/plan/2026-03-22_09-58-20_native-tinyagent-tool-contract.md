---
title: "native tinyagent tool contract implementation plan"
link: "native-tinyagent-tool-contract-plan"
type: implementation_plan
ontological_relations:
  - relates_to: [[tools-data-inputs-contracts-research]]
  - relates_to: [[tool-result-adapter-runtime-research]]
  - relates_to: [[minimax-tinyagent-contract-shape-vs-runtime-research]]
tags: [plan, tools, tinyagent, contracts]
uuid: "63700901-E626-467A-8282-6A6DB2EFBE6E"
created_at: "2026-03-22T09:58:20-0500"
parent_research: ".artifacts/research/2026-03-22_09-45-29_tools-data-inputs-contracts.md"
git_commit_at_plan: "4cf456d4"
---

## Goal

- Remove the current TunaCode tools layer and tool helper/facade utilities, then rebuild the supported tool surface directly on native tinyagent contracts.
- Execution outcome: this is a hard cutover. There is no `to_tinyagent_tool(...)` wrapper path, no decorator-based tool facade, supported tools are registered as native `AgentTool` definitions, and runtime/canonical/UI paths preserve structured `content` and `details` from native `AgentToolResult`.
- Out of scope:
  - adding new tools beyond the current supported set
  - changing provider configuration or MiniMax-specific request plumbing
  - broad README cleanup unrelated to the native tinyagent tool contract

## Scope & Assumptions

- In scope:
  - remove the current tool entrypoints under `src/tunacode/tools/` and the helper/facade modules that exist only to support the legacy wrapper path
  - remove legacy tool-facing documentation, prompts, tests, and benchmark artifacts that describe or enforce the old tools surface
  - rebuild the six supported tools as native tinyagent tools without `base_tool`, `file_tool`, or `to_tinyagent_tool(...)`
  - retire `ToolResult = str` and related text-only callback assumptions
  - register native `AgentTool` instances directly from the agent configuration path
  - forward `tool_call_id`, `signal`, and `on_update` through the runtime without an intermediate facade
  - handle `ToolExecutionUpdateEvent` in the orchestrator and surface partial updates to the UI
  - preserve `tool_name`, `content`, `details`, and `is_error` through canonical conversion and resume-safe serialization
  - update focused docs/metadata needed to keep developer documentation consistent with the implementation
- Out of scope:
  - adding image-producing tools in this phase
  - redesigning the Textual tool panel beyond what is needed to display native tool results
  - changing unrelated tool names documented in `README.md`
- Assumptions:
  - the installed tinyagent version in `.venv` already exposes `AgentToolResult`, `ToolExecutionUpdateEvent`, and `ToolResultMessage.details`
  - the six currently supported tools remain the target set after the rebuild: `bash`, `discover`, `read_file`, `hashline_edit`, `web_fetch`, and `write_file`
  - temporary breakage is acceptable inside the execution branch between the legacy-tool deletion task and the native-tool rebuild task, but the plan must not leave an empty or wrapper-backed tool surface at the end
  - session persistence may continue to use tinyagent message models; this plan only changes the lossy internal/canonical paths that currently flatten tool results

## Deliverables

- Legacy tool facade and helper layer removed from the runtime path
- Legacy tool-facing documentation, prompts, and obsolete tests/benchmarks removed from the repository
- Native tinyagent tool definitions for the six supported tools
- Direct tool registration from agent configuration with no wrapper/facade function
- Runtime support for partial tool updates and full final tool results
- Canonical tool-result representation that preserves `tool_name`, `content`, `details`, and `is_error`
- UI callback and panel rendering support for native tool results
- Updated developer-facing docs/metadata for the new contract

## Readiness

- Preconditions:
  - research docs are present:
    - `.artifacts/research/2026-03-22_09-45-29_tools-data-inputs-contracts.md`
    - `.artifacts/research/2026-03-22_09-53-07_tool-result-adapter-runtime.md`
    - `.artifacts/research/2026-03-22_09-53-52_minimax-tinyagent-contract-shape-vs-runtime.md`
  - current git base recorded as `4cf456d4`
  - current working tree already contains untracked research artifacts; do not delete or clean them during execution
- Execution notes:
  - execute the removal work first: delete the legacy tool surface and wrapper utilities before adding replacement native tools
  - do not introduce a compatibility facade, bridge, or adapter function that converts old-style tool functions into tinyagent tools
  - if reusable logic from the deleted tools must survive, move that logic into non-facade helper modules with domain-specific names; do not preserve the decorator/prompt-loader wrapper architecture
  - use the tinyagent MiniMax contract example as the implementation reference for direct `AgentTool` definitions, typed JSON-schema parameters, `execute(tool_call_id, args, signal, on_update)`, and `AgentToolResult(content, details)`

## Milestones

- M1: Remove the legacy tool surface and tool utilities
- M2: Rebuild the supported tools as direct native tinyagent tools
- M3: Runtime/canonical/UI preservation of full native tool results
- M4: Focused tests plus developer docs/metadata alignment

## Work Breakdown (Tasks)

## Task T001: Delete the legacy tool entrypoints, facade utilities, and tool-surface artifacts

- Summary: Remove the current tools layer implementation first, including the decorator/facade utilities and the repository artifacts that exist only for the legacy tool surface.
- Owner: JR Dev
- Estimate: 2 hours
- Dependencies: none
- Target milestone: M1
- Changes:
  - Delete the current legacy tool entrypoint implementations:
    - `src/tunacode/tools/bash.py`
    - `src/tunacode/tools/discover.py`
    - `src/tunacode/tools/read_file.py`
    - `src/tunacode/tools/hashline_edit.py`
    - `src/tunacode/tools/web_fetch.py`
    - `src/tunacode/tools/write_file.py`
  - Delete the wrapper/facade support modules that should not survive the rebuild:
    - `src/tunacode/tools/decorators.py`
    - `src/tunacode/tools/xml_helper.py`
    - `src/tunacode/tools/prompts/bash_prompt.xml`
    - `src/tunacode/tools/prompts/discover_prompt.xml`
    - `src/tunacode/tools/prompts/read_file_prompt.xml`
    - `src/tunacode/tools/prompts/hashline_edit_prompt.xml`
    - `src/tunacode/tools/prompts/web_fetch_prompt.xml`
    - `src/tunacode/tools/prompts/write_file_prompt.xml`
  - Delete or relocate legacy tool-only utility modules that are no longer referenced after the entrypoints are removed:
    - `src/tunacode/tools/cache_accessors/`
    - `src/tunacode/tools/utils/`
    - `src/tunacode/tools/ignore.py`
    - `src/tunacode/tools/ignore_manager.py`
    - `src/tunacode/tools/hashline.py`
    - `src/tunacode/tools/line_cache.py`
  - Delete legacy tool-facing tests and benchmarks that only validate the removed surface:
    - `tests/unit/tools/`
    - `tests/tools/`
    - `tests/integration/tools/`
    - `tests/benchmarks/bench_discover.py`
  - Remove legacy tool documentation before the rebuild so the repository does not keep describing the deleted surface:
    - `docs/modules/tools/tools.md`
    - legacy tool-contract notes in `docs/modules/core/core.md`
  - Update `src/tunacode/core/agents/agent_components/agent_config.py`, `src/tunacode/tools/__init__.py`, and any surviving imports so nothing references the deleted tool surface.
- Files/modules touched:
  - `src/tunacode/tools/`
  - `src/tunacode/core/agents/agent_components/agent_config.py`
  - `tests/unit/tools/`
  - `tests/tools/`
  - `tests/integration/tools/`
  - `tests/benchmarks/bench_discover.py`
  - `docs/modules/tools/tools.md`
  - `docs/modules/core/core.md`
- Acceptance test: `rg -n "to_tinyagent_tool|base_tool|file_tool|load_prompt_from_xml|tunacode\\.tools\\.(bash|discover|read_file|hashline_edit|web_fetch|write_file)" src/tunacode tests docs` returns no references to the deleted legacy tool surface after the removal pass.

## Task T002: Rebuild the six supported tools as direct native tinyagent tools

- Summary: Recreate `bash`, `discover`, `read_file`, `hashline_edit`, `web_fetch`, and `write_file` as native tinyagent tools with no decorator/facade layer.
- Owner: JR Dev
- Estimate: 3 hours
- Dependencies: T001
- Target milestone: M2
- Changes:
  - Reintroduce the six supported tools as native tinyagent implementations, either at the same module paths or at replacement module paths under `src/tunacode/tools/`, but expose them as `AgentTool` definitions or factory functions that already satisfy the tinyagent contract.
  - Build each tool around direct `execute(tool_call_id, args, signal, on_update)` behavior instead of wrapping a legacy async function signature.
  - Keep current human-readable output in `TextContent`, but construct `AgentToolResult` inside each tool implementation.
  - Preserve the existing file-edit and diagnostics behavior by moving reusable business logic into ordinary helper functions only where necessary; do not restore decorators, XML prompt loaders, or wrapper classes.
- Files/modules touched:
  - `src/tunacode/tools/bash.py`
  - `src/tunacode/tools/discover.py`
  - `src/tunacode/tools/read_file.py`
  - `src/tunacode/tools/hashline_edit.py`
  - `src/tunacode/tools/web_fetch.py`
  - `src/tunacode/tools/write_file.py`
  - any replacement helper modules created under `src/tunacode/tools/` for shared logic that is not a facade
  - replacement tests created under `tests/unit/tools/` and `tests/integration/tools/`
  - `tests/integration/core/test_tinyagent_tool_execution_contract.py`
- Acceptance test: `tests/integration/core/test_tinyagent_tool_execution_contract.py` shows a real TunaCode tool is already a native tinyagent tool and returns `AgentToolResult` without any wrapper-generated conversion.

## Task T003: Register native tinyagent tools directly from agent configuration

- Summary: Replace wrapper-based tool construction with direct registration of the rebuilt native tool definitions.
- Owner: JR Dev
- Estimate: 2 hours
- Dependencies: T002
- Target milestone: M2
- Changes:
  - Rewrite `_build_tools(...)` in `src/tunacode/core/agents/agent_components/agent_config.py` so it imports and returns native `AgentTool` instances directly.
  - Delete `_to_agent_tool(...)` and any remaining wrapper-specific helper code.
  - Update imports, type aliases, and benchmarks/tests so the runtime path no longer depends on `to_tinyagent_tool(...)`, `base_tool`, or `file_tool`.
  - Keep current concurrency limiting behavior, but apply it directly to native `AgentTool.execute`.
- Files/modules touched:
  - `src/tunacode/core/agents/agent_components/agent_config.py`
  - `src/tunacode/core/agents/agent_components/agent_helpers.py`
  - `tests/integration/core/test_tinyagent_tool_execution_contract.py`
  - `tests/integration/core/test_tinyagent_tool_execution_contract.py`
- Acceptance test: `tests/integration/tools/test_tool_conformance.py` verifies the supported tools can be loaded and registered without any wrapper/facade module.

## Task T004: Replace text-only internal tool-result types with native result payloads

- Summary: Update the internal type and registry layer so tool results are modeled as native tinyagent payloads instead of `str`.
- Owner: JR Dev
- Estimate: 2 hours
- Dependencies: T003
- Target milestone: M2
- Changes:
  - Replace `ToolResult = str` in `src/tunacode/types/base.py` with a native tinyagent-backed tool-result type or equivalent structured alias that can carry full `AgentToolResult` data.
  - Update `src/tunacode/types/callbacks.py` so `AsyncToolFunc` and `ToolResultCallback` no longer assume `str` results.
  - Update `src/tunacode/types/canonical.py` so `ToolReturnPart` and `CanonicalToolCall` can preserve `tool_name`, `content`, `details`, and `is_error` instead of only `content`/`result`/`error` text.
  - Update `src/tunacode/types/__init__.py` and `src/tunacode/core/types/tool_registry.py` exports/usages to match the new shapes.
- Files/modules touched:
  - `src/tunacode/types/base.py`
  - `src/tunacode/types/callbacks.py`
  - `src/tunacode/types/canonical.py`
  - `src/tunacode/types/__init__.py`
  - `src/tunacode/core/types/tool_registry.py`
  - `tests/unit/types/test_canonical.py`
  - `tests/unit/types/test_tool_registry.py`
- Acceptance test: `tests/unit/types/test_tool_registry.py` proves a completed and failed tool call can retain structured result metadata without flattening it to a single string.

## Task T005: Propagate native tool updates through the request orchestrator

- Summary: Teach the request loop to handle `ToolExecutionUpdateEvent` and preserve full native tool results in callbacks and registry state.
- Owner: JR Dev
- Estimate: 3 hours
- Dependencies: T003, T004
- Target milestone: M3
- Changes:
  - Import and handle `ToolExecutionUpdateEvent` in `src/tunacode/core/agents/main.py`.
  - Replace the text-only `extract_tool_result_text(...)` usage with native result handling; keep text extraction only as a derived helper for places that truly need plain text.
  - Update `src/tunacode/core/agents/helpers.py` so helper functions can extract display text from native `content` without dropping structured fields.
  - Update `ToolCallRegistry.complete(...)` and `.fail(...)` calls so registry state preserves the structured result payload defined in T004.
  - Update `ToolResultCallback` invocation to pass native tool results and mark whether an update is partial or final.
- Files/modules touched:
  - `src/tunacode/core/agents/main.py`
  - `src/tunacode/core/agents/helpers.py`
  - `src/tunacode/core/types/tool_registry.py`
  - `src/tunacode/types/callbacks.py`
  - `tests/unit/core/test_request_orchestrator_parallel_tools.py`
  - `tests/unit/core/test_agent_helpers.py`
- Acceptance test: `tests/unit/core/test_request_orchestrator_parallel_tools.py` verifies start, partial update, and final completion events preserve native tool-result payloads in callback order and registry state.

## Task T006: Preserve native tool results through canonical conversion, resume, compaction, and UI rendering

- Summary: Remove the remaining lossy text-only handling across canonical conversion, resume-safe serialization, compaction, and the REPL tool-result display path.
- Owner: JR Dev
- Estimate: 3 hours
- Dependencies: T004, T005
- Target milestone: M3
- Changes:
  - Update `src/tunacode/utils/messaging/adapter.py` so `to_canonical(...)` and `from_canonical(...)` preserve `tool_name`, full `content`, `details`, and `is_error` for tool-result messages.
  - Keep `src/tunacode/core/agents/resume/sanitize.py` aligned with the new canonical fields so sanitized resume payloads remain round-trippable.
  - Update `src/tunacode/core/compaction/summarizer.py` to derive summary text from the native tool result instead of assuming a single flattened string.
  - Update `src/tunacode/ui/repl_support.py` so `build_tool_result_callback(...)` accepts native tool results and partial/final status information.
  - Update `src/tunacode/ui/widgets/messages.py` and `src/tunacode/ui/app.py` so `ToolResultDisplay` carries the richer payload.
  - Update `src/tunacode/ui/renderers/panels.py` to render display text from `AgentToolResult.content` and add a small structured-details block only when `details` is non-empty.
  - Preserve the existing LSP refresh behavior for file-edit tools after final completion only.
- Files/modules touched:
  - `src/tunacode/utils/messaging/adapter.py`
  - `src/tunacode/types/canonical.py`
  - `src/tunacode/core/agents/resume/sanitize.py`
  - `src/tunacode/core/compaction/summarizer.py`
  - `src/tunacode/ui/repl_support.py`
  - `src/tunacode/ui/widgets/messages.py`
  - `src/tunacode/ui/app.py`
  - `src/tunacode/ui/renderers/panels.py`
  - `tests/unit/types/test_adapter.py`
  - `tests/unit/types/test_canonical.py`
  - `tests/unit/core/test_compaction_summarizer.py`
  - `tests/test_compaction.py`
  - `tests/system/cli/test_repl_support.py`
- Acceptance test: `tests/unit/types/test_adapter.py` round-trips a `tool_result` message with non-empty `details` and `is_error=True` without losing fields.

## Task T007: Add focused regression coverage for the native tinyagent contract

- Summary: Rewrite the narrow contract tests so they match the delete-first, no-facade native tinyagent architecture.
- Owner: JR Dev
- Estimate: 2 hours
- Dependencies: T002, T003, T004, T005, T006
- Target milestone: M4
- Changes:
  - Recreate only the tests needed for the rebuilt native tool surface; do not restore the removed legacy tool test directories as a copy-forward of the old design.
  - Update tests that currently assert `details={}` or text-only `ToolReturnPart` behavior.
  - Add one orchestrator-level regression that covers `ToolExecutionUpdateEvent`.
  - Add one canonical adapter regression that covers tool-result `details`.
  - Keep the scope narrow; do not expand to full end-to-end provider tests in this phase.
- Files/modules touched:
  - `tests/unit/tools/`
  - `tests/integration/core/test_tinyagent_tool_execution_contract.py`
  - `tests/integration/tools/test_tool_conformance.py`
  - `tests/unit/core/test_request_orchestrator_parallel_tools.py`
  - `tests/unit/types/test_adapter.py`
  - `tests/unit/types/test_tool_registry.py`
  - `tests/system/cli/test_repl_support.py`
- Acceptance test: `uv run pytest tests/integration/core/test_tinyagent_tool_execution_contract.py tests/integration/tools/test_tool_conformance.py tests/unit/core/test_request_orchestrator_parallel_tools.py tests/unit/types/test_adapter.py tests/unit/types/test_tool_registry.py tests/system/cli/test_repl_support.py`

## Task T008: Align developer docs and repository metadata with the native contract

- Summary: Update the minimum documentation and metadata required by repository rules after the contract migration lands.
- Owner: JR Dev
- Estimate: 1 hour
- Dependencies: T007
- Target milestone: M4
- Changes:
  - Re-add only the minimal developer documentation needed for the rebuilt tool surface after T001 removed the old tool docs.
  - Update the tool-contract sections in `docs/modules/tools/tools.md` and `docs/modules/core/core.md` so they describe the direct native tinyagent tool architecture and no longer mention decorator/facade-based tool wrapping.
  - Update `AGENTS.md` `Last Updated` and any tool-layer notes that changed because of the native tinyagent contract.
  - Keep doc changes limited to developer-facing contract accuracy; do not broaden into unrelated README cleanup.
- Files/modules touched:
  - `docs/modules/tools/tools.md`
  - `docs/modules/core/core.md`
  - `AGENTS.md`
- Acceptance test: `uv run python scripts/check_agents_freshness.py` passes after the doc and metadata updates.

## Risks & Mitigations

- Risk: importing tinyagent result types too deeply into shared layers can create coupling that is hard to unwind later.
- Mitigation: keep native tinyagent types at the contract boundary and use explicit structured fields in canonical data classes instead of passing raw untyped dicts across the codebase.

- Risk: canonical and resume paths drift apart, causing session replay or compaction regressions.
- Mitigation: land T005 as one atomic change set and use round-trip tests that exercise `to_canonical(...)`, `from_canonical(...)`, and resume sanitization assumptions together.

- Risk: partial tool updates create noisy or duplicated UI output.
- Mitigation: define one explicit UI rule in T006: partial updates render as running tool panels, final completion replaces the status/duration path and only final completion triggers file-edit side effects.

- Risk: execution leaves a hidden compatibility fallback in the adapter, preserving the shim the user asked to remove.
- Mitigation: delete the facade modules and legacy tool docs/tests first, then only reintroduce native-tool artifacts that are required by the rebuilt architecture.

## Test Strategy

- T001: verify repository-wide search no longer finds legacy tool facade code or docs references
- T002: extend one tinyagent execution contract test to assert native tool results
- T003: add one registration/conformance test for direct native tools
- T004: add/adjust one registry test for structured completed/failed results
- T005: extend one orchestrator test for `ToolExecutionUpdateEvent`
- T006: add one canonical round-trip test for `details` and `is_error`
- T007: run the focused pytest subset listed in the task acceptance test
- T008: run `uv run python scripts/check_agents_freshness.py`

## References

- Research:
  - `.artifacts/research/2026-03-22_09-45-29_tools-data-inputs-contracts.md`
  - `.artifacts/research/2026-03-22_09-53-07_tool-result-adapter-runtime.md`
  - `.artifacts/research/2026-03-22_09-53-52_minimax-tinyagent-contract-shape-vs-runtime.md`
- External reference:
  - `tinyAgent/examples/minimax_tool_contract_examples.py` — https://github.com/alchemiststudiosDOTai/tinyAgent/blob/master/examples/minimax_tool_contract_examples.py
- Key code references:
  - `src/tunacode/tools/decorators.py:177`
  - `src/tunacode/core/agents/main.py:439`
  - `src/tunacode/core/agents/helpers.py:85`
  - `src/tunacode/utils/messaging/adapter.py:188`
  - `src/tunacode/types/callbacks.py:62`
  - `src/tunacode/ui/repl_support.py:187`
  - `src/tunacode/ui/widgets/messages.py:30`
  - `src/tunacode/core/compaction/summarizer.py:290`
  - `tests/integration/core/test_tinyagent_tool_execution_contract.py:30`
  - `tests/unit/types/test_adapter.py:129`

## Final Gate

- Output summary: plan path `.artifacts/plan/2026-03-22_09-58-20_native-tinyagent-tool-contract.md`, milestones `4`, tasks `8`
- Git state: `4cf456d4`
- Next step: execute-phase using `.artifacts/plan/2026-03-22_09-58-20_native-tinyagent-tool-contract.md`
