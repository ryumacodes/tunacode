---
title: Model API Error Logging Gaps
link: model-api-error-logging-gaps
type: doc
path: problem_statement_model_api_error_logging.md
depth: 0
seams: [S]
ontological_relations:
  - relates_to: [[streaming-logging]]
  - affects: [[core-streaming]]
tags:
  - logging
  - streaming
  - error-handling
created_at: 2026-01-27T18:34:08-06:00
updated_at: 2026-01-27T18:34:08-06:00
uuid: b458ad34-52a2-469e-9b61-6f5e62f1e920
---

## Summary
Streaming failures from pydantic-ai are logged only as exception type + message through debug-only lifecycle logging, which drops critical context and leaves production logs without a failure record.

## Context
The streaming exception handler logs only:
```
Stream failed: {type(e).__name__}: {e}
```
Available context in scope is not recorded:
- request_id (from the streaming context)
- model name (self.model)
- iteration index
- HTTP status code (HTTPStatusError.response)
- request URL (HTTPStatusError.request)

ModelAPIError originates in pydantic-ai, so the error payload itself cannot be expanded without additional logging at the tunacode layer. Reference: memory-bank/research/2026-01-28_00-25-00_api-error-logging-gaps.md.

## Root Cause
The handler logs only the exception’s string form and does so via lifecycle logging, which is debug-only, while omitting richer context already present in scope.

## Changes
None. Problem statement only.

## Behavioral Impact
Operators see only a terse debug log entry such as “Stream failed: ModelAPIError: Connection error,” and production logs have no corresponding failure record, making diagnosis and correlation difficult.

## Related Cards
- None
