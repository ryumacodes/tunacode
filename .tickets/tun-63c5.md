---
id: tun-63c5
status: in_progress
deps: []
links: []
created: 2026-01-27T22:28:41Z
type: task
priority: 2
assignee: tunahorse1
tags: [typing, mypy, batch4, ui]
---
# Batch 4: UI contract mismatches

Align Textual UI protocols and callbacks: ShellRunnerHost notify signature, AppForCallbacks post_message/status_bar typing, push_screen callback, logger TUI callback, run_worker typing. Fix mypy errors in src/tunacode/ui/app.py and related UI helpers.


## Notes

**2026-01-27T22:28:47Z**

Updated UI protocol typings in shell_runner and repl_support, aligned TextualReplApp callback types (StatusBarLike, notify signature, push_screen callback, run_worker return, TUI callback). Mypy passes for ui/app.py, repl_support.py, shell_runner.py.
