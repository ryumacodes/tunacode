---
title: kb-claude quick commands
link: kb-claude-commands-cheatsheet
type: cheatsheets
ontological_relations:
  - relates_to: [[kb-claude-overview]]
tags:
  - kb-claude
  - commands
  - workflow
created_at: 2025-12-09T19:54:08Z
updated_at: 2025-12-09T19:54:08Z
uuid: 479e656c-e10f-452b-8de3-fa89519a8ccb
---
Short reminders for the CLI flow.
- `kb-claude init`: scaffold .claude/ layout inside a repo.
- `kb-claude new "Title" -t <type>`: guided entry creation with tags, relations, timestamps, UUIDs, and correct placement.
- `kb-claude search <keyword>`: case-insensitive search across metadata and body text.
- `kb-claude validate [--strict]`: parse every entry and flag missing metadata or slug mismatches; run before commits.
- `kb-claude manifest`: rebuild `.claude/manifest.md` summarizing the knowledge base.
- `kb-claude link source target`: add reciprocal `ontological_relations` between slugs.
