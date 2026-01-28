---
id: tun-81da
status: closed
deps: []
links: []
created: 2026-01-27T22:52:23Z
type: bug
priority: 2
assignee: tunahorse1
tags: [tools, grep, error-handling]
---
# Grep: clarify hybrid TooBroadPatternError handling

Hybrid search can raise TooBroadPatternError ambiguously when one strategy returns empty; clarify logic so error reflects both strategies timing out.


## Notes

**2026-01-27T22:59:46Z**

Updated hybrid TooBroadPatternError logic: now raise only when both strategies time out (all results are TooBroadPatternError). Staged grep.py.
