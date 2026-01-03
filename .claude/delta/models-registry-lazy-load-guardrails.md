---
title: Models Registry Lazy Load and Model Picker Guardrails
link: models-registry-lazy-load-guardrails
type: delta
ontological_relations:
  - relates_to: [[kb-claude-code-touchpoints]]
tags:
  - models
  - registry
  - lazy-load
  - ui
  - performance
  - behavior-change
created_at: 2026-01-03T00:34:17Z
updated_at: 2026-01-03T00:34:17Z
uuid: 9682fcff-c31f-4cc6-925a-c798a71e1539
---

# Summary

The bundled models registry is no longer touched during startup or session load. Model data is loaded only when the user explicitly enters model selection, and UI list rendering is guarded to avoid enumerating huge unfiltered lists.

# Motivation

Users should never experience a surprise registry load or massive list render during startup. This change prevents accidental "logic bomb" behavior (big reads and long UI renders) and keeps explicit control in the `/model` flow.

# Changes

- Added a cached-registry accessor and routed context window/pricing lookups through it.
- `/model` now explicitly loads the registry before applying a direct model change.
- Model and provider pickers cap unfiltered lists and show a disabled hint to type and filter.
- Introduced `MODEL_PICKER_UNFILTERED_LIMIT` to document and centralize the guardrail.

# Behavioral Impact

- Startup and session load no longer read `models_registry.json`.
- Context window and pricing are defaulted until the registry is loaded (usually via `/model`).
- The picker UI shows a truncated list by default and avoids rendering massive lists.

# Notes

- If accurate pricing or context limits are required immediately, users should invoke `/model` once.
- Setup screens still load the registry when shown (first-run onboarding remains explicit).
