# RequestContext Cutover Lesson (apply to debug_history)

## Why this was done
We removed slop caused by legacy cutover patterns and pass-through abstractions.

## What we changed
1. Removed legacy empty-response handler path from `src/tunacode/core/agents/main.py`.
2. Established request ID single source of truth:
   - `session.runtime.request_id`
3. Removed `RequestContext` pass-through plumbing.
4. Passed only required scalar (`max_iterations`) where needed.
5. Updated tests to remove `RequestContext` dependency.

## Source-of-truth rules used
- Request ID: `session.runtime.request_id`
- Max iterations: `session.user_config["settings"]["max_iterations"]`

## Anti-slop rules applied
- No defensive wrappers when shape/source are known.
- No duplicate carriers of the same data.
- No legacy half-cutover logic kept alive.
- No abstraction unless it reduces complexity.

## Concrete before/after pattern
- Before: create `RequestContext` and thread it through many methods that mostly did not use it.
- After: initialize runtime state once; pass only needed values directly.

## Debug-history lesson to carry forward
When touching `debug_history`:
1. Identify single source of truth first.
2. Map all callsites as: live-read vs pass-through vs dead.
3. Remove pass-through/dead layers.
4. Keep only direct, typed runtime flow.
5. Update tests to match simplified interfaces.
