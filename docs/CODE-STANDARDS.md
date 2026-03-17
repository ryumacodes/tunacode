# CODE-STANDARDS.md

## Purpose
This document defines coding standards for TunaCode to avoid unnecessary defensive complexity in an already complex codebase.

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

## Practical Checklist (Required before merge)
- [ ] Is this value read from its canonical source?
- [ ] Did I avoid introducing duplicate defaults?
- [ ] Did I avoid adding redundant coercion/parsing in internal paths?
- [ ] Is this abstraction necessary, or is it just defensive layering?
- [ ] Can another developer trace this path in under 60 seconds?

## Team Standard
Do not ship defensive slop.
Prefer direct, typed, source-of-truth-driven code paths.
In this project: simpler code is safer code.
