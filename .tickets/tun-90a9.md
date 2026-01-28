---
id: tun-90a9
status: closed
deps: []
links: []
created: 2026-01-27T22:52:21Z
type: task
priority: 2
assignee: tunahorse1
tags: [tools, grep, formatting]
---
# Grep: include context lines in formatted output

ResultFormatter._format_content currently ignores context_before/context_after. Update formatting to show context lines consistently.


## Notes

**2026-01-27T22:57:30Z**

Implemented context line rendering in ResultFormatter._format_content; added prefixes and output now includes context_before/context_after. Staged result_formatter.py.
