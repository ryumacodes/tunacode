---
id: tun-d495
status: closed
deps: [tun-dc79]
links: []
created: 2026-01-26T23:13:14Z
type: task
priority: 0
assignee: tunahorse1
tags: [prompt-migration]
---
# Simplify load_system_prompt() in agent_config.py

Replace load_system_prompt() function with simple file read. Remove SectionLoader, compose_prompt, template selection, and local mode logic. Keep resolve_prompt() call for dynamic placeholders.

