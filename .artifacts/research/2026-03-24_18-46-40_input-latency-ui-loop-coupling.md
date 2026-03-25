---
title: "input latency (UI/request loop coupling) research findings"
link: "input-latency-ui-loop-coupling-research"
type: research
ontological_relations:
  - relates_to: [[docs/reviews/2026-03-24-input-latency-research-artifact]]
tags: [research, ui, textual, input-latency, streaming]
uuid: "EFA242E7-8248-4568-AF21-BB254B9811DB"
created_at: "2026-03-24T18:46:44-0500"
---

## Structure
- UI entry point is the Textual `App` subclass `TextualReplApp` in `src/tunacode/ui/app.py:84-641`.
- App startup/lifecycle logic is `AppLifecycle` in `src/tunacode/ui/lifecycle.py:19-152`.
- Request execution orchestration is `RequestOrchestrator` (and `process_request`) in `src/tunacode/core/agents/main.py:111-680`.
- Streaming output widget state is managed by `StreamingHandler` in `src/tunacode/ui/streaming.py:12-34`.
- “Thinking” panel state is managed by functions in `src/tunacode/ui/thinking_state.py:12-87`.
- Tool result UI updates are routed through Textual `Message` objects (`ToolResultDisplay`) defined in `src/tunacode/ui/widgets/messages.py:30-49` and handled by `TextualReplApp.on_tool_result_display()` in `src/tunacode/ui/app.py:361-386`.
- Chat history rendering/mounting is implemented by `ChatContainer` in `src/tunacode/ui/widgets/chat.py:224-322`.

## Key Files
- `src/tunacode/ui/lifecycle.py:78-96` → `AppLifecycle._start_repl()` sets focus to `app.editor` (`:87`) and starts the background request worker via `app.run_worker(app._request_worker, exclusive=False)` (`:88`).
- `src/tunacode/ui/app.py:113-147` → `TextualReplApp.__init__()` constructs the request queue `self.request_queue: asyncio.Queue[str] = asyncio.Queue()` (`:123`).
- `src/tunacode/ui/app.py:149-181` → `TextualReplApp.compose()` mounts the main viewport widgets including:
  - `ChatContainer(id="chat-container", auto_scroll=True)` (`:151`)
  - `LoadingIndicator()` (`:154`)
  - `Static("", id="streaming-output")` and `StreamingHandler(...)` (`:152-153`)
  - `Editor()` (`:155`)
- `src/tunacode/ui/app.py:214-225` → `_request_worker()` awaits `self.request_queue.get()` (`:216`) and awaits `_process_request(request)` (`:218`).
- `src/tunacode/ui/app.py:255-317` → `_process_request()` imports `process_request` (`:267`), creates an asyncio task (`:270-282`), and awaits it (`:283`). The task is constructed with UI callbacks:
  - `streaming_callback=self.streaming.callback` (`:275` when enabled)
  - `thinking_callback=self._thinking_callback` (`:276`)
  - `tool_result_callback=build_tool_result_callback(self)` (`:277`)
  - `notice_callback=self._show_system_notice` (`:279`)
  - `compaction_status_callback=self._update_compaction_status` (`:280`)
- `src/tunacode/core/agents/main.py:577-615` → `RequestOrchestrator._run_stream()` iterates `async for event in agent.stream(self.message)` (`:595`) and dispatches each event via `_dispatch_stream_event(...)` (`:596-603`).
- `src/tunacode/core/agents/main.py:617-633` → `_handle_message_update()` awaits UI-provided callbacks:
  - awaits `self.streaming_callback(assistant_event.delta)` for `text_delta` (`:628-629`)
  - awaits `self.thinking_callback(assistant_event.delta)` for `thinking_delta` (`:632-633`)
- `src/tunacode/ui/streaming.py:19-28` → `StreamingHandler.callback()` accumulates text and calls `self._output.update(self._text)` (`:28`) when the throttle is satisfied (`:25-27`).
- `src/tunacode/ui/thinking_state.py:40-73` → `refresh_thinking_output()` mounts or updates the thinking panel in the chat:
  - mounts via `app.chat_container.write(...)` when first rendered (`:65-70`)
  - updates existing widget via `thinking_panel_widget.update(...)` (`:72`)
  - calls `app.chat_container.scroll_end(animate=False)` (`:73`)
- `src/tunacode/ui/repl_support.py:203-237` → `build_tool_result_callback()` constructs a sync callback which posts a `ToolResultDisplay(...)` message (`:227-235`) via `app.post_message(...)` (`:226`).
- `src/tunacode/ui/app.py:361-386` → `on_tool_result_display()` renders the tool panel via `tool_panel_smart(...)` and writes it into the chat with `self.chat_container.write(...)` (`:374`).
- `src/tunacode/ui/widgets/chat.py:262-306` → `ChatContainer.write()` mounts a new `CopyOnSelectStatic` widget (`self.mount(widget)` at `:301`) and auto-scrolls (`self.scroll_end(animate=False)` at `:304`) when `_auto_scroll` is enabled.
- `src/tunacode/ui/lifecycle.py:122-133` → `AppLifecycle._setup_logger()` installs a TUI logger callback that calls `app.chat_container.write(renderable)` (`:131`).

## Request / UI Update Flow (call chain)
1. Editor submit:
   - `Editor.action_submit()` posts `EditorSubmitRequested(...)` via `self.post_message(...)` in `src/tunacode/ui/widgets/editor.py:116-128`.
2. App receives submit:
   - `TextualReplApp.on_editor_submit_requested()` formats the user message and writes it to the chat container in `src/tunacode/ui/app.py:344-359`, then queues the request via `_queue_request_after_refresh()` (`:359`).
   - `_queue_request_after_refresh()` uses `self.call_after_refresh(lambda: self.request_queue.put_nowait(message))` in `src/tunacode/ui/app.py:252-253`.
3. Request worker consumes queue:
   - `_request_worker()` awaits `self.request_queue.get()` and then awaits `_process_request(request)` in `src/tunacode/ui/app.py:214-225`.
4. Core request orchestration runs with injected UI callbacks:
   - `_process_request()` creates and awaits a task running `tunacode.core.agents.main.process_request(...)` in `src/tunacode/ui/app.py:255-317`.
   - `process_request()` constructs `RequestOrchestrator(...)` and awaits `orchestrator.run()` in `src/tunacode/core/agents/main.py:658-680`.
5. Streaming/thinking deltas invoke UI callbacks during the stream loop:
   - `RequestOrchestrator._run_stream()` iterates stream events (`src/tunacode/core/agents/main.py:577-615`).
   - Per `MessageUpdateEvent`, `RequestOrchestrator._handle_message_update()` awaits `streaming_callback`/`thinking_callback` (`src/tunacode/core/agents/main.py:617-633`).
6. Tool execution events invoke tool result callbacks:
   - Tool execution updates/end events invoke `self.tool_result_callback(...)` in `src/tunacode/core/agents/main.py:430-473` (`:466-471`) and `:475-502` (`:495-500`).
   - The UI tool result callback posts a `ToolResultDisplay` message (`src/tunacode/ui/repl_support.py:203-237`), which is handled by `TextualReplApp.on_tool_result_display()` to mount a tool panel into the chat container (`src/tunacode/ui/app.py:361-386`).

## Patterns Found (locations)
- Request work starts from the UI lifecycle:
  - `AppLifecycle._start_repl()` calls `run_worker(app._request_worker, exclusive=False)` in `src/tunacode/ui/lifecycle.py:78-96` (call at `:88`).
- UI directly awaits an in-process async request task:
  - `TextualReplApp._process_request()` awaits `self._current_request_task` in `src/tunacode/ui/app.py:255-317` (`await` at `:283`).
- Core orchestrator awaits UI callbacks per streaming delta:
  - `await self.streaming_callback(...)` and `await self.thinking_callback(...)` in `src/tunacode/core/agents/main.py:617-633` (`:629`, `:633`).
- UI callbacks mutate widgets:
  - `Static.update(...)` for streaming output in `src/tunacode/ui/streaming.py:19-28`.
  - `ChatContainer.write(...)` and `ChatContainer.scroll_end(...)` for thinking output in `src/tunacode/ui/thinking_state.py:40-73`.
  - `ChatContainer.write(...)` for tool panels in `src/tunacode/ui/app.py:361-386`.
- Chat writes mount new widgets and auto-scroll when enabled:
  - `ChatContainer(id=..., auto_scroll=True)` created in `src/tunacode/ui/app.py:149-181` (`:151`).
  - `ChatContainer.write()` mounts + scrolls in `src/tunacode/ui/widgets/chat.py:262-306` (`:301-304`).

## Dependencies (import + callback wiring)
- UI → Core request execution:
  - `src/tunacode/ui/app.py:255-317` imports `process_request` from `tunacode.core.agents.main` (`:267`) and passes UI callbacks into it (`:271-281`).
- Core → callback type contracts:
  - `src/tunacode/core/agents/main.py:42-49` imports `NoticeCallback`, `StreamingCallback`, `ToolResultCallback`, and `ToolStartCallback` from `tunacode.types` and stores them on `RequestOrchestrator` (`src/tunacode/core/agents/main.py:114-136`).
- UI tool callback wiring:
  - `src/tunacode/ui/repl_support.py:19-27` imports `ToolResultCallback` (via `tunacode.core.ui_api.shared_types`) and returns a callable that posts `ToolResultDisplay` messages (`src/tunacode/ui/repl_support.py:203-237`).

## Symbol Index (selected)
- `src/tunacode/ui/lifecycle.py:19-152` → `class AppLifecycle`
  - `_start_repl()` `src/tunacode/ui/lifecycle.py:78-96`
  - `_setup_logger()` `src/tunacode/ui/lifecycle.py:122-133`
- `src/tunacode/ui/app.py:84-641` → `class TextualReplApp`
  - `compose()` `src/tunacode/ui/app.py:149-181`
  - `_request_worker()` `src/tunacode/ui/app.py:214-225`
  - `_process_request()` `src/tunacode/ui/app.py:255-317`
  - `on_tool_result_display()` `src/tunacode/ui/app.py:361-386`
  - `_thinking_callback()` `src/tunacode/ui/app.py:631-634`
- `src/tunacode/core/agents/main.py:111-650` → `class RequestOrchestrator`
  - `_run_stream()` `src/tunacode/core/agents/main.py:577-615`
  - `_handle_message_update()` `src/tunacode/core/agents/main.py:617-633`
- `src/tunacode/core/agents/main.py:658-680` → `async def process_request(...)`
- `src/tunacode/ui/streaming.py:12-34` → `class StreamingHandler` (`callback()` at `:19-28`)
- `src/tunacode/ui/thinking_state.py:12-87` → thinking panel functions (`thinking_callback()` at `:76-87`)
- `src/tunacode/ui/repl_support.py:203-237` → `def build_tool_result_callback(...)`
- `src/tunacode/ui/widgets/messages.py:30-49` → `class ToolResultDisplay(Message)`
- `src/tunacode/ui/widgets/chat.py:224-322` → `class ChatContainer` (`write()` at `:262-306`)
- `src/tunacode/ui/widgets/editor.py:38-398` → `class Editor` (`action_submit()` at `:116-128`)
- `src/tunacode/types/callbacks.py:63-70` → `ToolResultCallback` and `StreamingCallback` type aliases (with `StreamingCallback = Callable[[str], Awaitable[None]]` at `:70`).
