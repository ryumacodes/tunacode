# Agents Typed Map

Date: 2026-03-16
Branch: `any-cleanup`

## Scope

This note maps the remaining typing debt under `src/tunacode/core/agents` only.

It does not propose code in this pass. It is an inventory built from:

```bash
uv run mypy src/tunacode/core/agents --show-error-codes --hide-error-context --no-error-summary
```

## Snapshot

- Total reported errors in `core/agents`: `350`
- Files with errors: `7`
- Files without reported errors: `3`
- Dominant pattern: `Any` propagation, not missing imports or missing symbols

Top error kinds:

- `182` x `Expression has type "Any"  [misc]`
- `42` x `Expression type contains "Any" (has type "list[Any]")  [misc]`
- `35` x `Expression type contains "Any" (has type "dict[str, Any]")  [misc]`
- `28` x `Explicit "Any" is not allowed  [explicit-any]`
- `8` x `Expression type contains "Any" (has type "Any | None")  [misc]`

Non-`Any` spillover that still matters:

- `4` `arg-type` errors at `agent_components/agent_config.py:430` from `OpenAICompatModel(**model_kwargs)`
- `1` `no-any-return` in `main.py:120`
- `1` `var-annotated` in `main.py:167`

## File Map

### Highest-density files

- `src/tunacode/core/agents/resume/sanitize.py`: `114`
  - This is the largest typing hotspot.
  - The whole module models resumed history as raw `list[Any]` and `dict[str, Any]`.
  - Error clusters start at `_coerce_message_dict()` (`:59`), `_get_content_items()` (`:72`), `_filter_assistant_tool_calls()` (`:107`), `remove_dangling_tool_calls()` (`:168`), `remove_empty_responses()` (`:223`), `remove_consecutive_requests()` (`:259`), and `sanitize_history_for_resume()` (`:303`).
  - Root cause: persisted tinyagent JSON is treated as ad hoc dict/list payloads through the whole cleanup pipeline.

- `src/tunacode/core/agents/main.py`: `107`
  - This is the main runtime orchestration hotspot.
  - Error density starts early around `_TinyAgentStreamState` (`:92`), `EmptyResponseHandler` (`:100`), and `RequestOrchestrator` (`:139`).
  - High-friction areas:
    - untyped `user_config` / `settings` access in `RequestOrchestrator.__init__`
    - history flow around `conversation.messages`
    - event and tool-arg normalization around `_normalize_event_args()` (`:348`)
    - broad `Any` usage in abort cleanup at `_handle_abort_cleanup()` (`:742`)
    - reflective helper `get_agent_tool() -> tuple[type[Any], type[Any]]` (`:761`)
  - Root cause: session/runtime structures still expose several `Any` escape hatches, and the stream/event path leans on dynamic payload handling.

- `src/tunacode/core/agents/agent_components/agent_config.py`: `60`
  - This file is mostly config plumbing plus dynamic agent construction.
  - Error clusters are concentrated in:
    - `_compute_agent_version()` (`:116`) using `settings: dict[str, Any]`
    - `_resolve_base_url()` (`:284`) and `_build_api_key_resolver()` (`:319`) reading untyped `session.user_config`
    - `_build_tools()` (`:257`) and tool wrapper typing around `_wrap_tool_with_concurrency_limit()` (`:217`)
    - `_build_tinyagent_model()` (`:404`) and the `OpenAICompatModel(**model_kwargs)` call at `:430`
    - `get_or_create_agent()` (`:470`) interacting with `session.agents` and `session.agent_versions`
  - Root cause: dynamic config dicts, dynamic keyword assembly, and session caches typed too loosely.

### Secondary files

- `src/tunacode/core/agents/resume/sanitize_debug.py`: `25`
  - The debug logger is built on `messages: list[Any]` and free-form content items.
  - Errors come from `Any`-typed preview helpers and raw dict access during logging.
  - Root cause: it mirrors the same untyped resume-history shape as `resume/sanitize.py`.

- `src/tunacode/core/agents/agent_components/state_transition.py`: `22`
  - This file has no explicit `Any`, but `mypy` still sees `Any` leakage because the state machine is parameterized with generic `Enum` rather than the concrete `AgentState`.
  - Affected surfaces are `StateTransitionRules.valid_transitions`, `transition_to()`, `can_transition_to()`, and the `AGENT_TRANSITION_RULES` constant.
  - Root cause: overly generic enum typing for a concrete state machine.

- `src/tunacode/core/agents/agent_components/agent_helpers.py`: `16`
  - Tool-description helpers accept `dict[str, Any]` and `handle_empty_response()` takes `state: Any`.
  - Root cause: helper APIs are shaped around loose tool-arg/state objects rather than narrow protocols or typed mappings.

- `src/tunacode/core/agents/helpers.py`: `6`
  - Small file, but important because it sits on a major boundary.
  - The remaining debt is almost entirely `coerce_tinyagent_history(messages: list[Any]) -> list[AgentMessage]` (`:58`).
  - Root cause: conversation history still reaches this helper as `list[Any]` at runtime.

## Clean Files

These files had no reported issues in the scoped `mypy` run:

- `src/tunacode/core/agents/__init__.py`
- `src/tunacode/core/agents/resume/__init__.py`
- `src/tunacode/core/agents/agent_components/__init__.py`

## Recurring Root Causes

### 1. Resume history is still treated as raw JSON

The `resume/` path is dominated by:

- `list[Any]`
- `dict[str, Any]`
- `cast(dict[str, Any], ...)`
- repeated `.get(...)` access on unknown dict payloads

This is the single biggest concentration of remaining `Any` debt.

### 2. Session config is still effectively untyped at the call sites

Several agent paths read:

- `session.user_config`
- `session.user_config.get("settings", {})`
- `session.user_config.get("env", {})`

Even when the enclosing protocol is typed, the values retrieved from these dicts still degrade into `Any`.

### 3. Session caches and service handles are typed too loosely

The agent layer still depends on dynamic session fields such as:

- `session.agents`
- logger/state callback objects
- runtime/event helper state

That keeps `Any` alive even when the tinyagent message types are now typed.

### 4. Dynamic kwargs and reflection still bypass type precision

Two obvious examples:

- `OpenAICompatModel(**model_kwargs)` in `agent_config.py:430`
- `get_agent_tool() -> tuple[type[Any], type[Any]]` in `main.py:761`

These are narrow hotspots, but they block a clean `mypy` pass.

### 5. Concrete state machines are modeled with generic enums

`state_transition.py` is conceptually concrete, but the type surface is generic enough that `Any` leaks into transition checks and constant definitions.

## Suggested Cleanup Order

This is the order that appears most leverage-efficient based on the current map:

1. `resume/sanitize.py`
   - Largest error source.
   - Most of the debt is localized to one representation problem: raw resumed message payloads.

2. `resume/sanitize_debug.py`
   - Should follow immediately after `resume/sanitize.py` because it mirrors the same payload shape.

3. `agent_components/agent_config.py`
   - Next largest self-contained cluster.
   - Also contains the only non-`Any` type mismatch cluster (`OpenAICompatModel(**model_kwargs)`).

4. `main.py`
   - Large surface area.
   - Best tackled after the upstream helper/config boundaries are narrowed.

5. `agent_components/agent_helpers.py` and `helpers.py`
   - Small files.
   - Better cleaned after the surrounding state and history types are tightened.

6. `agent_components/state_transition.py`
   - Mechanically smaller.
   - Can likely be closed out once the concrete state types are made explicit.

## Bottom Line

The repo is not fully typed under `core/agents` yet.

The remaining debt is not spread evenly. It is concentrated in three places:

- raw resumed message JSON in `resume/sanitize.py`
- dynamic session/config plumbing in `agent_components/agent_config.py`
- orchestration/runtime state in `main.py`

If those three areas are tightened, most of the remaining `Any` fallout in `/agents` should collapse with them.
