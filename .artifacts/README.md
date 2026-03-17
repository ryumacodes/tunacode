# Artifact Frontmatter Standard

All markdown files in these directories must use the same YAML frontmatter pattern:

- `anchors/`
- `debug_history/`
- `plans/`
- `research/`

## Required frontmatter

```yaml
---
title: auth module broken after drizzle kit upgrade
link: auth-module-broken
type: debug_history
ontological_relations:
  - relates_to: [[drizzle-docs]]
tags: [dependencies, auth]
uuid: 123e4567-e89b-12d3-a456-426614174000
created_at: 2025-10-23T14:00:00Z
---
```

## Notes

- Frontmatter must appear at the very top of the file.
- Keep keys in this order.
- Use valid YAML.
- `created_at` must be ISO-8601 UTC format.
- `uuid` must be a valid UUID string.
- `type` should reflect the document kind (for example: `debug_history`, `plan`, `research`, `anchor`).
