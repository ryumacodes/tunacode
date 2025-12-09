---
title: pattern — typed capture with validation habit
link: kb-claude-capture-pattern
type: patterns
ontological_relations:
  - relates_to: [[kb-claude-memory-anchor]]
  - relates_to: [[kb-claude-commands-cheatsheet]]
tags:
  - kb-claude
  - pattern
  - validation
created_at: 2025-12-09T19:54:08Z
updated_at: 2025-12-09T19:54:08Z
uuid: 205dd37e-3b64-4031-ae12-55837bd65638
---
Repeatable approach for recording knowledge in this repo.
1) Run `kb-claude search <keyword>` to avoid duplicates.
2) Use `kb-claude new "<Title>" -t <type>` to enforce metadata, relations, and timestamps.
3) Link related entries with `kb-claude link` to keep ontology traversable.
4) Run `kb-claude validate --strict` and regenerate the manifest before committing.
This pattern keeps the knowledge base lean, searchable, and trustworthy.
