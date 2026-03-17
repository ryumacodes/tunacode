# tinyagent typing cleanup report

Date: 2026-03-16

## Bottom line

The `tiny-agent-os` package now ships `tinyagent/py.typed`, but this checkout is not locked to that release yet.

- Repo requirement: `tiny-agent-os>=1.2.7` in `pyproject.toml:31`
- Repo lock: `tiny-agent-os==1.2.7` in `uv.lock:2040`
- Locked wheel date: `2026-03-04`
- Current PyPI release checked: `1.2.9`
- Current wheel date: `2026-03-16`
- `1.2.9` wheel contains `tinyagent/py.typed`
- `1.2.7` wheel does not contain `tinyagent/py.typed`

That means the cleanup is justified, but it should be described as:

1. Upgrade-gated for static type checker benefits.
2. Focused on internal typed paths, not on JSON or provider/runtime boundaries.

## Main finding

The clearest cleanup target is `src/tunacode/ui/main.py:265`.

Current code:

- `_serialize_message(msg: object) -> dict[str, object]`
- Checks `isinstance(msg, UserMessage | AssistantMessage | ToolResultMessage | CustomAgentMessage)`
- Calls `msg.model_dump(exclude_none=True)`
- Then checks that the result is a `dict`

Why this looks removable after a bump to `1.2.9+`:

- This path is called from `src/tunacode/ui/main.py:178`, where it serializes `conversation.messages`.
- `ConversationState.messages` is type-checked as `list[AgentMessage]` in `src/tunacode/core/types/state_structures.py:15`.
- The published `tinyagent.agent_types` module already defines a typed `ModelDumpable` protocol and a `dump_model_dumpable(...)` helper.

Conclusion:

- `src/tunacode/ui/main.py:265` is the best candidate to simplify first.
- Once the lockfile is on a `py.typed` release, the explicit message-union guard and the post-`model_dump` `dict` check look like defensive leftovers more than necessary application logic.

## Secondary candidate

`src/tunacode/core/agents/helpers.py:58`:

- `coerce_tinyagent_history(messages: list[Any]) -> list[AgentMessage]`
- Verifies every message is one of the four tinyagent message models, then casts

Why this is only a secondary candidate:

- `src/tunacode/core/agents/main.py:198` uses it on `conversation.messages`.
- `ConversationState.messages` is statically typed, but intentionally becomes `list[Any]` at runtime in `src/tunacode/core/types/state_structures.py:15-17`.

Conclusion:

- This helper exists partly because of TunaCode's own runtime `Any` boundary, not only because tinyagent lacked `py.typed`.
- It can be reconsidered, but it is not as clear-cut a removal as the `ui/main.py` serializer.

## Defensive logic that should stay

These sites are still real boundary validation, even if tinyagent is fully typed.

### `src/tunacode/core/session/state.py:181`

`_serialize_messages()` and `_deserialize_message()` validate:

- in-memory session contents before persistence
- raw JSON before rehydration
- role-based message reconstruction via `model_validate(...)`

Reason to keep:

- This is a persistence boundary.
- `py.typed` does not protect persisted JSON or corrupted runtime state.

### `src/tunacode/utils/messaging/adapter.py:250`

`_coerce_agent_message_dict(message: Any)` accepts either:

- a raw `dict`
- or a tinyagent message model

Reason to keep:

- This is intentionally a mixed boundary adapter.
- Runtime type discrimination is part of the function's job.

### `src/tunacode/core/agents/main.py:348`

`_normalize_event_args(...)` rejects non-dict tool args.

Reason to keep:

- Tool-call event payloads are runtime data from the agent stream.

### `src/tunacode/core/agents/main.py:499`

The run-end handler checks that the emitted message is an `AssistantMessage`.

Reason to keep:

- Event payload narrowing is still valid runtime protection.

### `src/tunacode/core/agents/main.py:723`

The message-update handler ignores empty or non-string deltas.

Reason to keep:

- Streaming payloads are runtime/provider data, not a purely static path.

## What changed, precisely

The important change is not "tinyagent is typed now" in the abstract. The important change is:

1. The published package now advertises typing to external type checkers via `py.typed`.
2. TunaCode can rely more directly on tinyagent model types in internal code once the lockfile consumes that release.

What did not change:

- runtime JSON validation needs
- stream/provider payload uncertainty
- TunaCode's own `Any` escape hatches, especially `ConversationState.messages` at runtime

## Recommendation

1. Bump the lockfile to a `tiny-agent-os` release that includes `py.typed`.
2. Simplify `src/tunacode/ui/main.py:265` first.
3. Re-evaluate `src/tunacode/core/agents/helpers.py:58` after that.
4. Keep the boundary checks in `core/session/state.py`, `utils/messaging/adapter.py`, and `core/agents/main.py`.

## Source notes

Local code reviewed:

- `src/tunacode/ui/main.py`
- `src/tunacode/core/agents/helpers.py`
- `src/tunacode/core/session/state.py`
- `src/tunacode/utils/messaging/adapter.py`
- `src/tunacode/core/agents/main.py`
- `src/tunacode/core/types/state_structures.py`
- `pyproject.toml`
- `uv.lock`

Upstream package evidence:

- PyPI JSON: `https://pypi.org/pypi/tiny-agent-os/json`
- Locked wheel from `uv.lock`: `https://files.pythonhosted.org/packages/4d/0f/092855203861b5c7ae603648b116658e33ef3a35f6e9c45f06eb8712360c/tiny_agent_os-1.2.7-cp310-abi3-manylinux_2_34_x86_64.whl`
