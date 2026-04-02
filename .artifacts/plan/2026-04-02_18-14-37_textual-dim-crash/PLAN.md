---
title: "textual dim crash implementation plan"
link: "textual-dim-crash-plan"
type: implementation_plan
ontological_relations:
  - relates_to: [[textual-dim-crash-research]]
tags: [plan, textual, ui, coding]
uuid: "2c2e6ffb-f1c7-4e8e-b2b0-74d3bfee9ae7"
created_at: "2026-04-02T18:14:37-05:00"
parent_research: ".artifacts/research/2026-04-02_18-10-50_textual-dim-crash.md"
git_commit_at_plan: "5c08dba1"
---

## Goal

- Prevent TunaCode's Textual UI from crashing when startup or theme-preview rendering combines `dim` styles with unresolved default/ANSI colors under Textual 4.0.0.
- Keep the fix local to TunaCode's UI/theme registration and Rich rendering path; do not patch `.venv` packages or change dependency versions.
- Out of scope: upstream Textual bugfixes, dependency upgrades/downgrades, redesigning chat selection behavior, or broad visual restyling.

## Scope & Assumptions

- IN scope:
  - Harden wrapped built-in themes so TunaCode does not re-register themes with `None` or `ansi_default` color fields where TunaCode can provide safe concrete values.
  - Add a UI-local Rich style normalization layer before `SelectableRichVisual` hands segments back to Textual filters.
  - Add one focused app-level regression test for startup welcome rendering plus theme switching through the known risky built-in themes.
  - Refresh developer-facing docs and `AGENTS.md` for the new render-safety layer.
- OUT of scope:
  - Editing `textual/filter.py` or any dependency under `.venv/`.
  - Replacing the ANSI logo asset with a different format.
  - Rewriting the theme picker UX or changing the supported theme list.
  - Adding more than one new test file per task.
- Assumptions:
  - The research findings remain valid at commit `5c08dba1`: `Text.from_ansi(...)` on `src/tunacode/ui/assets/logo.ansi` yields default-color spans, and `ANSIToTruecolor.truecolor_style(...)` still crashes when asked to dim against `RichColor.default()`.
  - The related artifact `.artifacts/research/2026-03-31_11-32-31_theme-switch-dim-background-crash.md` is available during execution and should be treated as supporting context for theme-preview behavior.
  - The untracked research artifact present at plan time, `.artifacts/research/2026-04-02_18-10-50_textual-dim-crash.md`, must not be deleted or cleaned up during execution.

## Deliverables

- Hardened built-in theme wrapping in `src/tunacode/constants.py` with explicit tests around risky built-in themes.
- A new UI render-safety helper that converts unresolved Rich colors and pre-resolves `dim` styling before Textual's filters run.
- One integration regression covering startup welcome rendering and theme changes in `TextualReplApp`.
- Updated developer docs and `AGENTS.md` reflecting the new UI render-safety behavior.

## Readiness

- Preconditions:
  - Research artifacts exist at `.artifacts/research/2026-04-02_18-10-50_textual-dim-crash.md` and `.artifacts/research/2026-03-31_11-32-31_theme-switch-dim-background-crash.md`.
  - Current git baseline captured at commit `5c08dba1`.
  - The repo test harness can run `uv run pytest` and `uv run python scripts/check_agents_freshness.py`.
- Before starting execution:
  - Preserve the architecture boundary `types -> utils -> infrastructure -> configuration -> tools -> core -> ui`.
  - Keep the fix inside TunaCode source; do not vendor, monkeypatch, or edit Textual/Rich in site-packages.
  - Leave untracked artifacts in place unless the user explicitly asks for cleanup.

## Milestones

- M1: Theme registration no longer preserves unsafe built-in color placeholders.
- M2: Chat/welcome Rich segments are normalized before Textual filter processing.
- M3: App-level regression proves startup and theme switching no longer crash.
- M4: Developer docs and repository metadata reflect the new render-safety layer.

## Ticket Index

<!-- TICKET_INDEX:START -->

| Task | Title | Ticket |
|---|---|---|
| T001 | Harden wrapped built-in themes against unresolved colors | [tickets/T001.md](tickets/T001.md) |
| T002 | Normalize Rich segment styles before Textual filter execution | [tickets/T002.md](tickets/T002.md) |
| T003 | Add a startup and theme-switch crash regression harness | [tickets/T003.md](tickets/T003.md) |
| T004 | Refresh developer docs and AGENTS metadata for render safety | [tickets/T004.md](tickets/T004.md) |
| T005 | Investigate unresolved built-in theme fields as an architecture follow-up | [tickets/T005.md](tickets/T005.md) |

<!-- TICKET_INDEX:END -->

## Work Breakdown (Tasks)

### T001: Harden wrapped built-in themes against unresolved colors

**Summary**: Extend TunaCode's built-in theme metadata and wrapper logic so re-registered themes do not leave `foreground`, `background`, `surface`, or `panel` as `None` or `ansi_default` when TunaCode can supply safe concrete values.

**Owner**: ui-core

**Estimate**: 2h

**Dependencies**: none

**Target milestone**: M1

**Acceptance test**: `uv run pytest tests/unit/ui/test_theme_wrapping.py -q`

**Files/modules touched**:
- src/tunacode/constants.py
- tests/unit/ui/test_theme_wrapping.py

**Steps**:
1. In `src/tunacode/constants.py`, add explicit built-in fallback metadata for the color fields TunaCode copies from Textual themes (`foreground`, `background`, `surface`, `panel`) so built-ins with missing/default placeholders have concrete values available during wrapping.
2. Update `_wrap_builtin_theme(...)` to preserve already-concrete color fields, but replace `None` and `ansi_default` values with the new fallback metadata before constructing the replacement `Theme`.
3. Keep the existing contract-variable merge behavior unchanged; this task is only about hardening theme object color fields before registration.
4. Add `tests/unit/ui/test_theme_wrapping.py` with targeted assertions for `dracula`, `textual-dark`, `textual-light`, and `textual-ansi`, proving the wrapped theme objects expose concrete, non-default values for the copied color fields.
5. Run the acceptance test and confirm the wrapped-theme fixtures cover the risky built-ins called out in the research docs.

### T002: Normalize Rich segment styles before Textual filter execution

**Summary**: Add a UI-local render-safety helper that converts unresolved default/ANSI Rich colors to truecolor fallbacks and pre-computes `dim` styling so `SelectableRichVisual` never feeds unsafe segment styles into `ANSIToTruecolor`.

**Owner**: ui-core

**Estimate**: 3h

**Dependencies**: T001

**Target milestone**: M2

**Acceptance test**: `uv run pytest tests/unit/ui/test_render_safety.py -q`

**Files/modules touched**:
- src/tunacode/ui/render_safety.py
- src/tunacode/ui/widgets/chat.py
- src/tunacode/ui/welcome.py
- tests/unit/ui/test_render_safety.py

**Steps**:
1. Create `src/tunacode/ui/render_safety.py` with helpers that accept a Rich `Style`, the active app ANSI theme, and concrete fallback foreground/background colors, then return a style safe for Textual 4.0.0 filter processing.
2. In that helper, resolve any Rich color whose `triplet` is `None` by using the same terminal-theme conversion path Textual uses for ANSI/default colors; when conversion still yields a default placeholder, replace it with the supplied fallback foreground/background color.
3. In the same helper, detect `style.dim`, blend the resolved foreground toward the resolved background using Textual's current dimming factor, and clear the `dim` flag so Textual does not call `dim_color(...)` again on a default background.
4. Update `src/tunacode/ui/widgets/chat.py` so `SelectableRichVisual.render_strips(...)` normalizes each segment style before adding offset metadata and selection highlighting.
5. Update `src/tunacode/ui/welcome.py` so the ANSI logo text produced by `generate_logo()` is normalized through the same helper before it is written to the chat container.
6. Add `tests/unit/ui/test_render_safety.py` with direct cases for the reproduced failure mode: `dim=True` plus `RichColor.default()` background, default-color logo spans from `Text.from_ansi(...)`, and already-truecolor styles that should remain unchanged.

### T003: Add a startup and theme-switch crash regression harness

**Summary**: Add one integration test that exercises the real TunaCode app startup path and switches through the known risky themes while dim/default-color renderables are present in chat.

**Owner**: qa-ui

**Estimate**: 2.5h

**Dependencies**: T002

**Target milestone**: M3

**Acceptance test**: `uv run pytest tests/integration/ui/test_theme_render_crash_regression.py -q`

**Files/modules touched**:
- tests/integration/ui/test_theme_render_crash_regression.py

**Steps**:
1. Add `tests/integration/ui/test_theme_render_crash_regression.py` using `TextualReplApp(state_manager=StateManager())` and `app.run_test()` under temporary `HOME`/`XDG_DATA_HOME` directories so the real startup path mounts normally.
2. Let app startup render the welcome screen, then append one additional chat renderable containing explicit `dim` styling to keep the historically failing segment shape present during the test.
3. In the same test, assign `app.theme` through `dracula`, `textual-light`, `textual-dark`, and `textual-ansi`; include the live-preview path by pushing `ThemePickerScreen` and moving the highlighted option if that is the shortest way to hit the real preview code.
4. Assert that no exception escapes the pilot session and that the chat container still contains mounted `.chat-message` widgets after the theme changes complete.
5. Keep the regression focused on the crash condition only; do not add snapshot/assertion noise about visual details.

### T004: Refresh developer docs and AGENTS metadata for render safety

**Summary**: Document the new render-safety layer for future maintainers and satisfy the repository requirement to refresh `AGENTS.md` when `src/` changes.

**Owner**: docs

**Estimate**: 1h

**Dependencies**: T003

**Target milestone**: M4

**Acceptance test**: `uv run python scripts/check_agents_freshness.py`

**Files/modules touched**:
- docs/modules/ui/ui.md
- docs/ui/css-architecture.md
- AGENTS.md

**Steps**:
1. Update `docs/modules/ui/ui.md` to mention that chat renderables pass through a UI-local render-safety normalization step before Textual selection/filter handling.
2. Update `docs/ui/css-architecture.md` anywhere it describes theme preview or welcome/chat rendering so it notes the built-in-theme hardening and pre-filter Rich style normalization added for Textual 4.0.0.
3. Update `AGENTS.md` `Last Updated` and add a concise note under the UI structure/guidance sections that `src/tunacode/ui/render_safety.py` and theme wrapping are part of the startup/theme stability path.
4. Keep documentation changes strictly developer-facing; do not expand into release notes or user-facing README edits unless execution uncovers a user-visible CLI contract change.
5. Run the acceptance script and confirm the repo still considers `AGENTS.md` current after the source changes.

### T005: Investigate unresolved built-in theme fields as an architecture follow-up

**Summary**: Capture the broader design smell around TunaCode wrapping Textual built-in themes with unresolved visual contract fields, so the current crash fix can stay local while a later pass decides whether theme wrapping should be narrowed, redesigned, or removed.

**Owner**: architecture

**Estimate**: 2h

**Dependencies**: T004

**Target milestone**: follow-up / not on current execution path

**Acceptance test**: n/a (research / plan follow-up)

**Files/modules touched**:
- `.artifacts/research/`
- `.artifacts/plan/`

**Steps**:
1. Audit why TunaCode re-registers Textual built-in themes instead of consuming them directly, and document which invariants TunaCode currently expects from wrapped theme objects.
2. Enumerate every built-in theme field TunaCode reads or implicitly relies on during startup, theme switching, and render fallback resolution.
3. Decide whether built-in theme wrapping should remain a supported internal contract, be reduced to contract-variable injection only, or be replaced with a different integration path.
4. Produce a follow-up artifact that separates immediate crash-workaround logic from any broader theme-architecture cleanup, including risks and migration constraints.
5. Keep this work out of the current execution patch unless the narrow crash fix proves impossible without it.

## Risks & Mitigations

- Textual may change its internal dimming factor or ANSI conversion behavior in a future upgrade.
  - Mitigation: isolate TunaCode's workaround in one helper module and describe the Textual 4.0.0 dependency in code comments/tests.
- Theme wrapper hardening could accidentally change the appearance of built-in themes more broadly than intended.
  - Mitigation: only replace `None`/`ansi_default` fields and leave already-concrete theme properties untouched.
- The startup crash may depend on the combination of welcome ANSI spans and generic dim text rather than either one alone.
  - Mitigation: keep both inputs in the integration regression so execution validates the mixed render path explicitly.
- App-level tests can become flaky if they depend on theme-picker timing.
  - Mitigation: prefer direct `app.theme = ...` assignments unless preview-screen events are required to reach uncovered code.

## Test Strategy

- T001 adds one unit test file proving wrapped built-in themes no longer expose unsafe unresolved colors.
- T002 adds one unit test file proving the new render-safety helper resolves default/ANSI colors and clears `dim` safely.
- T003 adds one integration regression file that exercises the real app startup and theme-change path.
- T004 runs the existing `scripts/check_agents_freshness.py` gate after the source/docs update.

## References

- Research doc: `.artifacts/research/2026-04-02_18-10-50_textual-dim-crash.md` — `Structure`, `Key Files`, `Patterns Found`, `Observed Local Reproduction`
- Supporting research doc: `.artifacts/research/2026-03-31_11-32-31_theme-switch-dim-background-crash.md` — `Theme Object Construction`, `Chat Widget / Selection Path`, `ANSI Theme Values Matching the Traceback`
- `src/tunacode/ui/welcome.py:29`
- `src/tunacode/ui/widgets/chat.py:25`
- `src/tunacode/constants.py:117`
- `src/tunacode/ui/app.py:118`
- `.venv/lib/python3.11/site-packages/textual/filter.py:128`
- `.venv/lib/python3.11/site-packages/textual/filter.py:220`

## Final Gate

- **Output summary**: `.artifacts/plan/2026-04-02_18-14-37_textual-dim-crash/`, 4 milestones, 5 tickets total, 4 tickets on the current execution path
- **Next step**: proceed to execute-phase with `.artifacts/plan/2026-04-02_18-14-37_textual-dim-crash/PLAN.md`
