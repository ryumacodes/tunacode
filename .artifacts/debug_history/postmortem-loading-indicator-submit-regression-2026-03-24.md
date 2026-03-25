# Postmortem: Loading-indicator submit regression after TUI latency fix

**Date:** 2026-03-24
**Scope:** Textual submit path and loading-indicator visibility in `src/tunacode/ui/app.py`

## Summary
A change intended to make the loading indicator appear immediately after Enter introduced a TUI responsiveness regression.

The first fix attempt did improve perceived loader visibility, but it did so by making the submit handler wait for a refresh cycle before queueing the request. In live use, that created a bad UI state where the loader could appear and the interface could feel stuck or fail to proceed normally.

The root issue was not the model. It was the TUI submit/control-flow change.

## What happened
Original behavior under investigation:
- user reported that pressing Enter could take about 3 seconds before loading became visibly present
- likely cause: request-start work was blocking the first visible repaint of the loader

First attempted fix:
- show loading immediately in `on_editor_submit_requested(...)`
- render the user message
- `await` a helper that waited for `call_after_refresh(...)`
- only then queue the request

That version changed the submit path from:
- show user message
- queue request

to:
- show loading
- show user message
- wait for refresh
- queue request

## Why it broke
The failure was caused by adding a blocking wait into the submit event path.

Specifically:
- the submit handler became dependent on a refresh callback completing before request queueing could continue
- this made progress depend on a UI-refresh handshake inside the same interaction path
- that coupling was too fragile for the Textual event flow in this app

In practice, this created the exact kind of bug the user reported:
- loading visible
- UI felt wrong or stuck
- input path no longer behaved normally

## Root cause
**Bad control-flow design in the TUI submit handler.**

The mistake was:
- using an awaited refresh barrier in the user-input path

instead of:
- scheduling post-refresh work without blocking the handler

This was a UI orchestration bug, not a provider/model issue.

## Impact
- User-facing regression in the core REPL interaction path
- Loader behavior became misleading or stuck-looking
- Trust in the attempted latency fix was reduced because the UI felt worse even though loader timing initially looked improved in measurement

## Resolution applied
The blocking refresh wait was removed.

Current implementation:
- `on_editor_submit_requested(...)`
  - shows loading immediately
  - renders the user message immediately
  - schedules request queueing with `call_after_refresh(...)`
  - does **not** await the refresh from inside submit
- `_process_request(...)`
  - still shows loading defensively at request start
  - hides loading in finalization

Concrete code shape now:
- `src/tunacode/ui/app.py`
  - `_show_loading_indicator()`
  - `_hide_loading_indicator()`
  - `_queue_request_after_refresh()`
  - `on_editor_submit_requested(...)` now calls `_queue_request_after_refresh(normalized_message)`

## Why the corrected version is safer
The corrected approach preserves the intended paint ordering without blocking the input handler:
- loader can paint immediately
- request still starts after the next refresh
- submit path returns normally instead of waiting on a UI refresh completion signal

This keeps the UI responsive while still solving the original “loader appears too late” problem.

## Guardrail added
Added focused regression test:
- `tests/unit/ui/test_app_loading_indicator.py`

What it verifies:
- loading is shown during submit
- request is **not** queued immediately
- request is scheduled via `call_after_refresh(...)`
- when the scheduled callback runs, the request is queued

This specifically guards against reintroducing a blocking awaited-refresh pattern in the submit path.

## Validation after correction
Validated with:
- `uv run pytest tests/unit/ui/test_app_loading_indicator.py -q`
- `uv run pytest tests/test_dependency_layers.py -q`
- `uv run ruff check src/tunacode/ui/app.py tests/unit/ui/test_app_loading_indicator.py`

Live tmux sanity retest after correction:
- prompt visible: ~`56ms`
- loading visible: ~`56ms`
- simple response completed: ~`1483ms`

## Lessons learned
1. **Do not block the submit handler on UI refresh coordination.**
   - Schedule post-refresh work; do not await it in the core input path.
2. **Perceived-latency fixes in TUI code need live interaction checks, not just code reasoning.**
   - A fix can improve timing while still breaking responsiveness.
3. **Measure the exact user-visible event.**
   - Prompt visibility, loader visibility, and first assistant output are different milestones.
4. **When a user says the bug is in the UI, treat model/provider explanations as secondary until disproven.**

## Rule restatement
For TunaCode TUI interaction fixes:
- prefer non-blocking UI scheduling over awaited refresh barriers in input handlers
- optimize for user-visible responsiveness, not just internal state timing
