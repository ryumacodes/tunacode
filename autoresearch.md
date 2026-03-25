# Autoresearch: active-request editor input latency

## Objective
Reduce the latency users feel while typing a new draft during an already-active request, without hiding live thought updates or otherwise cheating by removing the user-visible work.

## Metrics
- **Primary**: `input_p95` (ms, lower is better) — median-of-runs p95 keypress latency while a synthetic active request is pushing live thinking updates through the real Textual app.
- **Secondary**:
  - `input_median` — typical keypress latency under load
  - `input_max` — spike severity during the sample
  - `idle_p95` — unloaded editor baseline
  - `active_idle_gap` — extra latency caused by an active request

## How to Run
`./autoresearch.sh`

The benchmark uses a real `TextualReplApp` test harness and patches `process_request()` with a synthetic request that continuously emits thinking deltas. It measures end-to-end per-key latency using `pilot.press()` while the loading indicator is active.

## Files in Scope
- `src/tunacode/ui/app.py` — request lifecycle, loading, streaming, thinking wiring
- `src/tunacode/ui/thinking_state.py` — live thought rendering and throttling
- `src/tunacode/ui/widgets/chat.py` — chat mounting / scroll behavior if needed
- `src/tunacode/ui/styles/layout.tcss` — any supporting live-thinking layout changes
- `tests/unit/ui/` and `tests/integration/ui/` — correctness coverage for request/thinking behavior
- `scripts/benchmarks/input_latency.py` — primary benchmark workload
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
- Historical probe: removing thought-panel auto-scroll alone did not materially help.
- Historical probe: deferring live thought repaint while drafting improved measurements, but it hid live thoughts and was rejected.
- Historical probe: replacing `LoadingIndicator` was worse.
- Historical probe: the threaded request worker improved the coarse tmux measurement, so the remaining issue is likely live UI churn on the main thread rather than request execution itself.
- Current session hypothesis: live thought rendering still couples request churn to editor responsiveness; make live thought presentation cheaper without removing it.
