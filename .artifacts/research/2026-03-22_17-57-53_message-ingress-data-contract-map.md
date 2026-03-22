---
title: "message ingress and data contract map research findings"
link: "message-ingress-data-contract-map"
type: research
ontological_relations:
  - relates_to: [[tools-data-inputs-contracts]]
  - relates_to: [[agent-message-serialization]]
tags: [research, message-flow, input-contracts]
uuid: "7E7690C0-DF9A-4A7C-9193-9EC6A5FE6744"
created_at: "2026-03-22T22:57:53Z"
---

## Structure
- `src/tunacode/ui/` contains the Textual request entrypoint and the headless CLI entrypoint.
- `src/tunacode/core/agents/` contains request orchestration, tinyagent handoff, abort cleanup, and resume sanitization.
- `src/tunacode/core/session/` contains session persistence and restore.
- `src/tunacode/utils/messaging/` contains canonical message adapters.
- `src/tunacode/types/canonical.py` contains the canonical message dataclasses.
- `.venv/lib/python3.12/site-packages/tinyagent/` contains the first `str -> UserMessage` conversion and the runtime message store.

## Key Files
- `src/tunacode/ui/app.py:330` -> `TextualReplApp.on_editor_submit_requested()`
- `src/tunacode/ui/repl_support.py:119` -> `normalize_agent_message_text()`
- `src/tunacode/ui/main.py:193` -> `run_headless(prompt: str)`
- `src/tunacode/core/agents/main.py:667` -> `process_request(message: str, ...)`
- `src/tunacode/core/agents/main.py:162` -> `RequestOrchestrator._run_impl()`
- `src/tunacode/core/agents/main.py:586` -> `RequestOrchestrator._run_stream()`
- `.venv/lib/python3.12/site-packages/tinyagent/agent.py:400` -> `Agent._build_input_messages()`
- `.venv/lib/python3.12/site-packages/tinyagent/agent.py:462` -> `Agent.stream()`
- `.venv/lib/python3.12/site-packages/tinyagent/agent_types.py:496` -> `AgentState.messages`
- `src/tunacode/core/agents/main.py:305` -> `_persist_agent_messages()`
- `src/tunacode/core/types/state_structures.py:15` -> `MessageHistory = list[AgentMessage]` under `TYPE_CHECKING`
- `src/tunacode/core/types/state_structures.py:17` -> `MessageHistory = list[Any]` at runtime
- `src/tunacode/core/session/state.py:170` -> `_serialize_messages()`
- `src/tunacode/core/session/state.py:176` -> `_deserialize_message()`
- `src/tunacode/core/session/state.py:319` -> `save_session()`
- `src/tunacode/core/session/state.py:348` -> `load_session()`
- `src/tunacode/utils/messaging/adapter.py:318` -> `to_canonical()`
- `src/tunacode/utils/messaging/adapter.py:445` -> `from_canonical()`
- `src/tunacode/core/agents/resume/sanitize.py:60` -> sanitize-specific resume message dataclasses
- `src/tunacode/core/agents/resume/sanitize.py:182` -> `_parse_message()`
- `src/tunacode/core/agents/resume/sanitize.py:442` -> `run_cleanup_loop()`

## Data Flow
### Textual UI ingress
1. `EditorSubmitRequested.text` enters at `src/tunacode/ui/app.py:330`.
2. `handle_command(self, message.text)` runs at `src/tunacode/ui/app.py:333`.
3. Non-command input is normalized by `normalize_agent_message_text(message.text)` at `src/tunacode/ui/app.py:335`.
4. `normalize_agent_message_text()` resolves `@path` mentions against `cwd` at `src/tunacode/ui/repl_support.py:119`.
5. The normalized string is queued with `request_queue.put(normalized_message)` at `src/tunacode/ui/app.py:336`.
6. `_request_worker()` dequeues the string and calls `_process_request(request)` at `src/tunacode/ui/app.py:213` and `src/tunacode/ui/app.py:217`.
7. `_process_request()` calls `process_request(message=message, ...)` at `src/tunacode/ui/app.py:255`.

### Headless CLI ingress
1. CLI input enters as `prompt: str` at `src/tunacode/ui/main.py:193`.
2. `run_headless()` calls `process_request(message=prompt, ...)` at `src/tunacode/ui/main.py:222`.

### Core orchestration
1. `process_request(message: str, ...)` is the public core entry point at `src/tunacode/core/agents/main.py:667`.
2. `RequestOrchestrator._run_impl()` reads existing `session.conversation.messages` at `src/tunacode/core/agents/main.py:167`.
3. Existing history is passed through `coerce_tinyagent_history(conversation.messages)` at `src/tunacode/core/agents/main.py:170` and `src/tunacode/core/agents/helpers.py:79`.
4. Existing history is loaded into tinyagent with `agent.replace_messages(compacted_history)` at `src/tunacode/core/agents/main.py:175`.
5. The new request string is handed to tinyagent with `agent.stream(self.message)` at `src/tunacode/core/agents/main.py:604`.

### First structured message object
1. tinyagent `Agent.stream()` accepts `input_data: str | AgentMessage | list[AgentMessage]` at `.venv/lib/python3.12/site-packages/tinyagent/agent.py:462`.
2. `Agent._build_input_messages()` converts a `str` into `[UserMessage(content=[TextContent(text=input_data)], ...)]` at `.venv/lib/python3.12/site-packages/tinyagent/agent.py:400`.
3. `UserMessage` is defined in `.venv/lib/python3.12/site-packages/tinyagent/agent_types.py:142`.

### Runtime message storage
1. tinyagent runtime state stores `messages: list[AgentMessage]` in `AgentState` at `.venv/lib/python3.12/site-packages/tinyagent/agent_types.py:496`.
2. `Agent.replace_messages()` writes `self._state.messages = messages.copy()` at `.venv/lib/python3.12/site-packages/tinyagent/agent.py:354`.
3. `Agent.append_message()` writes `self._state.messages = [*self._state.messages, message]` at `.venv/lib/python3.12/site-packages/tinyagent/agent.py:357`.
4. `_handle_agent_event()` dispatches event handlers at `.venv/lib/python3.12/site-packages/tinyagent/agent.py:141`.
5. `_on_message_end()` appends completed messages with `append_message(event.message)` at `.venv/lib/python3.12/site-packages/tinyagent/agent.py:55`.
6. TunaCode copies `agent.state.messages` into `session.conversation.messages` in `_persist_agent_messages()` at `src/tunacode/core/agents/main.py:305`.
7. `ConversationState.messages` is declared as `MessageHistory` at `src/tunacode/core/types/state_structures.py:43`.
8. `MessageHistory` is `list[AgentMessage]` under `TYPE_CHECKING` and `list[Any]` at runtime at `src/tunacode/core/types/state_structures.py:8`.

### Persistence boundary
1. `StateManager._serialize_messages()` converts in-memory message models to `list[dict[str, Any]]` with `model_dump(exclude_none=True)` at `src/tunacode/core/session/state.py:170`.
2. `save_session()` writes those dicts under `"messages"` in `session_data` at `src/tunacode/core/session/state.py:319`.
3. `load_session()` reads `"messages"` from disk at `src/tunacode/core/session/state.py:348`.
4. `_deserialize_messages()` rebuilds tinyagent message models by role at `src/tunacode/core/session/state.py:176`.
5. Loaded models are assigned to `self._session.conversation.messages` at `src/tunacode/core/session/state.py:401`.

### Canonical adapter boundary
1. `MessageRole`, part dataclasses, and `CanonicalMessage` are defined in `src/tunacode/types/canonical.py:23` and `src/tunacode/types/canonical.py:151`.
2. `adapter.to_canonical()` accepts dicts, tinyagent models, or `CanonicalMessage` at `src/tunacode/utils/messaging/adapter.py:318`.
3. `_coerce_agent_message_dict()` converts dict/model input to `dict[str, Any]` at `src/tunacode/utils/messaging/adapter.py:305`.
4. `adapter.from_canonical()` converts `CanonicalMessage` back to tinyagent-style dicts at `src/tunacode/utils/messaging/adapter.py:445`.

### Abort and resume cleanup boundary
1. Abort cleanup serializes live `AgentMessage` objects with `_serialize_agent_messages()` at `src/tunacode/core/agents/main.py:81`.
2. `_handle_abort_cleanup()` runs `_sanitize_conversation_after_abort()` after `_persist_agent_messages()` at `src/tunacode/core/agents/main.py:644`.
3. `sanitize.py` defines `UserResumeMessage`, `SystemResumeMessage`, `AssistantResumeMessage`, and `ToolResultResumeMessage` at `src/tunacode/core/agents/resume/sanitize.py:60`.
4. `_parse_message()` first calls `adapter.to_canonical(raw_message)` and then reparses the same input into `ResumeMessage` dataclasses at `src/tunacode/core/agents/resume/sanitize.py:182`.
5. `run_cleanup_loop()` operates on `messages: list[object]`, mutates `messages[:]`, and serializes back to `list[dict[str, object]]` at `src/tunacode/core/agents/resume/sanitize.py:442`.
6. `_deserialize_agent_messages()` converts sanitized dicts back into tinyagent message models at `src/tunacode/core/agents/main.py:88`.

## Patterns Found
- Raw user input enters TunaCode as `str` in both Textual UI and headless CLI paths.
- The first `UserMessage` object is constructed inside tinyagent.
- Runtime conversation history is mirrored between `agent.state.messages` and `session.conversation.messages`.
- Session persistence stores message history as JSON dicts.
- The canonical adapter projects message data into `CanonicalMessage` and back into dicts.
- Resume cleanup projects message data into sanitize-specific dataclasses and back into dicts.

## Dependencies
- `src/tunacode/ui/app.py` imports `process_request` from `src/tunacode/core/agents/main.py` at `src/tunacode/ui/app.py:252`.
- `src/tunacode/ui/main.py` imports `process_request` from `src/tunacode/core/agents/main.py` at `src/tunacode/ui/main.py:209`.
- `src/tunacode/core/agents/main.py` imports `Agent`, `AgentMessage`, `UserMessage`, `AssistantMessage`, and `ToolResultMessage` from tinyagent at `src/tunacode/core/agents/main.py:10`.
- `src/tunacode/core/session/state.py` imports tinyagent message classes for role-based deserialization at `src/tunacode/core/session/state.py:177`.
- `src/tunacode/core/agents/resume/sanitize.py` imports `adapter` from `src/tunacode/utils/messaging/adapter.py` at `src/tunacode/core/agents/resume/sanitize.py:10`.
- `src/tunacode/utils/messaging/adapter.py` imports `CanonicalMessage` and related part types from `src/tunacode/types/canonical.py` at `src/tunacode/utils/messaging/adapter.py:23`.

## Symbol Index
- `src/tunacode/ui/main.py:193` -> `run_headless`
- `src/tunacode/ui/app.py:239` -> `TextualReplApp._process_request`
- `src/tunacode/ui/app.py:330` -> `TextualReplApp.on_editor_submit_requested`
- `src/tunacode/ui/repl_support.py:119` -> `normalize_agent_message_text`
- `src/tunacode/core/agents/main.py:667` -> `process_request`
- `src/tunacode/core/agents/main.py:81` -> `_serialize_agent_messages`
- `src/tunacode/core/agents/main.py:88` -> `_deserialize_agent_messages`
- `src/tunacode/core/agents/main.py:305` -> `_persist_agent_messages`
- `src/tunacode/core/agents/helpers.py:79` -> `coerce_tinyagent_history`
- `src/tunacode/core/session/state.py:170` -> `_serialize_messages`
- `src/tunacode/core/session/state.py:176` -> `_deserialize_message`
- `src/tunacode/core/session/state.py:319` -> `save_session`
- `src/tunacode/core/session/state.py:348` -> `load_session`
- `src/tunacode/utils/messaging/adapter.py:318` -> `to_canonical`
- `src/tunacode/utils/messaging/adapter.py:445` -> `from_canonical`
- `src/tunacode/core/agents/resume/sanitize.py:182` -> `_parse_message`
- `src/tunacode/core/agents/resume/sanitize.py:442` -> `run_cleanup_loop`
- `.venv/lib/python3.12/site-packages/tinyagent/agent.py:400` -> `Agent._build_input_messages`
- `.venv/lib/python3.12/site-packages/tinyagent/agent.py:462` -> `Agent.stream`
- `.venv/lib/python3.12/site-packages/tinyagent/agent_types.py:496` -> `AgentState`
