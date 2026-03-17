---
title: "replace_messages cutover research findings"
link: "replace_messages-cutover-research"
type: research
ontological_relations:
  - relates_to: [[REQUEST_CONTEXT_CUTOVER_LESSON]]
  - relates_to: [[CODE-STANDARDS]]
tags: [research, replace_messages, tinyagent]
uuid: "f77c4111-2640-4fc1-8ee7-2b92246808dc"
created_at: "2026-03-17T18:01:09.462024+00:00"
---

## Structure
- `src/tunacode/core/agents/`
  - `main.py` contains `RequestOrchestrator` request loop and tinyagent stream handling.
  - `agent_components/agent_config.py` contains cached `Agent` factory (`get_or_create_agent`).
- `src/tunacode/ui/`
  - `app.py` contains TUI request worker and request task creation.
  - `main.py` contains headless `run` command and request task creation.
- `.venv/lib/python3.13/site-packages/tinyagent/`
  - `agent.py` contains the installed runtime `Agent` API used by TunaCode.
- `uv.lock`
  - lockfile contains resolved `tiny-agent-os` version.

## Key Files
- `src/tunacode/core/agents/main.py:L95-L98` → `_coerce_max_iterations(session)` reads `session.user_config["settings"]["max_iterations"]` and returns `int(...)`.
- `src/tunacode/core/agents/main.py:L188-L215` → `_run_impl()` prepares history, compaction, then calls `agent.replace_messages(compacted_history)` at `L201`.
- `src/tunacode/core/agents/main.py:L266-L291` → overflow retry path calls `agent.replace_messages(forced_history)` at `L285` before retry stream.
- `src/tunacode/core/agents/main.py:L649-L669` → exported async `process_request(...)` entrypoint.
- `src/tunacode/core/agents/agent_components/agent_config.py:L478-L539` → `get_or_create_agent(...)` returns cached or newly constructed `tinyagent.agent.Agent`.
- `src/tunacode/ui/app.py:L239-L268` → TUI `_process_request(...)` creates task for `process_request(...)`.
- `src/tunacode/ui/main.py:L193-L233` → headless `run_headless(...)` creates task for `process_request(...)`.
- `.venv/lib/python3.13/site-packages/tinyagent/agent.py:L91-L188` → installed `Agent` class and methods (`state`, `clear_messages`, `reset`).
- `.venv/lib/python3.13/site-packages/tinyagent/agent.py:L280-L370` → `stream(...)` uses `messages=self._state.messages.copy()` in loop context.
- `uv.lock:L2040-L2042` (HEAD) → locked package `tiny-agent-os` is `1.2.10`.

### Historical snapshots (git)
- `src/tunacode/core/agents/main.py@3f8dea1a:L239-L241` → first tinyagent stream-era usage: `history = ...`, `agent.replace_messages(history)`.
- `src/tunacode/core/agents/main.py@9c903606:L357` → compaction-pre-stream `agent.replace_messages(compacted_history)`.
- `src/tunacode/core/agents/main.py@9c903606:L481` → overflow-retry `agent.replace_messages(forced_history)`.
- `src/tunacode/core/agents/main.py@3f8dea1a^:L246` → pre-tinyagent flow used `agent.iter(..., message_history=message_history)` (history passed per-run, no `replace_messages`).
- `uv.lock@9c903606:L1938-L1940` → locked `tiny-agent-os` was `1.1.0`.
- `uv.lock@7375c01c:L1938-L1940` → locked `tiny-agent-os` was `1.1.5`.

## Patterns Found
- **Pattern: history loaded into agent state before stream**
  - `src/tunacode/core/agents/main.py:L201`
  - `src/tunacode/core/agents/main.py:L285`
  - `src/tunacode/core/agents/main.py@3f8dea1a:L240`
- **Pattern: stream loop reads state messages as context source**
  - `.venv/lib/python3.13/site-packages/tinyagent/agent.py:L365-L369`
- **Pattern: same request API used by TUI and headless**
  - `src/tunacode/ui/app.py:L252-L267`
  - `src/tunacode/ui/main.py:L209-L230`
- **Pattern: session-scoped cached agent reused by model/version**
  - `src/tunacode/core/agents/agent_components/agent_config.py:L494-L499`
  - `src/tunacode/core/agents/agent_components/agent_config.py:L538-L539`
- **Pattern: API surface drift in tiny-agent-os across versions (runtime check)**
  - `tiny-agent-os==1.1.5` runtime check: `Agent` has `replace_messages`.
  - `tiny-agent-os==1.2.10` runtime check: `Agent` does not have `replace_messages`.
  - Installed runtime file in repo venv (`.venv/.../tinyagent/agent.py`) has `clear_messages`/`stream` but no `replace_messages` definition.

## Dependencies
- `src/tunacode/ui/app.py` → imports → `tunacode.core.agents.main.process_request`
  - Import location: `src/tunacode/ui/app.py:L252`
  - Call location: `src/tunacode/ui/app.py:L255-L267`
- `src/tunacode/ui/main.py` → imports → `tunacode.core.agents.main.process_request`
  - Import location: `src/tunacode/ui/main.py:L209`
  - Call location: `src/tunacode/ui/main.py:L222-L230`
- `src/tunacode/core/agents/main.py` → imports → `tinyagent.agent.Agent`
  - Import location: `src/tunacode/core/agents/main.py:L11`
- `src/tunacode/core/agents/main.py` → uses → `agent_components.get_or_create_agent`
  - Import location: `src/tunacode/core/agents/main.py:L63`
  - Use location: `src/tunacode/core/agents/main.py:L195`
- `src/tunacode/core/agents/agent_components/agent_config.py` → imports → `tinyagent.agent.Agent`
  - Import location: `src/tunacode/core/agents/agent_components/agent_config.py:L16`
  - Construction location: `src/tunacode/core/agents/agent_components/agent_config.py:L525-L532`

## Symbol Index
- `src/tunacode/core/agents/main.py:L95` → `_coerce_max_iterations(session: SessionStateProtocol) -> int`
- `src/tunacode/core/agents/main.py:L145` → `class RequestOrchestrator`
- `src/tunacode/core/agents/main.py:L188` → `_run_impl(self) -> Agent`
- `src/tunacode/core/agents/main.py:L568` → `_run_stream(self, *, agent: Agent, max_iterations: int, baseline_message_count: int) -> Agent`
- `src/tunacode/core/agents/main.py:L644` → `get_agent_tool() -> tuple[type[Agent], type[object]]`
- `src/tunacode/core/agents/main.py:L649` → `process_request(...) -> Agent`
- `src/tunacode/core/agents/agent_components/agent_config.py:L478` → `get_or_create_agent(model, state_manager) -> Agent`
- `.venv/lib/python3.13/site-packages/tinyagent/agent.py:L91` → `class Agent`
- `.venv/lib/python3.13/site-packages/tinyagent/agent.py:L177` → `clear_messages(self) -> None`
- `.venv/lib/python3.13/site-packages/tinyagent/agent.py:L280` → `stream(self, input_data, images=None) -> AsyncIterator[AgentEvent]`
- `.venv/lib/python3.13/site-packages/tinyagent/agent.py:L323` → `continue_(self) -> AgentMessage`

## Reproduction Commands Used
- `uv run mypy src/tunacode/core/agents/main.py`
- `git log --oneline -S"replace_messages" -- src/tunacode/core/agents/main.py`
- `git show <rev> -- src/tunacode/core/agents/main.py`
- `uv run python -c "from tinyagent.agent import Agent; print(hasattr(Agent,'replace_messages'))"`
- `uv run --with tiny-agent-os==1.1.5 python -c "from tinyagent.agent import Agent; print(hasattr(Agent,'replace_messages'))"`
- `uv run --with tiny-agent-os==1.2.10 python -c "from tinyagent.agent import Agent; print(hasattr(Agent,'replace_messages'))"`
