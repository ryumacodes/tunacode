---
id: tun-ba75
status: closed
deps: []
links: []
created: 2026-01-28T04:31:38Z
type: task
priority: 2
assignee: tunahorse1
tags: [refactor, dependency-direction]
---
# Move truncate_diagnostic_message from utils to tools/utils

Refactor: Move formatting helper to tools layer to eliminate cross-layer dependency

## Design

tools/lsp/__init__.py currently imports truncate_diagnostic_message from utils.formatting, creating a cross-layer edge (tools → utils). utils.formatting only contains this single 3-line function.

Move the function to tools/utils/formatting.py where it belongs as a tools-layer utility. tools/utils/ already contains text_match.py and ripgrep.py, making this the natural home.

## Acceptance Criteria

- truncate_diagnostic_message exists in tools/utils/formatting.py
- tools/lsp/__init__.py imports from tools.utils.formatting
- src/tunacode/utils/formatting.py deleted
- DEPENDENCY_LAYERS.dot updated (remove tools -> utils edge)

