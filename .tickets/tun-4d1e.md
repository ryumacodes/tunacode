---
id: tun-4d1e
status: closed
deps: []
links: []
created: 2026-01-28T00:35:49Z
type: bug
priority: 2
assignee: tunahorse1
tags: [logging, debug, streaming]
---
# Expose model API failures at non-debug log level

Streaming failures currently only log via lifecycle (debug-only). Add non-debug logging for model API errors; include HTTP status code and request URL when HTTPStatusError is present. Reference: memory-bank/research/2026-01-28_00-25-00_api-error-logging-gaps.md.

## Acceptance Criteria

- Streaming failures are logged at error/warn level (not only lifecycle/debug).
- When HTTPStatusError is present, log status code and request URL.

