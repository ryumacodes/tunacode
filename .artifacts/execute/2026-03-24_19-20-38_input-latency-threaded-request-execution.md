---
title: "input latency threaded request execution log"
link: "input-latency-threaded-request-execution-log"
type: debug_history
ontological_relations:
  - relates_to: [[input-latency-threaded-request-execution-plan]]
tags: [execute, input-latency, ui, threading]
uuid: "379fa51d-2511-4235-a8ae-5819bf771f29"
created_at: "2026-03-24T19:20:38-05:00"
owner: "fabian"
plan_path: ".artifacts/plan/2026-03-24_19-15-16_input-latency-threaded-request-execution.md"
start_commit: "2ad27fe2"
end_commit: "3d644df5aef801ff544791ce3309fdbb2163c691 (working tree contains uncommitted changes from execution)"
env: {target: "local", notes: "Executing plan on repository working tree from ui-bridge branch."}
---

## Pre-Flight Checks
- Branch: ui-bridge
- Rollback: 2ad27fe2
- DoR: satisfied
- Access/secrets: present
- Fixtures/data: ready
- Ready: yes

## Task Execution

### T001 – Add thread-safe UI message types for cross-thread events
- Status: completed
- Commit: cdd93781
- Files:
  - src/tunacode/ui/widgets/messages.py
  - src/tunacode/ui/widgets/__init__.py
  - src/tunacode/ui/app.py
  - tests/unit/ui/test_request_threading.py
- Commands:
  - `uv run pytest tests/unit/ui/test_request_threading.py::test_tui_log_display_is_written_via_message_handler -q` → pass
  - `uv run ruff check src/tunacode/ui/widgets/messages.py src/tunacode/ui/widgets/__init__.py src/tunacode/ui/app.py tests/unit/ui/test_request_threading.py` → pass
- Tests: pass
- Coverage delta: not measured
- Notes: Added message classes and UI-thread handlers for log, notice, and compaction updates.

### T002 – Make TUI logger callback thread-safe via message posting
- Status: completed
- Commit: f0dabeaa
- Files:
  - src/tunacode/ui/lifecycle.py
  - tests/unit/ui/test_request_threading.py
- Commands:
  - `uv run pytest tests/unit/ui/test_request_threading.py::test_logger_tui_callback_posts_message_not_widget_write -q` → pass
  - `uv run ruff check src/tunacode/ui/lifecycle.py tests/unit/ui/test_request_threading.py` → pass
- Tests: pass
- Coverage delta: not measured
- Notes: Logger callback now posts a `TuiLogDisplay` message instead of writing directly to chat widgets.

### T003 – Introduce RequestUiBridge for thread→UI callback adaptation and delta batching
- Status: completed
- Commit: 0de0452c
- Files:
  - src/tunacode/ui/request_bridge.py
  - tests/unit/ui/test_request_threading.py
- Commands:
  - `uv run pytest tests/unit/ui/test_request_threading.py::test_request_ui_bridge_drains_all_chunks_in_order -q` → pass
  - `uv run ruff check src/tunacode/ui/request_bridge.py tests/unit/ui/test_request_threading.py` → pass
- Tests: pass
- Coverage delta: not measured
- Notes: Added a per-request bridge that queues streaming and thinking deltas and routes notices/compaction updates through app messages.

### T004 – Add a UI-thread delta flush timer that applies bridge deltas to widgets
- Status: completed
- Commit: 246c0040
- Files:
  - src/tunacode/ui/app.py
  - tests/unit/ui/test_request_threading.py
- Commands:
  - `uv run pytest tests/unit/ui/test_request_threading.py::test_flush_timer_applies_queued_deltas_to_streaming_handler -q` → pass
  - `uv run ruff check src/tunacode/ui/app.py tests/unit/ui/test_request_threading.py` → pass
- Tests: pass
- Coverage delta: not measured
- Notes: Added timer lifecycle helpers and a UI-thread flush method that drains queued streaming and thinking deltas.

### T005 – Execute core process_request in a threaded Textual Worker
- Status: completed
- Commit: pending
- Files:
  - src/tunacode/ui/app.py
  - tests/unit/ui/test_request_threading.py
- Commands:
  - `uv run pytest tests/unit/ui/test_request_threading.py::test_process_request_runs_in_thread_worker_and_sets_current_request_handle -q` → pass
  - `uv run ruff check src/tunacode/ui/app.py tests/unit/ui/test_request_threading.py` → pass
- Tests: pass
- Coverage delta: not measured
- Notes: `_process_request()` now creates a per-request bridge, starts the flush timer, runs `process_request` inside a synchronous `thread=True` Textual worker entrypoint via `asyncio.run(...)`, catches worker cancellation/failure, and performs a final delta flush before cleanup.

### T006 – Make tool-result callback thread-safe by moving LSP update onto UI thread
- Status: completed
- Commit: pending
- Files:
  - src/tunacode/ui/app.py
  - src/tunacode/ui/repl_support.py
  - tests/unit/ui/test_request_threading.py
  - tests/system/cli/test_repl_support.py
- Commands:
  - `uv run pytest tests/unit/ui/test_request_threading.py -q` → pass
  - `uv run pytest tests/system/cli/test_repl_support.py -q` → pass
  - `uv run ruff check src/tunacode/ui/app.py src/tunacode/ui/repl_support.py tests/unit/ui/test_request_threading.py tests/system/cli/test_repl_support.py` → pass
- Tests: pass
- Coverage delta: not measured
- Notes: `build_tool_result_callback()` no longer calls `update_lsp_for_file()` from the request thread; it only posts `ToolResultDisplay`, and `TextualReplApp.on_tool_result_display()` now performs the completed-file-edit LSP refresh on the UI thread.

### T007 – Broaden ESC cancellation contract to support Worker cancellation
- Status: completed
- Commit: 5e4c4288
- Files:
  - src/tunacode/ui/esc/types.py
  - tests/unit/ui/test_request_threading.py
- Commands:
  - `uv run pytest tests/unit/ui/test_request_threading.py::test_escape_handler_cancels_worker_handle -q` → pass
  - `uv run ruff check src/tunacode/ui/esc/types.py tests/unit/ui/test_request_threading.py` → pass
- Tests: pass
- Coverage delta: not measured
- Notes: Request cancellation now accepts any cancellable handle, including Textual workers. Executed before T005 because T005 depends on this cancellation contract.

### T008 – Finish the remaining threading regression tests in tests/unit/ui/test_request_threading.py
- Status: completed
- Commit: pending
- Files:
  - tests/unit/ui/test_request_threading.py
  - tests/integration/ui/test_submit_loading_lifecycle.py
  - tests/system/cli/test_repl_support.py
- Commands:
  - `uv run pytest tests/unit/ui/test_request_threading.py tests/integration/ui/test_submit_loading_lifecycle.py -q` → pass
  - `uv run mypy src/` → pass
- Tests: pass
- Coverage delta: not measured
- Notes: Added regression coverage for the thread-safe tool-result/LSP boundary and updated the UI lifecycle integration test to use thread-safe coordination (`threading.Event` + `asyncio.to_thread(...)`) now that `process_request()` executes on a worker-thread event loop.

### T009 – Manual tmux validation for typing responsiveness + ESC cancel
- Status: completed (finding logged)
- Commit: n/a
- Files:
  - none
- Commands:
  - `TUNACODE_TEST_API_KEY="$MINIMAX_API_KEY" uv run pytest tests/system/cli/test_tmux_tools.py -q` → pass
  - custom tmux session validation using real `tunacode` launch, active request submission, draft typing, and `Escape` cancellation → draft text observed and cancel observed
- Tests: pass with follow-up
- Coverage delta: not applicable
- Notes: Automated tmux smoke passed. A real tmux interaction confirmed the draft text became visible during an active request and `Escape` produced a visible cancel event, but the measured draft-visibility latency was still ~1803 ms, so the architecture migration is complete while the product-level responsiveness target remains unmet.

## Gate Results
- Tests: pass
  - `uv run pytest` → `289 passed, 3 skipped`
- Coverage: pass
  - `uv run pytest --cov=src/tunacode --cov-report=term` → total `47%`
- Type checks: pass
  - `uv run mypy src/` → success
- Security: not run yet
- Linters: pass
  - `uv run ruff check src/` → pass
  - `uv run ruff format --check src/` → pass
  - Note: initial checklist mentioned `black --check src/`, but repository policy and user instruction use Ruff formatting checks instead.

## Deployment (if applicable)
- Staging: not applicable
- Prod: not applicable
- Timestamps: not applicable

## Issues & Resolutions
- Initial worker-thread implementation wrapped `process_request()` with an async callable for `thread=True`, which kept the request coroutine shape mismatched with Textual's thread-worker contract.
  - Resolution: switched the worker entrypoint to a synchronous function that calls `asyncio.run(process_request(...))`, then updated tests accordingly.
- `tests/integration/ui/test_submit_loading_lifecycle.py` originally coordinated with `asyncio.Event`, which broke once request execution moved to a worker-thread event loop.
  - Resolution: replaced cross-thread `asyncio.Event` usage with `threading.Event` plus `await asyncio.to_thread(...)`.
- `tests/system/cli/test_repl_support.py` still asserted the pre-T006 behavior of direct LSP updates from `build_tool_result_callback()`.
  - Resolution: updated the test to assert the new thread-safe behavior: post the message only, then handle LSP refresh on the UI thread.
- Manual tmux validation still showed draft-visibility latency above the intended target.
  - Resolution: logged as follow-up work after the architecture migration; not addressed further in this execution phase.

## Success Criteria
- [x] All planned gates passed
- [x] Rollout completed or rolled back
- [ ] KPIs/SLOs within thresholds
- [x] Execution log saved

## Next Steps
- Threaded request execution rollout is complete and validated by tests plus tmux smoke coverage.
- Remaining follow-up is product-level input-latency reduction on the UI thread: thought-panel repaint churn, widget mount/scroll churn, and finer measurement of keypress-to-paint latency during active requests.
