---
title: faq — how kb-claude differs from notes
link: kb-claude-faq
type: qa
ontological_relations:
  - relates_to: [[kb-claude-overview]]
  - relates_to: [[kb-claude-memory-anchor]]
tags:
  - kb-claude
  - faq
  - ontology
created_at: 2025-12-09T19:54:08Z
updated_at: 2025-12-09T19:54:08Z
uuid: d9f9e36e-ad86-4c52-9c43-f9e7df1d1ea0
---
Q: Why use kb-claude instead of ad-hoc notes?
A: It enforces typed Markdown with UUIDs, timestamps, and folder-based ontology so knowledge stays queryable and auditable in git.

Q: What metadata is mandatory?
A: `title`, `link`, `type`, `ontological_relations`, `tags`, `created_at`, `updated_at`, and `uuid`—matching the folder name for type.

Q: Where do rough ideas go?
A: Use `.claude/other/` for scratch notes that the CLI can ignore.
