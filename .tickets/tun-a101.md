---
id: tun-a101
status: closed
deps: []
links: []
created: 2026-01-28T00:35:15Z
type: bug
priority: 2
assignee: tunahorse1
tags: [logging, debug, streaming]
---
# Log model API error context in streaming debug

Current streaming error logging only records type+message and is debug-only. Capture available context (request_id, model name, iteration index, HTTP status/URL when available) and ensure errors are logged at non-debug level. Reference: memory-bank/research/2026-01-28_00-25-00_api-error-logging-gaps.md.

## Acceptance Criteria

- Streaming failures log request_id, model name, iteration index.
- When HTTPStatusError is present, log status code and request URL.
- Errors are visible outside debug-only lifecycle logging (e.g., error or warning).
- Update any related docs/codebase-map if behavior changes.


## Notes

**2026-01-28T00:35:51Z**

Superseded by tun-9d06 (context fields) and tun-4d1e (non-debug/error logging + HTTP status/URL).
