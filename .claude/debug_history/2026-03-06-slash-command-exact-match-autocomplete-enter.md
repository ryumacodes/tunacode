---
title: Slash command autocomplete exact-match enter interception
link: slash-command-exact-match-autocomplete-enter
type: bugfix
path: src/tunacode/ui/widgets/command_autocomplete.py
tags:
  - ui
  - autocomplete
  - commands
  - textual
created_at: 2026-03-06T21:45:00-06:00
updated_at: 2026-03-06T21:45:00-06:00
---

## Summary

Fixed the generic slash-command autocomplete path so exact command matches no longer keep the dropdown open and steal Enter from command submission.

## Trigger

Typing an exact slash command like `/compact` or `/help` left the autocomplete visible because the dropdown item text included both the command and description. The upstream exact-match visibility check compared against the full rendered label, so Enter completed to `/command ` instead of submitting.

## Changes

- Added a helper that extracts the command-name editing region before the cursor.
- Added exact command-name matching against `COMMANDS`.
- Updated `CommandAutoComplete.should_show_dropdown()` to hide the dropdown once the typed command already exactly matches a registered command.
- Added focused UI tests covering exact-match dropdown hiding and Enter submission.

## Tests

- `uv run pytest tests/unit/ui/test_command_autocomplete.py tests/unit/ui/test_skill_command.py -q`
- `uv run ruff check src/tunacode/ui/widgets/command_autocomplete.py tests/unit/ui/test_command_autocomplete.py`
