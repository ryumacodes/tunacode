---
title: Development Workflows
summary: Index of the repository's accepted development workflows.
when_to_read:
  - When choosing a workflow for a task
  - When navigating the workflow docs
last_updated: "2026-04-04"
---

# Development Workflows

This directory is the map for accepted development workflows in `tunacode-cli`.

Use this README as the index. Each workflow should live in its own Markdown
file so the guidance stays focused and easy to maintain.

## Workflow Map

- `FEATURES.md` — adding or extending product behavior.
- `DEBUG.md` — reproducing, isolating, and fixing defects.
- `HOTFIX.md` — urgent production-facing corrections with minimal scope.
- `DOCS.md` — documentation updates and workflow maintenance.
- `QA.md` — validation, checks, and handoff readiness.
- `HARNESS.md` — code-quality harness, local gates, and CI enforcement.
- `DREAM.md` — random exploration, ideation, and vibing only; use clearly
  labeled branches that make it obvious this is a sparring session rather than
  committed feature delivery.

## How To Use This Directory

1. Start in this README to choose the workflow that matches the task.
2. Open the dedicated Markdown file for the workflow you are executing.
3. Keep workflow-specific rules in that file instead of growing this index.

## Authoring Rule

When a workflow grows beyond a short summary, create or update its dedicated
Markdown file and keep this README as the map only.
