---
id: tun-aee9
status: closed
deps: []
links: []
created: 2026-01-27T22:52:25Z
type: chore
priority: 3
assignee: tunahorse1
tags: [tools, grep, cleanup]
---
# Grep: DRY strategy info formatting

Strategy info string construction in execute is duplicated; extract to a helper to keep formatting consistent.


## Notes

**2026-01-27T23:01:03Z**

Extracted strategy formatting into _build_strategy_messages and removed duplicated string construction. Added MAX_CANDIDATE_FILES constant and used candidate_count variable. Staged grep.py.
