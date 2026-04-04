---
title: Code Standards
summary: Repository coding standards and guardrails for keeping changes simple and scoped.
when_to_read:
  - When editing source code
  - When reviewing local style and complexity rules
last_updated: "2026-04-04"
---

# CODE-STANDARDS.md

## Purpose
This document defines coding standards for TunaCode to avoid unnecessary defensive complexity in an already complex codebase.


 - minimal changes
 - no extra abstractions
 - no defensive layers
 - one scoped step at a time

abstractions must be earned
complexity must be ground down to its ultimate truth
never allows the "it passess" to beat common sense
legacy logic must be destroyed when refactoring, half cutovers cuase chaos, if you can cut it overclean in a few files you have a project not an issue



## Case Study: Defensive Slop (What went wrong)
A recent change introduced duplicate and fallback logic for `max_iterations`:
- hardcoded fallback values were added in code (`15`, `40`)
- runtime logic drifted away from the real source of truth
- extra coercion/normalization layers were added where the data shape was already known

This is exactly the kind of complexity we do **not** want.

## Rule 1: Single Source of Truth
If a value has an established canonical source, read it there directly.

For `max_iterations`, the source of truth is:
- `~/.config/tunacode.json`
- path: `settings.max_iterations`

Do not add duplicate defaults or alternate fallbacks in unrelated modules.

## Rule 2: No Redundant Defensive Layers
Most of our data paths are known and typed.
Do not add extra “just in case” coercion/parsing wrappers when:
- data origin is controlled
- shape is established
- existing code already guarantees structure

Every extra defensive layer adds:
- cognitive load
- more failure modes
- harder debugging
- harder maintenance

## Rule 3: Validate at Boundaries, Not Everywhere
Validation belongs at true trust boundaries (user/file/network inputs).
Inside internal typed flows, keep code direct and simple.

Bad pattern:
- repeated re-validation and remapping deep in internal runtime code

Good pattern:
- validate once at boundary
- consume directly in core logic

## Rule 4: Do Not Reintroduce Legacy Fallbacks
Never copy stale constants/fallbacks from deleted or transitional modules without explicit approval.

If a module is removed, do not “recreate” old behavior by default.
First confirm the intended source of truth and current architecture.

## Rule 5: Complexity Budget Is Real
This repository is already layered and non-trivial.
Do not add abstraction unless it clearly reduces complexity.

Heuristic:
- If the code gets longer, more indirect, and harder to trace, it is probably wrong.

## Rule 6: No Interface Stubs for Concrete Internal Models
If a runtime value is already a concrete internal model type, do not add local protocol/stub layers just to call methods it already owns.

Examples of what to avoid in internal typed paths:
- local `Protocol` wrappers for `model_dump()`
- stub bodies like `raise NotImplementedError` for methods that are never real implementations in this module

Use the concrete type directly.

## Rule 7: No Runtime Re-validation After Internal Typing
Once data is typed and validated at a boundary, do not repeatedly re-check method return shape in core flow.

Examples to avoid in internal typed paths:
- repeated `isinstance(..., dict)` checks after `model_dump(exclude_none=True)`
- extra guard rails around established internal message models

Boundary validation is required. Internal re-validation is not.

## Practical Checklist (Required before merge)
- [ ] Is this value read from its canonical source?
- [ ] Did I avoid introducing duplicate defaults?
- [ ] Did I avoid adding redundant coercion/parsing in internal paths?
- [ ] Did I avoid protocol/stub indirection for concrete internal model types?
- [ ] Did I avoid repeated runtime shape checks after boundary validation?
- [ ] Is this abstraction necessary, or is it just defensive layering?
- [ ] Can another developer trace this path in under 60 seconds?

## Team Standard
Do not ship defensive slop.
Prefer direct, typed, source-of-truth-driven code paths.
In this project: simpler code is safer code.
