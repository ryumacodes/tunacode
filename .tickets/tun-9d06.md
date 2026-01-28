---
id: tun-9d06
status: closed
deps: []
links: []
created: 2026-01-28T00:35:46Z
type: bug
priority: 2
assignee: tunahorse1
tags: [logging, streaming]
---
# Log streaming context (request_id/model/iteration)

Streaming error logging should include request_id, model name, and iteration index when failures occur. Reference: memory-bank/research/2026-01-28_00-25-00_api-error-logging-gaps.md.

## Acceptance Criteria

- Streaming failures log request_id, model name, iteration index.
- Log output includes these fields consistently.

