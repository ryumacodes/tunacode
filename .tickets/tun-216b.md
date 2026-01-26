---
id: tun-216b
status: closed
deps: [tun-0de7]
links: []
created: 2026-01-26T21:58:42Z
type: task
priority: 2
assignee: tunahorse1
tags: [planning-deletion, phase4]
---
# Remove UI command and state references

Remove PlanCommand from commands/__init__.py, approval handling from app.py, PendingPlanApprovalState from repl_support.py, /plan mention from welcome.py, and plan_mode/plan_approval_callback from state.py

## Acceptance Criteria

App starts without plan-related attributes, /plan command no longer available

