# Postmortem: Defensive message typing slop around `model_dump`

**Date:** 2026-03-17
**Scope:** Internal tinyagent message serialization paths

## Summary
A defensive typing/validation pattern was introduced in core serialization paths even though message types were already defined and controlled.

The pattern added:
- protocol stubs with `NotImplementedError`
- repeated runtime guards for `model_dump(exclude_none=True)` return shape
- `Any`/cast-heavy indirection in internal flows

This conflicted with `docs/CODE-STANDARDS.md` (single source of truth, no redundant defensive layers, validate at boundaries).

## What happened
The codebase had mixed strategies for the same operation (`message.model_dump(exclude_none=True)`):

- `src/tunacode/core/agents/main.py`
  - Local protocol `_ModelDumpableMessage(Protocol)` with stub method body.
  - Runtime check that serialized output was a `dict`.
- `src/tunacode/core/session/state.py`
  - Per-message runtime `isinstance` guards in `_serialize_messages()`.
  - Runtime check that `model_dump` returned `dict`.
- `src/tunacode/utils/messaging/adapter.py`
  - Runtime check that `model_dump` returned `dict`.

Result: inconsistent, defensive layering in internal typed code paths.

## Why this happened
1. **Type-check pressure in strict modules**
   - `core.agents` has stricter mypy constraints (`disallow_any_*`), which encouraged local typing workarounds.
2. **Pattern copy from dependency internals**
   - tinyagent defines a similar protocol stub (`ModelDumpable`) in its own types module, and that style was mirrored locally.
3. **No enforced repo-wide rule against internal re-validation**
   - Standards existed, but were not applied consistently in existing serialization code.

## Impact
- Increased cognitive load in critical message paths.
- Harder to trace actual source-of-truth data flow.
- Inconsistent implementation style across modules.
- Friction during maintenance and review.

## Resolution applied
Defensive layers were removed from internal typed serialization paths:

- `src/tunacode/core/agents/main.py`
  - Removed `_ModelDumpableMessage(Protocol)`.
  - Removed runtime “must return dict” check.
  - Use direct `message.model_dump(exclude_none=True)`.

- `src/tunacode/core/session/state.py`
  - Removed `_agent_message_types()` helper and per-item runtime guards in `_serialize_messages()`.
  - Removed runtime “must return dict” check.
  - Use direct typed serialization.

- `src/tunacode/utils/messaging/adapter.py`
  - Removed runtime “must return dict” check after `model_dump`.
  - Use direct typed serialization.

## Correct boundary model (going forward)
- **Boundary validation stays:** file/session load, external payload parsing, model validation at ingress.
- **Internal flow stays direct:** once typed as tinyagent message models, do not re-validate shape repeatedly.

## Prevention actions
1. During review, reject internal runtime re-validation of already-typed message objects.
2. Avoid local protocol stubs for methods guaranteed by canonical internal model types unless absolutely required.
3. Keep serialization idiom consistent across modules:
   - `message.model_dump(exclude_none=True)` directly in typed flows.
4. If strict typing friction appears, solve at the type boundary (narrow type aliases/annotations), not via extra runtime defensive code.

## Rule restatement
For this codebase: **no defensive slop in internal typed paths**.
Validate at boundaries once; keep core runtime code direct and traceable.
