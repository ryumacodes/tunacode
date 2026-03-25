# Autoresearch: active-request tmux draft visibility latency

## Objective
Reduce the latency users feel while typing a new draft during an already-active request, without hiding live thought updates or otherwise cheating by removing the user-visible work.

This session optimizes the closest automated proxy to the original user complaint: **time until newly typed draft text becomes visible in a real tmux pane while a request is active**.

The current one-token tmux workload showed that `pane_p95` is too unstable to serve as the primary optimization target: unchanged-code reruns bounce between roughly low-30 ms and low-60 ms because the benchmark is effectively measuring whether a single sample missed one extra polling interval. The stable signal in this workload is `pane_median`, while `pane_max` remains useful as a tail monitor.

## Metrics
- **Primary**: `pane_median` (ms, lower is better) — typical delay from sending a draft token into a real tmux-hosted TunaCode session until that token becomes visible in pane capture during an active synthetic request.
- **Secondary**:
  - `pane_p95` — still tracked as a noisy tail monitor
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
- The simpler one-token tmux benchmark remains the most practical automated proxy for now. Attempts to stabilize it via a multi-token-per-session redesign either timed out or still produced confirmation spikes, so that path is deferred.
- A `125 ms` recent-keypress window briefly looked better than `150 ms` on the old one-token tmux workload, but failed on confirmation with a severe tail spike; `150 ms` remains the stable setting.
- Detached live-thinking widgets and several buffer/cadence micro-tweaks kept improving or preserving `pane_median` but frequently lost on noisy `pane_p95` spikes.
- Current hypothesis: optimize against `pane_median` while monitoring `pane_p95`/`pane_max` for catastrophic regressions. That should better match the common visible typing feel instead of a single noisy polling miss.
