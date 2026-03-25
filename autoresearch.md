# Autoresearch: active-request tmux draft visibility latency

## Objective
Reduce the latency users feel while typing a new draft during an already-active request, without hiding live thought updates or otherwise cheating by removing the user-visible work.

This session now optimizes the closest automated proxy to the original user complaint: **time until newly typed draft text becomes visible in a real tmux pane while a request is active**.

## Metrics
- **Primary**: `pane_p95` (ms, lower is better) — median-of-runs p95 delay from sending a draft token into a real tmux-hosted TunaCode session until that token becomes visible in the pane capture during an active synthetic request.
- **Secondary**:
  - `pane_median` — typical pane-visibility latency under load
  - `pane_max` — spike severity under load
  - `idle_pane_p95` — unloaded pane-visibility baseline
  - `active_idle_pane_gap` — extra pane delay caused by an active request

## How to Run
`./autoresearch.sh`

The benchmark launches a real `TextualReplApp` inside tmux with a patched synthetic request loop, submits a prompt, waits briefly for the request to become active, types a unique draft token, and polls `tmux capture-pane` until the token is visible.

## Files in Scope
- `src/tunacode/ui/app.py` — request lifecycle, loading, streaming, thinking wiring
- `src/tunacode/ui/thinking_state.py` — live thought rendering and throttling
- `src/tunacode/ui/widgets/editor.py` — local typing path and edit-activity tracking
- `src/tunacode/ui/renderers/thinking.py` — thought content shaping if needed
- `src/tunacode/ui/widgets/chat.py` — chat mounting / scroll behavior if needed
- `tests/unit/ui/` and `tests/integration/ui/` — correctness coverage for request/thinking behavior
- `scripts/benchmarks/input_tmux_latency.py` — primary benchmark workload
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
- Earlier wins already on the branch from the coarse `pilot.press()` benchmark:
  - removing forced `scroll_end()` on incremental thought updates
  - adaptive thought throttling (`100 ms` normally, `300 ms` while drafting)
  - shrinking hidden thought retention from `20k` chars to `2.4k`
  - deferring incremental thought refreshes for `150 ms` after the most recent editing keypress
- The intermediate render-focused benchmark showed the branch already around low-20 ms keypress-to-render latency, and it confirmed the `150 ms` recent-keypress deferral still helped.
- Many nearby cadence/buffer/render-path variants regressed under earlier benchmarks: `125 ms` / `175 ms` keypress windows, `200 ms` / `350 ms` drafting throttles, detached live thought widgets, pending-delta buffers, queue-drain deferral, smaller visible thought payloads, and editor-path micro-optimizations.
- Current hypothesis: the current branch may already be near the floor for real tmux pane visibility, so the most valuable work is validating that with the tmux workload and only keeping changes that improve this closest user-facing proxy.
