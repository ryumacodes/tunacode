---
title: "input latency (threaded request execution) implementation plan"
link: "input-latency-threaded-request-execution-plan"
type: implementation_plan
ontological_relations:
  - relates_to: [[input-latency-ui-loop-coupling-research]]
  - relates_to: [[docs/reviews/2026-03-24-input-latency-research-artifact]]
tags: [plan, ui, textual, input-latency, threading]
uuid: "A4A5CC00-BAD7-4219-BD28-17934C9C0CD4"
created_at: "2026-03-24T19:15:22-0500"
parent_research: ".artifacts/research/2026-03-24_18-46-40_input-latency-ui-loop-coupling.md"
git_commit_at_plan: "2def2098"
---

## Goal

- Make editor typing immediately responsive while a request is running by moving request execution (core agent stream + tools) off the Textual UI event loop and batching UI updates back onto the UI thread.

## Scope & Assumptions

- IN scope:
  - Run `tunacode.core.agents.main.process_request()` in a Textual `Worker` with `thread=True`.
  - Replace direct UI-mutation callbacks (streaming/thinking/notice/compaction/tool-result side effects/logging) with thread-safe adapters that only enqueue/post messages.
  - Batch-apply streaming & thinking deltas on the UI thread at a fixed interval.
  - Keep ESC cancellation working (cancel the current request worker).
  - Add targeted unit tests + a manual tmux reproduction check.
- OUT of scope:
  - Rewriting the Editor widget, CSS, or Rich rendering.
  - Changing core agent streaming semantics or tool execution model.
  - Provider/prompt performance optimizations unrelated to UI-loop contention.
- Assumptions:
  - Textual in this repo supports `App.run_worker(..., thread=True)` for coroutine work.
  - `App.post_message(...)` is thread-safe (Textual uses `loop.call_soon_threadsafe` when needed).
  - UI may read `state_manager.session` while the request thread mutates it; if races appear, follow-up work will add locking/snapshots.

## Deliverables

- New UI bridge module for thread-safe callbacks + delta queues.
- UI message types + handlers for thread→UI routing (logger + notices + compaction status).
- Updated request execution pipeline in `TextualReplApp._process_request()` using a threaded Worker.
- Tool-result callback made thread-safe (no UI widget mutation inside request thread).
- Unit tests proving threading wiring + cancellation + message routing.

## Readiness

- Preconditions:
  - Repo passes architecture tests after changes (`tests/test_dependency_layers.py`, `tests/architecture/*`).
  - Thread-worker execution of a coroutine is validated via unit test (M4).
- Git state at plan time:
  - commit: `2def2098`
  - status: untracked research artifacts present in `.artifacts/` and `docs/reviews/` (no local modifications).

## Milestones

- M1: Thread-safe UI event surfaces (messages + logger + cancellable-handle typing)
- M2: Request UI bridge (delta queues + batching) and callback adapters
- M3: Threaded request execution wiring + tool-result callback fix
- M4: Tests + manual perf validation

## Work Breakdown (Tasks)

### Task T001: Add thread-safe UI message types for cross-thread events

**Summary**: Add Textual `Message` classes for logger output, system notices, and compaction status changes, plus handlers on `TextualReplApp`.

- **Owner**: dev
- **Estimate**: 1–2h
- **Dependencies**: none
- **Target milestone**: M1

**Changes**:
1. In `src/tunacode/ui/widgets/messages.py`, add:
   - `class TuiLogDisplay(Message)` with `renderable: RenderableType`
   - `class SystemNoticeDisplay(Message)` with `notice: str`
   - `class CompactionStatusChanged(Message)` with `active: bool`
2. In `src/tunacode/ui/app.py`, implement handlers:
   - `on_tui_log_display(self, message: TuiLogDisplay) -> None` → `self.chat_container.write(message.renderable)`
   - `on_system_notice_display(self, message: SystemNoticeDisplay) -> None` → call existing `_show_system_notice(message.notice)`
   - `on_compaction_status_changed(self, message: CompactionStatusChanged) -> None` → call existing `_update_compaction_status(message.active)`

**Acceptance test**:
- `uv run pytest tests/unit/ui/test_request_threading.py::test_tui_log_display_is_written_via_message_handler -q`

**Files/modules touched**:
- `src/tunacode/ui/widgets/messages.py`
- `src/tunacode/ui/app.py`
- `tests/unit/ui/test_request_threading.py` (new)

### Task T002: Make TUI logger callback thread-safe via message posting

**Summary**: Ensure core debug logs can be emitted from a request thread without directly mutating UI widgets.

- **Owner**: dev
- **Estimate**: 30–60m
- **Dependencies**: T001
- **Target milestone**: M1

**Changes**:
1. In `src/tunacode/ui/lifecycle.py:_setup_logger`, change `write_tui(renderable)` to:
   - `app.post_message(TuiLogDisplay(renderable=renderable))`
2. Confirm no direct `chat_container.write(...)` happens inside the logger callback.

**Acceptance test**:
- `uv run pytest tests/unit/ui/test_request_threading.py::test_logger_tui_callback_posts_message_not_widget_write -q`

**Files/modules touched**:
- `src/tunacode/ui/lifecycle.py`
- `tests/unit/ui/test_request_threading.py`

### Task T003: Introduce RequestUiBridge for thread→UI callback adaptation and delta batching

**Summary**: Create a per-request bridge that provides thread-safe callbacks for core and exposes drain methods for the UI to flush deltas.

- **Owner**: dev
- **Estimate**: 2–3h
- **Dependencies**: T001
- **Target milestone**: M2

**Changes**:
1. Create `src/tunacode/ui/request_bridge.py` with:
   - Thread-safe `queue.SimpleQueue[str]` for `text_delta` and `thinking_delta`.
   - `async def streaming_callback(delta: str) -> None` → `put_nowait(delta)`
   - `async def thinking_callback(delta: str) -> None` → `put_nowait(delta)`
   - `def notice_callback(notice: str) -> None` → `app.post_message(SystemNoticeDisplay(notice=notice))`
   - `def compaction_status_callback(active: bool) -> None` → `app.post_message(CompactionStatusChanged(active=active))`
   - `def drain_streaming() -> str` and `def drain_thinking() -> str` (join all queued chunks).
2. Add a docstring noting: callbacks must not raise; UI mutation happens only in app flush.

**Acceptance test**:
- `uv run pytest tests/unit/ui/test_request_threading.py::test_request_ui_bridge_drains_all_chunks_in_order -q`

**Files/modules touched**:
- `src/tunacode/ui/request_bridge.py` (new)
- `tests/unit/ui/test_request_threading.py`

### Task T004: Add a UI-thread delta flush timer that applies bridge deltas to widgets

**Summary**: Batch-apply streaming/thinking deltas on the UI thread at a controlled cadence.

- **Owner**: dev
- **Estimate**: 2–3h
- **Dependencies**: T003
- **Target milestone**: M2

**Changes**:
1. In `src/tunacode/ui/app.py` add attributes:
   - `self._request_bridge: RequestUiBridge | None = None`
   - `self._delta_flush_timer: Timer | None = None`
2. Add methods:
   - `_start_delta_flush_timer()` → `self.set_interval(self.STREAM_THROTTLE_MS / 1000.0, self._flush_request_deltas)`
   - `_stop_delta_flush_timer()` → stops timer and clears ref
   - `async def _flush_request_deltas(self) -> None`:
     - If no bridge: return
     - `stream_chunk = bridge.drain_streaming()` → if non-empty: `await self.streaming.callback(stream_chunk)`
     - `thinking_chunk = bridge.drain_thinking()` → if non-empty: `await self._thinking_callback(thinking_chunk)`
3. Ensure `_clear_thinking_state()` and `self.streaming.reset()` happen after a final flush when request completes.

**Acceptance test**:
- `uv run pytest tests/unit/ui/test_request_threading.py::test_flush_timer_applies_queued_deltas_to_streaming_handler -q`

**Files/modules touched**:
- `src/tunacode/ui/app.py`
- `tests/unit/ui/test_request_threading.py`

### Task T005: Execute core process_request in a threaded Textual Worker

**Summary**: Move request execution off the UI event loop by running `process_request()` inside a Textual `Worker(thread=True)`.

- **Owner**: dev
- **Estimate**: 3–5h
- **Dependencies**: T003, T004, T007
- **Target milestone**: M3

**Changes**:
1. In `src/tunacode/ui/app.py:_process_request`:
   - Instantiate `bridge = RequestUiBridge(self)` and set `self._request_bridge = bridge`.
   - Start flush timer at request start.
   - Replace `asyncio.create_task(process_request(...))` with:
     - `worker = self.run_worker(lambda: process_request(...callbacks...), thread=True, exit_on_error=False, name="process_request")`
     - Store `self._current_request_task = worker`
     - `await worker.wait()`
   - Pass callbacks:
     - `streaming_callback = bridge.streaming_callback if should_stream_agent_text else None`
     - `thinking_callback = bridge.thinking_callback`
     - `notice_callback = bridge.notice_callback`
     - `compaction_status_callback = bridge.compaction_status_callback`
     - `tool_result_callback = build_tool_result_callback(self)` (made thread-safe in T006)
2. Error handling:
   - Catch `textual.worker.WorkerCancelled` → `self.notify("Cancelled")`
   - Catch `textual.worker.WorkerFailed` → render exception to chat (same renderer as today)
3. In `finally`:
   - Final `await self._flush_request_deltas()` before resetting streaming/thinking.
   - Stop flush timer, clear bridge, clear `_current_request_task`.

**Acceptance test**:
- `uv run pytest tests/unit/ui/test_request_threading.py::test_process_request_runs_in_thread_worker_and_sets_current_request_handle -q`

**Files/modules touched**:
- `src/tunacode/ui/app.py`
- `src/tunacode/ui/request_bridge.py`
- `tests/unit/ui/test_request_threading.py`

### Task T006: Make tool-result callback safe to run from request thread

**Summary**: Remove UI widget mutation from `build_tool_result_callback` so it can be called from the threaded request worker.

- **Owner**: dev
- **Estimate**: 1–2h
- **Dependencies**: T005
- **Target milestone**: M3

**Changes**:
1. In `src/tunacode/ui/repl_support.py:build_tool_result_callback`:
   - Remove `app.update_lsp_for_file(...)` call.
   - Update `AppForCallbacks` Protocol to remove `update_lsp_for_file` requirement.
   - Keep only logic to filter validation errors and `app.post_message(ToolResultDisplay(...))`.
2. In `src/tunacode/ui/app.py:on_tool_result_display`:
   - When `message.status == "completed"` and tool name in `FILE_EDIT_TOOLS`, extract `filepath` and call `self.update_lsp_for_file(filepath)` on the UI thread (alongside existing `_edited_files` update).

**Acceptance test**:
- `uv run pytest tests/unit/ui/test_request_threading.py::test_tool_result_callback_never_calls_update_lsp_for_file_from_request_thread -q`

**Files/modules touched**:
- `src/tunacode/ui/repl_support.py`
- `src/tunacode/ui/app.py`
- `tests/unit/ui/test_request_threading.py`

### Task T007: Broaden ESC cancellation contract to support Worker cancellation

**Summary**: Allow ESC handler to cancel either an `asyncio.Task` (old) or a Textual `Worker` (new threaded request path).

- **Owner**: dev
- **Estimate**: 30–60m
- **Dependencies**: none
- **Target milestone**: M1

**Changes**:
1. In `src/tunacode/ui/esc/types.py`, replace `RequestTask = asyncio.Task[object]` with a `Protocol`:
   - `class Cancellable(Protocol):
       def cancel(self) -> None: ...`
   - `RequestTask: TypeAlias = Cancellable`
2. Keep `EscHandler.handle_escape()` logic the same (`current_request_task.cancel()`).

**Acceptance test**:
- `uv run pytest tests/unit/ui/test_request_threading.py::test_escape_handler_cancels_worker_handle -q`

**Files/modules touched**:
- `src/tunacode/ui/esc/types.py`
- `tests/unit/ui/test_request_threading.py`

### Task T008: Add unit tests for threaded request execution and thread-safe UI routing

**Summary**: Add a compact test suite that prevents regressions on the threading boundary.

- **Owner**: dev
- **Estimate**: 2–4h
- **Dependencies**: T001–T007
- **Target milestone**: M4

**Changes**:
1. Create `tests/unit/ui/test_request_threading.py` with fakes/mocks for:
   - `TextualReplApp.run_worker` returning a fake Worker with `.wait()` coroutine + `.cancel()`
   - `chat_container.write` spy
   - `post_message` spy for logger + notice messages
2. Add the tests referenced by acceptance criteria above (T001–T007).

**Acceptance test**:
- `uv run pytest tests/unit/ui/test_request_threading.py -q`

**Files/modules touched**:
- `tests/unit/ui/test_request_threading.py` (new)

### Task T009: Manual tmux regression validation (real-world feel)

**Summary**: Validate the product-level acceptance criterion using the known tmux reproduction steps from the research artifact.

- **Owner**: dev
- **Estimate**: 30–60m
- **Dependencies**: T005, T006
- **Target milestone**: M4

**Changes**:
1. Run TunaCode in tmux and reproduce:
   - Submit a real prompt.
   - While request is active (stream/tool), type a new draft and confirm characters echo immediately.
2. Validate ESC cancels the threaded request promptly.

**Acceptance test**:
- Manual: follow “Real-World Reproduction” in `docs/reviews/2026-03-24-input-latency-research-artifact.md` and confirm no visible input delay (>100ms) while request active.

**Files/modules touched**:
- none (verification-only)

## Risks & Mitigations

- **Thread-affinity violations (UI mutation from request thread)**: Mitigate by routing *all* UI mutations through `post_message` or the UI flush timer. Audit callbacks (`build_tool_result_callback`, logger callback) specifically.
- **Worker cancellation semantics differ from asyncio.Task**: Mitigate by using Textual `Worker.cancel()` and catching `WorkerCancelled` in `_process_request`.
- **StateManager thread safety**: Initial implementation relies on GIL for basic safety; if races occur, add a follow-up plan for explicit locking or read-only snapshots for UI.
- **Queue growth if UI can't keep up**: Flush at fixed interval; if memory grows, add max-size/backpressure later (follow-up).

## Test Strategy

- Unit tests:
  - Ensure `process_request` is run with `thread=True` worker.
  - Ensure logger/tool callbacks do not directly mutate UI from request thread.
  - Ensure ESC cancels worker handle.
- Manual tmux check:
  - Confirm the visible “typing lag” is gone under real request load.

## References

- Research map: `.artifacts/research/2026-03-24_18-46-40_input-latency-ui-loop-coupling.md`
  - Worker startup: `src/tunacode/ui/lifecycle.py:78-96`
  - Request queue/processing: `src/tunacode/ui/app.py:214-317`
  - Stream loop + awaited callbacks: `src/tunacode/core/agents/main.py:577-633`
  - UI mutation points: `src/tunacode/ui/streaming.py:19-28`, `src/tunacode/ui/thinking_state.py:40-73`, `src/tunacode/ui/widgets/chat.py:262-306`
- Product acceptance criterion + reproduction: `docs/reviews/2026-03-24-input-latency-research-artifact.md`

## Final Gate

- **Output summary**:
  - Plan path: `.artifacts/plan/2026-03-24_19-15-16_input-latency-threaded-request-execution.md`
  - Milestones: 4
  - Tasks: 9
- **Next step**:
  - Proceed to execute-phase using this plan path.
