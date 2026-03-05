---
title: Tighten tool adapter to typed AgentToolResult/TextContent
type: delta
link: tool-adapter-typed-agenttoolresult
path:
  - src/tunacode/tools/decorators.py
  - src/tunacode/core/agents/agent_components/agent_config.py
  - src/tunacode/core/agents/helpers.py
  - tests/unit/tools/test_tinyagent_tool_adapter.py
  - tests/unit/core/test_tool_concurrency_limit.py
  - tests/integration/core/test_tinyagent_tool_execution_contract.py
depth: 2
seams: [M]
ontological_relations:
  - affects: [[tunacode-tools]]
  - affects: [[tinyagent-tool-contracts]]
  - affects: [[tool-lifecycle]]
  - affects: [[tests]]
tags:
  - tinyagent
  - typing
  - tools
  - agenttoolresult
  - tests
created_at: 2026-03-04T21:28:27Z
updated_at: 2026-03-04T21:28:27Z
uuid: 5cc6f574-c1ee-484d-b518-cc0c5775ccfa
---

# Tighten tool adapter to typed AgentToolResult/TextContent

## Summary

Completed the strict-typing cleanup for the tinyagent tool adapter path:

- Tool execution now produces **typed** `AgentToolResult` payloads containing `TextContent` objects (no dict shims).
- Legacy “silent coercions” (e.g. `None` -> empty result) were removed in favor of fail-fast errors.

## Runtime changes

### `src/tunacode/tools/decorators.py`

- `to_tinyagent_tool(...).execute(...)` now matches the typed tinyagent contract:
  - `args: JsonObject`
  - `on_update: AgentToolUpdateCallback`
- Tool functions are treated as **`str`-returning**; non-`str` results raise `ToolExecutionError`.
- Adapter always returns `AgentToolResult(content=[TextContent(text=...)], details={})`.
- Removed obsolete result coercions (`AgentToolResult` passthrough, `None` -> empty output, dict content blocks).

### `src/tunacode/core/agents/agent_components/agent_config.py`

- Concurrency-limit wrapper now uses the same typed execute signature (`JsonObject` + `AgentToolUpdateCallback`) to avoid “Any” widening.

### `src/tunacode/core/agents/helpers.py`

- `extract_tool_result_text(...)` now accepts `AgentToolResult | None` and extracts only from `TextContent` (removed dict/getattr fallbacks).

## Test updates / harness coverage

- Updated unit tests to assert `TextContent` objects rather than dict content.
- Added an offline integration harness test covering `tinyagent.execute_tool_calls(...)`:
  - verifies typed `ToolExecutionStartEvent`/`ToolExecutionEndEvent` + `MessageStartEvent`/`MessageEndEvent`
  - verifies typed `ToolResultMessage.content` and `AgentToolResult.content`.

## Validation

- `uv run ruff check .` ✅
- `uv run pytest` ✅ (full suite)
