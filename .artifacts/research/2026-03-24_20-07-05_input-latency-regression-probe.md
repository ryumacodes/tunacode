---
title: "input latency regression probe"
link: "input-latency-regression-probe"
type: research
ontological_relations:
  - relates_to: [[input-latency-threaded-request-execution-plan]]
  - relates_to: [[input-latency-threaded-request-execution-log]]
  - relates_to: [[tui-submit-latency-research]]
tags: [research, ui, input-latency, tmux, regression]
uuid: "38d59109-86d6-4899-8ed8-568fa95bfdb4"
created_at: "2026-03-24T20:07:05-05:00"
---

## Purpose

Capture what was learned after the threaded-request rollout when the user still reported severe input lag during active requests.

This note is specifically about the follow-up regression hunt:
- what was tested
- what was ruled out
- what actually measured better or worse
- what uncertainty remains

## Baseline Context

- Branch during probe: `ui-bridge`
- Current validated commit during probe: `fb0b6742`
- Working tree state at end of probe: clean
- Environment used for live checks:
  - real `tmux`
  - real `tunacode`
  - real `MINIMAX_API_KEY`
  - config with:
    - `stream_agent_text: false`
    - `lsp.enabled: true`
    - `request_delay: 0.0`

## User Claim Under Investigation

User report:
- input lag is severe while a request is active
- this felt like a new problem "today"
- there should be effectively no visible delay while typing a new draft during load

Important distinction:
- the user is reporting *typing feel*
- the automated probe used here measures *time until typed text becomes visible in captured tmux pane output*

Those are related, but not identical.

## What Was Already Known Before This Probe

From the threaded-request rollout:
- request execution was moved off the UI loop into a threaded Textual worker
- callbacks were routed back onto the UI thread through queues/messages
- `pytest`, `mypy`, `ruff check`, `ruff format --check`, and coverage all passed

Earlier tmux check after rollout:
- draft text became visible during an active request
- `Escape` cancellation worked
- measured draft visibility was still slow enough to be user-visible

## Hypotheses Tested

### Hypothesis 1: live thought-panel repaint churn is the main remaining problem

Tested changes:
- remove forced `scroll_end()` on every thought-panel update
- defer live thought-panel repaint while the editor contains a draft

Observed result:
- removing forced scroll alone did not materially help
- deferring live thought repaint while drafting improved the tmux probe from about `1898 ms` to about `857 ms`

Why this was not kept:
- user explicitly wanted live thought updates to remain visible
- the change improved the measurement, but it changed behavior the user did not want

Conclusion:
- thought-panel churn is a real contributor
- but the simplest helpful version of that fix was not acceptable product behavior

### Hypothesis 2: the loading indicator widget itself is blocking input

Reason to test:
- Textual's built-in `LoadingIndicator` stops and prevents `InputEvent`s in its own implementation
- that looked like a direct explanation for input lag

Tested change:
- replace `LoadingIndicator()` with a plain `Static("Loading...")`

Observed result:
- focused tests still passed
- tmux draft-visibility probe got worse: about `2058 ms`

Conclusion:
- the loading indicator widget class itself was not the fix
- the experiment was reverted

### Hypothesis 3: today's "show loading indicator immediately on submit" change introduced the regression

Candidate commit:
- `ff2668e0` — `fix(ui): show loading indicator immediately on submit`

Why it looked suspicious:
- it landed today
- it changed submit-path ordering
- it introduced `call_after_refresh(...)` request queueing

Initial local experiment:
- revert immediate loading show
- revert deferred queueing after refresh

Observed result from that isolated local experiment:
- tmux probe improved somewhat, to about `1645 ms`

This was suggestive, but not enough to prove causality.

## Commit-by-Commit Regression Probe

To stop guessing, the same tmux draft-visibility probe was run across multiple commits using detached worktrees and the same real provider/config.

Probe shape:
- launch TunaCode in tmux
- submit a real prompt
- wait `0.5s`
- type a unique draft token
- poll pane capture until the draft token becomes visible
- send `Escape`
- confirm cancellation marker becomes visible

### Measured Results

- `c42e11ca` (`Merge branch 'commands'`)
  - `draft_visible=true`
  - `draft_latency_ms=1674`
  - `cancel_seen=true`

- `ff2668e0` (`fix(ui): show loading indicator immediately on submit`)
  - `draft_visible=true`
  - `draft_latency_ms=1613`
  - `cancel_seen=true`

- `3d644df5` (`T005: run process_request in a threaded Textual worker`)
  - `draft_visible=true`
  - `draft_latency_ms=1564`
  - `cancel_seen=true`

- `fb0b6742` (`Thread request execution and UI callback routing`)
  - `draft_visible=true`
  - `draft_latency_ms=983`
  - `cancel_seen=true`

## Hard Findings

### Finding 1: the lag did not start with today's loading-submit change

`ff2668e0` was not a regression spike in this probe.

It was slightly better than the earlier `c42e11ca` baseline:
- `1674 ms` → `1613 ms`

So the user's "this only happened today" report was not confirmed by this automated measurement.

### Finding 2: the threaded-request work improved the measured pane-visibility latency

The threaded/callback-routed implementation was the best result measured in this probe:
- `fb0b6742` at about `983 ms`

That means:
- the threaded execution work did not create the observed delay in this metric
- it reduced it relative to the pre-threaded baseline

### Finding 3: tmux pane visibility is probably not measuring the full user pain

The user still reported typing as obviously sluggish.

But the commit-by-commit probe showed:
- lag existed before today's submit/loading change
- current threaded code measured better than earlier code

So either:
1. the remaining lag is real but this probe is too blunt to isolate it, or
2. the main pain is not "time until text appears in pane capture"

Most likely issue:
- the current measurement is missing the exact interaction the user feels:
  - keypress delivery
  - editor redraw
  - cursor update
  - wrap/layout cost
  - viewport churn

## Dead Ends / Disproved Ideas

- "the loading indicator widget class is the main blocker"
  - tested and not supported

- "today's immediate-loading submit change caused the entire regression"
  - not supported by commit-by-commit probe

- "threading made it worse"
  - not supported by commit-by-commit probe

## Most Plausible Remaining Explanations

### 1. The probe is measuring the wrong milestone

Pane-capture visibility is coarse.

It can miss:
- sticky keypress feel
- delayed cursor motion
- editor-side wrap/render cost before pane capture reflects stable text

### 2. Live UI churn is still affecting local typing feel

Even after moving request execution off the UI loop, the UI thread still does:
- thought-panel rendering
- tool panel mounts
- chat widget mounts
- viewport scrolling
- streaming/thinking flushes on an interval

This can still make typing feel bad even if the final pane text shows up under the probe's threshold.

### 3. The most user-visible delay may be in the editor path itself

Potential areas not yet directly instrumented:
- `Editor.on_key(...)`
- input value watchers / wrap cache invalidation
- cursor positioning / `scroll_to_region(...)`
- screen refresh after editor mutation

## Best Current Interpretation

The data gathered here supports this interpretation:

- the app had non-trivial active-request typing lag even before today's submit/loading commit
- today's loading-submit change is not the root cause
- the threaded-request rollout improved the measured situation rather than worsening it
- there is still a real user-facing responsiveness problem, but this probe is not enough to localize it precisely

## Recommended Next Step

Do not keep making blind UI tweaks.

Instrument the actual editor/input path while a request is active:
- timestamp key event receipt
- timestamp editor value mutation
- timestamp next visible refresh / render pass
- capture whether thought/tool/stream flush happened in the same interval

That will reveal whether the remaining delay is:
- input-event delivery
- editor rendering
- viewport/layout churn
- or tmux/pane-observation noise

## Final State At End Of This Probe

- repository restored to clean `fb0b6742` state
- no experimental loading-indicator replacement left in the worktree
- no submit-path revert left in the worktree
- best measured commit from this probe: `fb0b6742`
