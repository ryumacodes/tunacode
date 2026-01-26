---
id: t-46de
status: closed
deps: []
links: []
created: 2026-01-26T06:05:25Z
type: task
priority: 2
parent: t-69f0
tags: [architecture, types, callbacks]
---
# Define explicit callback type aliases in types/

Define explicit callback type aliases for boundary surfaces.

Scope:
- Tool result callbacks
- Plan approval callbacks
- Streaming callbacks

Location: src/tunacode/types/callbacks.py (or new file)

Acceptance:
- All callback signatures have named TypeAlias definitions
- No Callable[..., Any] at boundaries
- Docstrings explain contract (preconditions, postconditions)
