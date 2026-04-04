---
title: Input Latency Research Artifact
summary: Research notes explaining the causes of input latency during active requests.
when_to_read:
  - When investigating editor sluggishness during requests
  - When reviewing the original latency research
last_updated: "2026-04-04"
---

# Input Latency Research Artifact

Date: 2026-03-24
Repo: `tunacode`
Type: Research artifact
Conclusion: This is an architecture issue, not an editor-widget bug

## Research Question

Why does the editor feel sluggish while a request is loading, even though the user is only typing a new draft and has not submitted it?

## Executive Summary

The editor is not explicitly disabled during loading.
The sluggishness comes from shared runtime ownership: the editor, request orchestration, live request callbacks, panel rendering, and viewport updates all run inside the same Textual app process and compete on the same UI/event loop.

So the issue is not:

- "the loading indicator blocks the input"
- "the editor is disabled during a request"

The issue is:

- request work and UI work are not isolated from local typing

## Repository Evidence

The core coupling points are visible in the current codebase:

- App lifecycle starts the request worker inside the Textual app:
  [src/tunacode/ui/lifecycle.py](/home/fabian/tunacode/src/tunacode/ui/lifecycle.py)
- The app owns the request queue and awaits request processing:
  [src/tunacode/ui/app.py](/home/fabian/tunacode/src/tunacode/ui/app.py)
- Request execution runs through the in-process agent stream:
  [src/tunacode/core/agents/main.py](/home/fabian/tunacode/src/tunacode/core/agents/main.py)
- Streaming/thinking/tool callbacks all feed back into UI rendering:
  [src/tunacode/ui/streaming.py](/home/fabian/tunacode/src/tunacode/ui/streaming.py)
  [src/tunacode/ui/thinking_state.py](/home/fabian/tunacode/src/tunacode/ui/thinking_state.py)
  [src/tunacode/ui/repl_support.py](/home/fabian/tunacode/src/tunacode/ui/repl_support.py)
- Chat writes mount widgets and trigger viewport churn:
  [src/tunacode/ui/widgets/chat.py](/home/fabian/tunacode/src/tunacode/ui/widgets/chat.py)

This means the "current request" and the "new local draft" are not operationally independent.

## Real-World Reproduction

The issue was reproduced in a real `.venv` + `tmux` TunaCode session, not only by reading code.

Basic reproduction:

1. Launch TunaCode in `tmux`.
2. Submit a real model request such as:
   `Tell me about AGENTS.md in this repo and be specific.`
3. Wait until the request is clearly active.
4. Type a new draft into the editor without submitting it.
5. Observe that the new draft does not appear immediately.

Observed behavior:

- Newly typed text took around one second to become visible during the active request.
- This delay remained large even after smaller UI-level tweaks.

That strongly suggests loop contention, not a simple widget-state bug.

## Why This Is Architectural

The important distinction is logical separation vs runtime separation.

Logically:

- the user is drafting a new prompt
- the previous prompt is still loading

Architecturally, however:

- both activities are sharing the same app runtime
- both activities depend on the same event loop staying responsive
- both activities trigger redraw and state churn inside the same UI system

So "the input should have nothing to do with loading" is a correct product expectation, but it is not how the current architecture behaves.

## What Small UI Tweaks Can And Cannot Fix

Small UI tweaks can reduce symptoms:

- less aggressive thought rendering
- less auto-scroll churn
- fewer large live panel mounts
- coarser throttling

But those are mitigations, not the real fix.
They may improve or worsen the feel slightly, but they do not remove the fundamental coupling.

## Actual Fix Direction

The durable fix is to separate request execution from the UI loop.

Recommended direction:

1. Run request orchestration off the main Textual UI loop.
2. Marshal UI updates back onto the UI thread in controlled batches.
3. Keep editor input/rendering local and immediately responsive even while request work continues elsewhere.
4. Treat streaming/thinking/tool events as queued view-model updates, not direct widget mutations from the request path.

## Acceptance Criterion

The system should satisfy this product rule:

"Typing a new draft during an active request remains immediately visible and locally responsive, regardless of ongoing model/tool rendering."

Until that rule is enforced at the architecture boundary, the app will keep exhibiting this class of lag under real request load.
