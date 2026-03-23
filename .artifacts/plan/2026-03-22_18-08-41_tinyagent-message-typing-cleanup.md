---
title: "tinyagent message typing cleanup implementation plan"
link: "tinyagent-message-typing-cleanup-plan"
type: implementation_plan
ontological_relations:
  - relates_to: [[message-ingress-data-contract-map]]
  - relates_to: [[postmortem-defensive-message-typing-2026-03-17]]
tags: [plan, tinyagent, typing, messaging, coding]
uuid: "d73299c9-b92e-4f21-9c33-7bdc1f359761"
created_at: "2026-03-22T23:08:41Z"
parent_research: ".artifacts/research/2026-03-22_17-57-53_message-ingress-data-contract-map.md"
git_commit_at_plan: "98e94e1e"
---

## Goal

One outcome only:
- remove message-typing indirection from internal runtime code so TunaCode uses tinyagent message models directly in memory and plain dicts only at real boundaries

Out of scope:
- repo-wide `Any` cleanup
- test rewrites
- new abstraction layers
- canonical model redesign
- persistence schema changes

## Locked Decisions

1. Tinyagent is already the source of truth. Use its existing `AgentMessage`, `UserMessage`, `AssistantMessage`, `ToolResultMessage`, `CustomAgentMessage`, and `JsonObject` types directly.
2. Do **not** add `src/tunacode/types/messages.py`, `contracts.py`, or any parallel TunaCode-owned message-contract module.
3. `ConversationState.messages` is an in-memory tinyagent history. Fix typing at that source instead of compensating downstream with `list[Any]`, cast helpers, or wrapper unions.
4. Keep dict payloads only at actual boundaries:
   - session save/load
   - adapter ingress/egress
   - resume-cleanup payload handoff
5. Boundary validation stays. Internal typed flows stay direct.
6. Do not extract a shared deserializer unless the final code is obviously smaller and does not create another layer. Duplicating a short role switch is preferable to another helper.

## Scope & Assumptions

- In scope:
  - `src/tunacode/core/types/state_structures.py`
  - `src/tunacode/core/agents/main.py`
  - `src/tunacode/core/agents/helpers.py`
  - `src/tunacode/core/session/state.py`
  - `src/tunacode/utils/messaging/adapter.py`
  - `src/tunacode/utils/messaging/token_counter.py`
  - `src/tunacode/core/ui_api/messaging.py`
  - any direct callers that break because those signatures become honest
- Out of scope:
  - `resume/sanitize.py` dataclass redesign
  - non-message `Any` cleanup in config, caches, or tool runtime
  - new public APIs
- Assumptions:
  - installed tinyagent already provides the typed message models and `JsonObject`
  - the user will handle broader test fallout separately
  - this pass should remove helpers, not add helpers

## Deliverables

- runtime history typed at the source
- internal serializers stripped of message-only casts and indirection
- adapter/token/UI helper signatures narrowed to the actual supported message shapes
- no new TunaCode-owned message-contract layer
- minimal `AGENTS.md` freshness update if `src/` changes during execution

## Readiness

- `src/tunacode/core/types/state_structures.py:8-17` introduces the runtime `list[Any]` fallback that causes downstream coercion
- `src/tunacode/core/agents/main.py:81-116` serializes/deserializes typed messages but still carries cast-based glue
- `src/tunacode/core/agents/main.py:162-175` re-narrows `conversation.messages` before sending it back to tinyagent
- `src/tunacode/core/agents/helpers.py:75-90` exists mainly to compensate for the degraded history type
- `src/tunacode/core/session/state.py:170-218` is a real persisted-JSON boundary and should stay explicit
- `src/tunacode/utils/messaging/adapter.py:305-318` is a real mixed-input boundary and should stay explicit
- `src/tunacode/utils/messaging/token_counter.py:31-56` and `src/tunacode/core/ui_api/messaging.py:11-23` should mirror the narrowed adapter surface

## Milestones

- M1: Fix the in-memory history type at the source
- M2: Remove internal serializer/history indirection
- M3: Narrow mixed-boundary helpers without adding a new layer
- M4: Clean handoff and metadata update

## Work Breakdown

### T001
- **Summary**: Type `ConversationState.messages` as tinyagent history at the source instead of falling back to `list[Any]`
- **Owner**: JR Dev
- **Estimate**: 45 minutes
- **Dependencies**: none
- **Target milestone**: M1
- **Acceptance check**: `rg -n "MessageHistory = list\\[Any\\]|messages: MessageHistory" src/tunacode/core/types/state_structures.py`
  Expected result: no runtime `list[Any]` alias remains; the field is annotated directly as tinyagent history.
- **Files/modules touched**:
  - `src/tunacode/core/types/state_structures.py`
- **Implementation notes**:
  1. Remove the runtime `MessageHistory = list[Any]` fallback.
  2. Use postponed annotations and the existing tinyagent import pattern; do not add a new local alias module.
  3. Let downstream cleanups happen in later tasks instead of patching around them here.

### T002
- **Summary**: Make the request path consume typed history directly and delete history re-narrowing that only exists because of the old `list[Any]` fallback
- **Owner**: JR Dev
- **Estimate**: 1.5 hours
- **Dependencies**: T001
- **Target milestone**: M2
- **Acceptance check**: `rg -n "coerce_tinyagent_history|replace_messages\\(" src/tunacode/core/agents/main.py src/tunacode/core/agents/helpers.py`
  Expected result: `RequestOrchestrator._run_impl()` passes conversation history directly into tinyagent, and `coerce_tinyagent_history()` is either deleted or reduced to a true boundary-only helper with a real caller.
- **Files/modules touched**:
  - `src/tunacode/core/agents/main.py`
  - `src/tunacode/core/agents/helpers.py`
- **Implementation notes**:
  1. Start at `RequestOrchestrator._run_impl()` in `src/tunacode/core/agents/main.py:162-175`.
  2. If `conversation.messages` is now typed honestly, remove the extra narrowing hop before `agent.replace_messages(...)`.
  3. Delete `coerce_tinyagent_history()` if nothing outside a real boundary needs it.
  4. Do not replace the deleted helper with another helper that just restates the same contract.

### T003
- **Summary**: Simplify internal tinyagent serialization paths without inventing shared contract helpers
- **Owner**: JR Dev
- **Estimate**: 1.5 hours
- **Dependencies**: T001
- **Target milestone**: M2
- **Acceptance check**: `rg -n "cast\\(dict\\[str, (Any|object)\\], message\\.model_dump|types/messages.py|message contract" src/tunacode/core`
  Expected result: no message-serialization casts remain in the core internal paths, and no new message-contract module exists.
- **Files/modules touched**:
  - `src/tunacode/core/agents/main.py`
  - `src/tunacode/core/session/state.py`
- **Implementation notes**:
  1. In `_serialize_agent_messages()` and `StateManager._serialize_messages()`, call `message.model_dump(exclude_none=True)` directly on typed tinyagent models.
  2. Keep `_deserialize_message()` in `state.py` as an explicit persisted-JSON boundary.
  3. Keep `_deserialize_agent_messages()` in `main.py` as an explicit sanitized-dict boundary unless removing it makes the code shorter without moving logic into a new layer.
  4. Do not add a shared `messages.py`, `contracts.py`, or helper module to “centralize” this.

### T004
- **Summary**: Narrow adapter/token/UI helper signatures to the real supported message shapes and stop using `Any` as the public contract
- **Owner**: JR Dev
- **Estimate**: 2 hours
- **Dependencies**: T001, T003
- **Target milestone**: M3
- **Acceptance check**: `rg -n "def (to_canonical|to_canonical_list|get_content|get_tool_call_ids|get_tool_return_ids|find_dangling_tool_calls|estimate_message_tokens|estimate_messages_tokens).*Any|list\\[Any\\]" src/tunacode/utils/messaging src/tunacode/core/ui_api/messaging.py`
  Expected result: public helpers describe the actual supported inputs instead of `Any` / `list[Any]`.
- **Files/modules touched**:
  - `src/tunacode/utils/messaging/adapter.py`
  - `src/tunacode/utils/messaging/token_counter.py`
  - `src/tunacode/core/ui_api/messaging.py`
  - `src/tunacode/ui/headless/output.py` if needed for annotation fallout
- **Implementation notes**:
  1. Supported inputs are:
     - `CanonicalMessage`
     - tinyagent `AgentMessage`
     - tinyagent-style dict payloads at the adapter boundary
  2. Use tinyagent types directly in this file. If a local alias helps readability, define it in the same file and keep it private.
  3. Do not widen support to legacy formats.
  4. Do not add a repo-global union/type wrapper just to name this set once.

### T005
- **Summary**: Remove leftover message-specific casts and stop conditions created by the old typing workaround
- **Owner**: JR Dev
- **Estimate**: 1 hour
- **Dependencies**: T002, T003, T004
- **Target milestone**: M3
- **Acceptance check**: `rg -n "cast\\(AgentMessage|cast\\(UserMessage|cast\\(AssistantMessage|cast\\(ToolResultMessage|cast\\(CustomAgentMessage" src/tunacode/core src/tunacode/utils/messaging`
  Expected result: remaining message casts are only at unavoidable external boundaries; none remain just to placate internal typing.
- **Files/modules touched**:
  - `src/tunacode/core/agents/main.py`
  - `src/tunacode/core/agents/helpers.py`
  - `src/tunacode/utils/messaging/adapter.py`
  - any direct call sites surfaced by the signature cleanup
- **Implementation notes**:
  1. Remove casts that became unnecessary after T001-T004.
  2. If a cast still remains, leave a short code comment only if it marks a real boundary or third-party limitation.
  3. Do not do opportunistic cleanup outside message flow.

### T006
- **Summary**: Finish the source-tree handoff cleanly without expanding scope into tests or unrelated typing work
- **Owner**: JR Dev
- **Estimate**: 15 minutes
- **Dependencies**: T005
- **Target milestone**: M4
- **Acceptance check**: `uv run python scripts/check_agents_freshness.py`
- **Files/modules touched**:
  - `AGENTS.md` only if `src/` changed
- **Implementation notes**:
  1. Update `AGENTS.md` `Last Updated` only because `src/` changed.
  2. If you find unrelated `Any` hotspots during execution, record them as follow-ups. Do not solve them in this task.
  3. Do not spend time rewriting or fixing tests in this pass unless a trivial assertion update is unavoidable to keep the changed code importable.

## Escalate Instead Of Guessing

- Stop and ask if deleting `coerce_tinyagent_history()` reveals a real runtime path that stores non-tinyagent objects in `conversation.messages`.
- Stop and ask if narrowing adapter signatures breaks a caller that truly needs a fourth message shape.
- Stop and ask if simplifying deserialization would require a new shared helper/module just to avoid 10-15 duplicated lines.

## References

- Research: `.artifacts/research/2026-03-22_17-57-53_message-ingress-data-contract-map.md`
- Postmortem: `.artifacts/debug_history/postmortem-defensive-message-typing-2026-03-17.md`
- Current source points:
  - `src/tunacode/core/types/state_structures.py:8-17`
  - `src/tunacode/core/agents/main.py:81-116`
  - `src/tunacode/core/agents/main.py:162-175`
  - `src/tunacode/core/agents/helpers.py:75-90`
  - `src/tunacode/core/session/state.py:170-218`
  - `src/tunacode/utils/messaging/adapter.py:305-318`
  - `src/tunacode/utils/messaging/adapter.py:474-498`
  - `src/tunacode/utils/messaging/token_counter.py:31-56`
  - `src/tunacode/core/ui_api/messaging.py:11-23`
  - `.venv/lib/python3.12/site-packages/tinyagent/agent_types.py:23`
  - `.venv/lib/python3.12/site-packages/tinyagent/agent_types.py:142-209`

## Final Gate

- **Output summary**: one code-focused cleanup plan, 4 milestones, 6 tasks ready
- **Next step**: execute this file directly; do not create a second planning layer to describe it
