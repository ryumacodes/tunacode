---
title: Skills autocomplete selected the wrong skill for short prefixes
link: skills-autocomplete-selection-ranking
type: bugfix
path: src/tunacode/ui/widgets/skills_autocomplete.py
tags:
  - skills
  - ui
  - autocomplete
  - ranking
created_at: 2026-03-06T22:15:00-06:00
updated_at: 2026-03-06T22:15:00-06:00
---

## Summary

Fixed `/skills` autocomplete so short prefixes now prefer the best semantic skill match instead of an arbitrary fuzzy-match winner.

## Trigger

Typing `/skills de` and pressing Enter selected `dead-code-detector` ahead of `demo`, even though `demo` was the more specific prefix match the user intended.

## Changes

- Added `src/tunacode/skills/search.py` with deterministic skill-match ordering.
- Ranked exact name matches before prefix matches, prefix matches before substring matches, and description matches last.
- Broke prefix ties by shorter skill name first so concise exact-prefix skills win.
- Updated `SkillsAutoComplete` to preserve the candidate order it computes instead of letting fuzzy scoring reshuffle the dropdown.
- Updated `/skills` catalog filtering to use the same ordering logic as autocomplete.

## Tests

- Added unit coverage for skill ranking behavior.
- Added a headless TUI test proving `/skills de` + Enter selects `demo`, then Enter loads it.
