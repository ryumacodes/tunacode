---
title: Research Agent State Manager and API Key Injection Fix
link: research-agent-state-manager-fix
type: delta
ontological_relations:
  - relates_to: [[kb-claude-code-touchpoints]]
tags:
  - research-agent
  - state-manager
  - api-key
  - bug-fix
  - pr-170
created_at: 2025-12-13T23:45:00Z
updated_at: 2025-12-13T23:45:00Z
uuid: a0e4a89f-1cc7-4a6b-b680-e6f273b9a119
---

# PR #170: Research Agent API Key Access Fix

## Summary

Fixed research agent failing with API key errors due to incorrect state manager initialization and model instantiation.

## Root Cause

1. `delegation_tools.py:62` created `StateManager()` instead of passing the parent's `state_manager`, losing user config including API keys
2. `research_agent.py` passed raw model string directly instead of using `_create_model_with_retry()` which injects API keys from user config

## Changes

### delegation_tools.py
- **Before:** `state_manager=StateManager()` (isolated, empty config)
- **After:** `state_manager=state_manager` (shares parent's config)

### research_agent.py
- Added HTTP retry transport with `AsyncTenacityTransport` and `RetryConfig`
- Added `_create_model_with_retry()` call to properly inject API keys
- Added symbolic constant `MAX_RETRY_WAIT_SECONDS = 60` (per CodeRabbit review)
- Fixed leading space in "FILE READ LIMIT REACHED" message (per CodeRabbit review)

## Files Modified

| File | Change |
|------|--------|
| `src/tunacode/core/agents/delegation_tools.py` | Pass parent state_manager |
| `src/tunacode/core/agents/research_agent.py` | Add retry transport, use `_create_model_with_retry()` |

## Behavioral Impact

- Research agent now correctly accesses API keys from user config
- Research agent now has HTTP retry logic matching main agent pattern
- No breaking changes to public API

## Related Commits

- `688f3b4` - Initial fix
- `6a0d176` - CodeRabbit review feedback (leading space, magic number)
- `67f0414` - Squash merge to master
