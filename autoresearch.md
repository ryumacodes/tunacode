# Autoresearch: active-request editor input paint latency

## Objective
Reduce the latency users feel while typing a new draft during an already-active request, without hiding live thought updates or otherwise cheating by removing the user-visible work.

This session now optimizes a more user-facing benchmark than the earlier `pilot.press()` wall-time metric. The new workload measures **time until the editor is next rendered after a keypress**, which is closer to the visible local typing experience the user complained about.

## Metrics
- **Primary**: `paint_p95` (ms, lower is better) — median-of-runs p95 time from keypress injection to the next editor render pass showing the updated editor value during an active synthetic request.
- **Secondary**:
  - `paint_median` — typical paint latency under load
  - `press_return_p95` — previous coarse `pilot.press()`-style wall time for comparison
  - `paint_after_return_p95` — residual paint delay after `pilot.press()` returns
  - `idle_paint_p95` — unloaded editor paint baseline
  - `active_idle_paint_gap` — extra paint delay caused by an active request

## How to Run
`./autoresearch.sh`

The benchmark patches `Editor.render_line()` to timestamp the first render pass after each keypress where the editor value reflects the new text. It still runs through a real `TextualReplApp` test harness and a synthetic active request that continuously emits thinking deltas.

## Files in Scope
- `src/tunacode/ui/app.py` — request lifecycle, loading, streaming, thinking wiring
- `src/tunacode/ui/thinking_state.py` — live thought rendering and throttling
- `src/tunacode/ui/widgets/editor.py` — local typing path and edit-activity tracking
- `src/tunacode/ui/renderers/thinking.py` — thought content shaping if needed
- `src/tunacode/ui/widgets/chat.py` — chat mounting / scroll behavior if needed
- `tests/unit/ui/` and `tests/integration/ui/` — correctness coverage for request/thinking behavior
- `scripts/benchmarks/input_paint_latency.py` — primary benchmark workload
- `autoresearch.checks.sh` — focused validation commands

## Off Limits
- Disabling live thought updates entirely
- Faking a better result by shrinking the workload below a realistic active-request scenario
- Changes outside the input-latency path unless required by failing focused checks
- Destructive cleanup of untracked files

## Constraints
- Keep the benchmark representative of active-request UI churn.
- Do not overfit to the benchmark by removing functionality the user relies on.
- Keep edits minimal and within existing architecture boundaries.
- Focused UI tests must pass for kept changes.
- Update `AGENTS.md` if `src/` changes.

## What's Been Tried
- Earlier coarse benchmark wins already on the branch:
  - removing forced `scroll_end()` on incremental thought updates
  - adaptive thought throttling (`100 ms` normally, `300 ms` while drafting)
  - shrinking hidden thought retention from `20k` chars to `2.4k`
  - deferring incremental thought refreshes for `150 ms` after the most recent editing keypress
- Under the older `pilot.press()` metric, many nearby variants regressed: `125 ms` and `175 ms` keypress windows, `200 ms` and `350 ms` drafting throttles, smaller visible thought payloads, pending-delta buffers, queue-drain deferral, detached live thought widgets, and editor-side micro-optimizations.
- Current hypothesis for the new benchmark: the existing keyburst-aware thought deferral should help actual keypress-to-paint latency too, but the more precise render metric may expose a different optimum than the coarser wall-time metric.
