---
title: "tui submit latency research findings"
link: "tui-submit-latency-research"
type: research
ontological_relations:
  - relates_to: [[docs/modules/ui/ui]]
  - relates_to: [[docs/modules/ui/commands]]
  - relates_to: [[docs/modules/core/core]]
tags: [research, tui-submit-latency]
uuid: "e9401373-0e79-414f-9614-c8cecc6d40c3"
created_at: "2026-03-24T16:58:32-05:00"
---

## Structure
- `src/tunacode/ui/widgets/editor.py` — editor submit action and input rendering.
- `src/tunacode/ui/app.py` — submit event handler, request queue, request worker, final agent panel render.
- `src/tunacode/ui/streaming.py` — throttled incremental streaming renderer.
- `src/tunacode/ui/lifecycle.py` — REPL startup, worker startup, ready-file emission for tmux tests.
- `src/tunacode/core/agents/main.py` — request orchestration, compaction call, agent stream loop, request-complete timing log.
- `src/tunacode/core/agents/agent_components/agent_config.py` — per-request agent lookup/build, skills prompt assembly, AGENTS.md context load, stream function creation.
- `src/tunacode/skills/registry.py` / `src/tunacode/skills/selection.py` — available-skill enumeration and selected-skill loading.
- `src/tunacode/infrastructure/cache/caches/tunacode_context.py` / `src/tunacode/infrastructure/cache/caches/skills.py` — mtime caches used by AGENTS.md context and skills.
- `src/tunacode/configuration/defaults.py` — default `stream_agent_text`, `request_delay`, timeout settings.
- `tests/system/cli/test_tmux_tools.py` — tmux-backed TUI startup/prompt integration path.
- `scripts/startup_timer.py` / `scripts/ui_import_timer.py` — repository timing utilities present for startup/import measurement.

## Key Files
- `src/tunacode/ui/widgets/editor.py:L116-L128` → `Editor.action_submit()` builds submission, posts `EditorSubmitRequested`, clears the input widget.
- `src/tunacode/ui/widgets/editor.py:L376-L390` → `_build_submission()` returns trimmed typed text or paste-buffer content.
- `src/tunacode/ui/app.py:L214-L225` → `_request_worker()` consumes `request_queue` and calls `_process_request()`.
- `src/tunacode/ui/app.py:L227-L238` → `_should_stream_agent_text()` reads `settings.stream_agent_text`.
- `src/tunacode/ui/app.py:L240-L269` → `_process_request()` sets `_request_start_time`, removes streaming CSS class, clears insertion anchor, enables loading state via `self.loading_indicator.add_class("active")`, and calls `core.agents.main.process_request(...)`.
- `src/tunacode/ui/app.py:L251-L253` → streaming callback is `self.streaming.callback` only when `stream_agent_text` is true; otherwise `None` is passed.
- `src/tunacode/ui/app.py:L277-L304` → after request completion, streaming state is reset, latest assistant text is extracted, final agent panel is rendered, resource bar is updated, and session is saved.
- `src/tunacode/ui/app.py:L331-L340` → `on_editor_submit_requested()` routes slash/shell commands, enqueues normal agent input, then writes the user message block to chat.
- `src/tunacode/ui/streaming.py:L19-L29` → `StreamingHandler.callback()` appends chunks and updates the widget on first chunk or after throttle interval.
- `src/tunacode/ui/lifecycle.py:L78-L96` → `_start_repl()` focuses the editor, starts `_request_worker`, updates the resource bar, shows welcome content, and emits the ready file after refresh.
- `src/tunacode/core/agents/main.py:L138-L146` → `RequestOrchestrator.run()` applies `global_request_timeout` around `_run_impl()`.
- `src/tunacode/core/agents/main.py:L154-L180` → `_run_impl()` initializes request state, obtains an agent, compacts history, replaces agent messages, and starts the stream loop.
- `src/tunacode/core/agents/main.py:L211-L220` → `_compact_history_for_request()` invokes compaction before the stream.
- `src/tunacode/core/agents/main.py:L577-L609` → `_run_stream()` iterates `agent.stream(...)` and logs `Request complete (<ms>ms)`.
- `src/tunacode/core/agents/agent_components/agent_config.py:L295-L324` → `_build_stream_fn()` applies `request_delay` before provider streaming and retries transient failures with backoff.
- `src/tunacode/core/agents/agent_components/agent_config.py:L372-L379` → `_build_skills_prompt_state()` enumerates all skill summaries and resolves selected skills.
- `src/tunacode/core/agents/agent_components/agent_config.py:L420-L474` → `get_or_create_agent()` loads models registry, builds skills prompt state, computes agent version, reuses session-cached agents when version matches, otherwise rebuilds system prompt, model, and tools.
- `src/tunacode/infrastructure/cache/caches/tunacode_context.py:L21-L45` → `get_context()` returns mtime-cached AGENTS.md-derived project context.
- `src/tunacode/infrastructure/cache/caches/skills.py:L24-L67` → skill summaries and loaded skills are stored in an mtime cache.
- `src/tunacode/skills/registry.py:L16-L31` → `list_skill_summaries()` discovers and loads all valid skill summaries.
- `src/tunacode/skills/registry.py:L91-L108` → summary and full-skill loads are cache-backed.
- `src/tunacode/skills/selection.py:L42-L73` → `resolve_selected_skills()` loads each selected skill and related paths.
- `src/tunacode/configuration/defaults.py:L23-L39` → defaults include `request_delay: 0.0`, `global_request_timeout: 600.0`, `stream_agent_text: False`, and `lsp.enabled: True`.
- `tests/system/cli/test_tmux_tools.py:L15-L17` → tmux startup test constants: ready timeout 20s, response timeout 60s, poll interval 0.5s.
- `tests/system/cli/test_tmux_tools.py:L101-L136` → tmux integration test launches TunaCode, waits for readiness file, sends a prompt, and polls pane contents for the response.
- `scripts/startup_timer.py` → CLI startup timer utility.
- `scripts/ui_import_timer.py` → isolated-import timing utility.

## Patterns Found
- Submit event path:
  - `src/tunacode/ui/widgets/editor.py:L116-L128`
  - `src/tunacode/ui/app.py:L331-L340`
  - `src/tunacode/ui/app.py:L214-L225`
  - `src/tunacode/ui/app.py:L240-L304`
- User message is written after queue insertion and before request completion:
  - `src/tunacode/ui/app.py:L336-L340`
- Loading-state activation occurs at the start of `_process_request()` before the call into `core.agents.main.process_request(...)`:
  - `src/tunacode/ui/app.py:L240-L248`
- Request-start work performed after loading-state activation includes agent retrieval/build and compaction setup:
  - `src/tunacode/core/agents/main.py:L154-L180`
  - `src/tunacode/core/agents/main.py:L211-L220`
  - `src/tunacode/core/agents/agent_components/agent_config.py:L420-L474`
- Streaming text is optional and config-gated:
  - `src/tunacode/ui/app.py:L227-L238`
  - `src/tunacode/ui/app.py:L251-L253`
  - `src/tunacode/configuration/defaults.py:L23-L39`
- Streaming updates are throttled to 100ms in the app and applied on first chunk or throttle expiry:
  - `src/tunacode/ui/app.py:L87-L94`
  - `src/tunacode/ui/streaming.py:L12-L29`
- Pre-stream request work includes request-state reset, agent retrieval/build, and compaction:
  - `src/tunacode/core/agents/main.py:L154-L180`
  - `src/tunacode/core/agents/main.py:L211-L220`
  - `src/tunacode/core/agents/agent_components/agent_config.py:L420-L474`
- Agent build path assembles prompt material from system prompt, AGENTS.md context, selected skills, and available skills:
  - `src/tunacode/core/agents/agent_components/agent_config.py:L446-L454`
  - `src/tunacode/core/agents/agent_components/agent_config.py:L372-L379`
  - `src/tunacode/skills/registry.py:L16-L31`
  - `src/tunacode/skills/selection.py:L42-L73`
- Cache-backed prompt inputs:
  - AGENTS.md context cache: `src/tunacode/infrastructure/cache/caches/tunacode_context.py:L21-L45`
  - skill summary/load cache: `src/tunacode/infrastructure/cache/caches/skills.py:L24-L67`
  - models registry cache: `src/tunacode/configuration/models.py:L69-L90`
- Provider stream delay/backoff path:
  - `src/tunacode/core/agents/agent_components/agent_config.py:L295-L324`
- Tmux readiness and prompt polling path already exists in tests:
  - `tests/system/cli/test_tmux_tools.py:L36-L60`
  - `tests/system/cli/test_tmux_tools.py:L101-L136`

## Dependencies
- `Editor.action_submit()` → posts `EditorSubmitRequested` → `TextualReplApp.on_editor_submit_requested()`
- `TextualReplApp.on_editor_submit_requested()` → `request_queue.put(...)` → `_request_worker()` → `_process_request()`
- `TextualReplApp._process_request()` → `tunacode.core.agents.main.process_request(...)`
- `process_request()` → `RequestOrchestrator.run()` → `RequestOrchestrator._run_impl()`
- `RequestOrchestrator._run_impl()` → `ac.get_or_create_agent(...)`
- `get_or_create_agent()` → `load_models_registry()` + `_build_skills_prompt_state()` + `load_system_prompt()` + `load_tunacode_context()` + `_build_tools()`
- `_build_skills_prompt_state()` → `list_skill_summaries()` + `resolve_selected_skills()`
- `list_skill_summaries()` → `discover_skills()` + skill-summary cache/load
- `resolve_selected_skills()` → `load_skill_by_name()` + `list_skill_related_paths()`
- `RequestOrchestrator._run_impl()` → `_compact_history_for_request()` → `CompactionController.check_and_compact(...)`
- `RequestOrchestrator._run_stream()` → `agent.stream(self.message)` → `_handle_message_update(...)`
- `_handle_message_update(...)` → `streaming_callback(delta)` only when a callback was passed from UI
- `TextualReplApp._process_request()` finalization → `_get_latest_response_text()` → `render_agent_response(...)` → `chat_container.write(...)`

## Symbol Index
- `src/tunacode/ui/widgets/editor.py:L38` → `Editor`
- `src/tunacode/ui/app.py:L70` → `TextualReplApp`
- `src/tunacode/ui/streaming.py:L12` → `StreamingHandler`
- `src/tunacode/ui/lifecycle.py:L18` → `AppLifecycle`
- `src/tunacode/core/agents/main.py:L111` → `RequestOrchestrator`
- `src/tunacode/core/agents/main.py:L658` → `process_request`
- `src/tunacode/core/agents/agent_components/agent_config.py:L420` → `get_or_create_agent`
- `src/tunacode/skills/registry.py:L16` → `list_skill_summaries`
- `src/tunacode/skills/selection.py:L42` → `resolve_selected_skills`
- `src/tunacode/infrastructure/cache/caches/tunacode_context.py:L21` → `get_context`
- `src/tunacode/infrastructure/cache/caches/skills.py:L24` → `get_skill_summary`
- `src/tunacode/infrastructure/cache/caches/skills.py:L47` → `get_loaded_skill`

## Observed Configuration
- Sanitized local config path: `/home/fabian/.config/tunacode.json`
- Sanitized observed values:
  - `default_model`: `minimax-coding-plan:MiniMax-M2.7`
  - `settings.max_retries`: `10`
  - `settings.max_iterations`: `40`
  - `settings.request_delay`: `0.0`
  - `settings.global_request_timeout`: `120.0`
  - `settings.stream_agent_text`: `false`
  - `settings.lsp.enabled`: `true`
  - `settings.lsp.timeout`: `5.0`

## Observed Timings
- `uv run python scripts/startup_timer.py --iterations 3 --command=--version`
  - mean: `0.266s`
  - median: `0.266s`
  - min: `0.260s`
  - max: `0.271s`
- `uv run python scripts/ui_import_timer.py --iterations 3 --warmup 0 --module tunacode.ui.main --module tunacode.ui.app --module tunacode.ui.repl_support`
  - `tunacode.ui.main` mean: `0.2475s`
  - `tunacode.ui.app` mean: `0.2438s`
  - `tunacode.ui.repl_support` mean: `0.1939s`
- Live tmux session observation on existing session `tunacode`:
  - a unique submitted prompt became visible in the pane in `59ms`
  - measurement method: `tmux send-keys` followed by repeated `tmux capture-pane` polling for the unique token
  - this observation measured submitted-prompt visibility in the pane, not loading-indicator visibility
- User-reported manual observation in the same investigation:
  - loading indicator became visibly present about `3s` after Enter
- Code-path timing distinction captured in this note:
  - loading state is activated in `_process_request()` at `src/tunacode/ui/app.py:L240-L248`
  - this note does not include a direct instrumented measurement of the first visible repaint of the loading indicator

## Research Tooling Availability
- Absent in this repository:
  - `scripts/structure-map.sh`
  - `scripts/ast-scan.sh`
  - `scripts/symbol-index.sh`
  - `scripts/dependency-graph.sh`
- Present in this repository:
  - `scripts/startup_timer.py`
  - `scripts/ui_import_timer.py`
