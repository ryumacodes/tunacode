---
title: Agent Message Serialization Pattern
summary: Documents the three type systems for agent messages (tinyagent, canonical, sanitize), how data flows from user input through to the agent loop, and why the serialization roundtrips are a smell.
read_when:
  - Modifying agent message handling
  - Working on abort/resume logic
  - Reviewing type boundary violations
  - Understanding message type ownership
depends_on:
  - src/tunacode/core/agents/main.py
  - src/tunacode/core/agents/resume/sanitize.py
  - src/tunacode/utils/messaging/adapter.py
  - src/tunacode/types/canonical.py
feeds_into:
  - docs/modules/core/core.md
---

## The Problem: Three Type Systems for One Concept

The codebase has **three different type systems** representing the same domain concept (agent messages):

| Type System | Location | Types | Format |
|-------------|----------|-------|--------|
| **tinyagent** | `tinyagent` package | `AgentMessage`, `UserMessage`, `AssistantMessage`, `ToolResultMessage` | Pydantic models |
| **canonical** | `src/tunacode/types/canonical.py` | `CanonicalMessage`, `CanonicalPart` | Dataclasses |
| **sanitize** | `src/tunacode/core/agents/resume/sanitize.py` | `UserResumeMessage`, `AssistantResumeMessage`, `ToolResultResumeMessage` | Dataclasses |

All three communicate via raw **dicts** as the intermediate serialization format.

## Data Flow: From User Input to Agent

```
1. USER INPUT (UI/Repl)
   Raw text string
           ↓
2. session.conversation.messages
   Type: list[AgentMessage] (static) / list[Any] (runtime per typed.md)
   Source: session.add_message() or similar
           ↓
3. coerce_tinyagent_history() in helpers.py:79
   Validates all messages are AgentMessage types
   Has cast() at line 85: [cast(AgentMessage, message) for message in ...]
           ↓
           ├──────────────────┬─────────────────────┐
           ↓                  ↓                     ↓
   (normal flow)       (ABORT path)          (ADAPTER path)
           ↓                  ↓                     ↓
4a. agent.stream()    4b. _serialize_         4c. adapter.to_canonical()
   (tinyagent)          agent_messages()        → CanonicalMessage
                          → dicts                 (for utilities)
```

## The Three Conversion Points

### Point 1: coerce_tinyagent_history() — helpers.py:79

```python
def coerce_tinyagent_history(messages: Iterable[object]) -> list[AgentMessage]:
    if all(is_tinyagent_message(message) for message in message_list):
        return [cast(AgentMessage, message) for message in message_list]
```

**Smell**: The `cast()` assumes all messages are already `AgentMessage`. No validation, no conversion. If a non-tinyagent message sneaks in, it's a runtime crash.

### Point 2: _serialize_agent_messages() — main.py:81

```python
def _serialize_agent_messages(messages: list[AgentMessage]) -> list[object]:
    for message in messages:
        serialized_messages.append(
            cast(dict[str, object], message.model_dump(exclude_none=True))
        )
```

**Smell**: The `cast()` hides the fact that `model_dump()` returns `dict[str, Any]`, not `dict[str, object]`. The cast is a lie about precision.

### Point 3: adapter.to_canonical() — adapter.py:318

```python
def _coerce_agent_message_dict(message: Any) -> dict[str, Any]:
    if isinstance(message, dict):
        return cast(dict[str, Any], message)

    if not isinstance(message, UserMessage | AssistantMessage | ...):
        raise TypeError(...)

    return cast(dict[str, Any], message.model_dump(exclude_none=True))
```

**Smell**: The adapter accepts `Any` and uses `cast()` to claim dict shapes. No actual schema enforcement.

## The Abort Path Flow

When a user aborts, the message history goes through a complex roundtrip:

```
AgentMessage (Pydantic)
    ↓ _serialize_agent_messages() + model_dump()
dict (plain) ──────────────────────────────┐
    ↓                                       ↓
sanitize._parse_message()                  adapter.to_canonical()
    ↓                                       ↓
ResumeMessage (dataclass)              CanonicalMessage (dataclass)
    ↓ _remove_dangling_tool_calls()         (separate path)
    ↓ _remove_empty_responses()            for utilities only
    ↓ _remove_consecutive_requests()
    ↓ _serialize_message()
dict (plain)
    ↓ _deserialize_agent_messages()
AgentMessage (Pydantic)
    ↓ _persist_agent_messages()
session.conversation.messages
```

The `cast()` doesn't fix anything — it just silences mypy while the runtime behavior is controlled by the dict structure, not the cast.

## Root Cause: Who Owns the Message Schema?

No single module owns the message schema. Instead:

| Module | Owns | Trusts |
|--------|------|--------|
| `tinyagent` | `AgentMessage` schema | — |
| `adapter.py` | `CanonicalMessage` schema | dict shape from anywhere |
| `sanitize.py` | `ResumeMessage` schema | dict shape from caller |
| `main.py` | Orchestration | All of the above |

This creates a trust chain with no validation:
```
tinyagent model → dict → sanitize → dict → tinyagent model
         ↓
      adapter → dict → canonical
```

## The cast() Pattern is a Type Lie

All three conversion points share the same anti-pattern:

```python
cast(dict[str, object], some_dict)  # Says it's dict[str, object]
# But dict[str, object] ≠ dict[str, Any]
```

`cast()` tells mypy "trust me, this is the right type" without any runtime validation. It:
- Silences type errors without fixing them
- Hides schema drift between type systems
- Makes refactoring dangerous — mypy won't catch mismatches

## Refactoring Direction

1. **Pick one canonical type**: Either `AgentMessage`, `CanonicalMessage`, or `ResumeMessage`
2. **Single serialization boundary**: Session persistence only
3. **Remove the other two**: Eliminate conversion code paths
4. **Validate at boundaries**: Not with `cast()`, but with actual schema validation (e.g., `model_validate`)

## See Also

- `src/tunacode/core/agents/helpers.py` — coerce_tinyagent_history with cast()
- `src/tunacode/utils/messaging/adapter.py` — Canonical conversion with cast()
- `src/tunacode/types/canonical.py` — Canonical message types
- `typed.md` — Runtime vs static typing notes for conversation.messages
- `docs/modules/tools/hashline-subsystem.md` — Another serialization pattern in codebase
