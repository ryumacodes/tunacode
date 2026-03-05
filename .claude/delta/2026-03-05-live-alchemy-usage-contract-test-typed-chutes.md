---
title: Update live alchemy usage contract test for typed tinyagent context and chutes provider
type: delta
link: live-alchemy-usage-contract-test-typed-chutes
path: tests/integration/core/test_tinyagent_alchemy_usage_contract_live.py
depth: 1
seams: [M]
ontological_relations:
  - affects: [[integration-tests]]
  - affects: [[tinyagent-contracts]]
  - affects: [[provider-selection]]
tags:
  - tests
  - tinyagent
  - alchemy
  - chutes
  - typing
created_at: 2026-03-05T04:20:00+00:00
updated_at: 2026-03-05T04:20:00+00:00
uuid: f26fc65a-a8b4-4a13-b9e2-d95bc4f7b606
---

# Update live alchemy usage contract test for typed tinyagent context and chutes provider

## Summary

Fixed the live alchemy usage contract integration test after the tinyagent typing upgrade.

## Changes

- Replaced dict-based context message payloads with typed tinyagent models:
  - `UserMessage`
  - `TextContent`
- Replaced dict-based stream options with `SimpleStreamOptions`.
- Switched the live provider from OpenRouter to Chutes:
  - env var: `CHUTES_API_KEY`
  - base URL: `https://llm.chutes.ai/v1/chat/completions`
  - model: `deepseek-ai/DeepSeek-V3.1`
- Added `.env` fallback reader for `CHUTES_API_KEY` so the live test can run from local dotenv config.
- Added explicit `max_tokens` cap in stream options to keep live calls bounded.

## Validation

- `uv run pytest tests/integration/core/test_tinyagent_alchemy_usage_contract_live.py -q -x` ✅
- `uv run pytest` ✅ (707 passed, 1 skipped)
