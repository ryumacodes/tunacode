---
title: Skills: legacy markdown loading, invalid-summary isolation, and casefold precedence
link: skills-legacy-loading-and-casefold-precedence
type: bugfix
path: src/tunacode/skills/
tags:
  - skills
  - loader
  - discovery
  - ui
created_at: 2026-03-06T20:30:00-06:00
updated_at: 2026-03-06T20:30:00-06:00
---

## Summary

Fixed three production issues in the skills rollout:

1. Legacy `SKILL.md` files without YAML frontmatter now load.
2. Local skills correctly override global skills on case-insensitive name collisions.
3. Invalid skill summaries no longer crash agent creation or the available-skills prompt block.

## Trigger

A real global skill (`debug-tunacode-api`) was plain markdown and raised `SkillFrontmatterError` during prompt construction. A second real-world issue was malformed frontmatter in one discovered skill poisoning `list_skill_summaries()` for the whole session.

## Changes

- `src/tunacode/skills/loader.py`
  - Added legacy markdown fallback when frontmatter is absent.
  - Derives the summary description from the first non-heading prose line, then heading, then a fallback string.
- `src/tunacode/skills/discovery.py`
  - Merges discovered skills by `casefold()` key so local beats global even for `demo` vs `Demo`.
- `src/tunacode/skills/registry.py`
  - Skips invalid skill summaries with a warning instead of aborting prompt construction.
  - Still loads selected skills strictly through `load_skill_by_name()`.
- `src/tunacode/ui/commands/skills.py`
  - Replaced `/skill` with `/skills`.
  - Added catalog browsing, `loaded`, `clear`, and search behavior.
- `src/tunacode/ui/context_panel.py`
  - Renamed the inspector zone to `Loaded Skills`.

## Tests

Added coverage for:

- legacy markdown skills without frontmatter
- local-over-global casefold collisions
- invalid discovered skills skipped from summary listing
- agent creation with legacy and invalid global skills present
- `/skills` command attach/search/clear behavior
