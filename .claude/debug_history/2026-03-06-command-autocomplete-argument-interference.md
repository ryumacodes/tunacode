---
title: Slash-command autocomplete intercepted `/skills` argument navigation
link: command-autocomplete-argument-interference
type: bugfix
path: src/tunacode/ui/widgets/command_autocomplete.py
tags:
  - ui
  - autocomplete
  - commands
  - skills
created_at: 2026-03-06T22:35:00-06:00
updated_at: 2026-03-06T22:35:00-06:00
---

## Summary

Fixed the root cause of broken `/skills` navigation: the generic slash-command autocomplete was still building candidates while the user was editing command arguments, so arrow and Enter keys could be consumed by the wrong dropdown.

## Trigger

Typing `/skills ...` correctly opened the skills dropdown, but pressing Down caused the hidden slash-command autocomplete to activate and move its own highlight. Enter could then complete `/cancel`, `/compact`, or another slash command instead of the highlighted skill.

## Changes

- Tightened `CommandAutoComplete.get_candidates()` to return candidates only while the user is editing the command-name region before the first space.
- Reused the same command-name parser already used by visibility logic.
- Added focused tests proving command autocomplete is inactive during `/skills` argument editing.
- Added an end-to-end headless UI test proving `/skills ` + Down + Enter selects the highlighted skill, not a slash command.

## Tests

- `uv run pytest tests/unit/ui/test_command_autocomplete.py tests/unit/ui/test_skills_autocomplete.py -q`
- `uv run ruff check src/tunacode/ui/widgets/command_autocomplete.py tests/unit/ui/test_command_autocomplete.py tests/unit/ui/test_skills_autocomplete.py`
