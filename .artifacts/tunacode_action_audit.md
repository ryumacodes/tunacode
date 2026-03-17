# TunaCode Action Audit (UI + Command Surface)

Created: 2026-03-17
Scope: Actions available from the TunaCode editor input and keybindings.

## Source of truth used
- `src/tunacode/ui/command_registry.py` (registered slash commands)
- `src/tunacode/ui/commands/__init__.py` (routing for `/`, `!`, and legacy `exit`)
- `src/tunacode/ui/app.py` (keybindings and ESC behavior)
- `src/tunacode/ui/esc/handler.py` (cancel priority)
- `src/tunacode/ui/widgets/editor.py` (enter submit, `!` behavior)
- `src/tunacode/ui/widgets/file_autocomplete.py` (`@` file mentions)
- `src/tunacode/ui/widgets/command_autocomplete.py` and `skills_autocomplete.py`

---

## 1) Action inventory

### A. Regular input actions
| Action | Syntax / Key | Behavior |
|---|---|---|
| Agent message | `any text` + Enter | Queues a normal request to the agent loop. |
| Shell command | `!<cmd>` + Enter | Runs command via `ShellRunner`; prints panel with stdout/stderr/exit code. |
| Legacy exit | `exit` + Enter | Exits app (legacy alias). |

### B. Slash commands (registered)
| Command | Usage | Behavior summary |
|---|---|---|
| `/help` | `/help` | Shows command table. |
| `/cancel` | `/cancel` | Cancels active request or running shell command (same action as ESC binding). |
| `/clear` | `/clear` | Clears chat display + transient runtime state, preserves session messages for `/resume`. |
| `/compact` | `/compact` | Forces context compaction and reports reclaimed tokens / skip / error. |
| `/debug` | `/debug` | Toggles debug logging on/off. |
| `/exit` | `/exit` | Exits app. |
| `/model` | `/model [provider:model]` | Opens picker (no args) or switches directly (with arg). |
| `/resume` | `/resume [list\|load <id>\|delete <id>]` | Session list/load/delete flows. |
| `/skills` | `/skills [loaded\|clear\|search <query>\|<exact-name>]` | Browse/search/load/clear session skills. |
| `/theme` | `/theme [name]` | Opens picker (no args) or switches directly (with arg). |
| `/thoughts` | `/thoughts` | Toggles thought/reasoning panel visibility. |
| `/update` | `/update` | Checks updates; may open install confirmation flow. |

### C. Keyboard + UI actions
| Action | Key | Behavior |
|---|---|---|
| Cancel current operation | `Esc` | Priority: cancel request task first, else cancel running shell command. |
| Toggle context rail | `Ctrl+e` | Shows/hides Session Inspector panel (if terminal width allows). |
| Copy selection | `Ctrl+y` or `Ctrl+Shift+c` | Copies current text selection to clipboard integration path. |
| Submit input | `Enter` | Submits editor content. |

### D. Assisted input actions
| Action | Trigger | Behavior |
|---|---|---|
| Command autocomplete | Start with `/` | Suggests slash commands while editing command name. |
| Skills autocomplete | Start with `/skills ` | Suggests subcommands and skill names. |
| File autocomplete | Type `@` path prefix | Suggests project files for insertion. |
| Bash mode helper | Type `!` at line start | Auto-inserts `! ` and toggles shell-mode styling. |

---

## 2) tmux test checklist (one-by-one)
Session: `tunacode_demo`
Pane 0: TunaCode UI
Pane 1: Shell helper
Evidence log: `.artifacts/tmux_action_audit_run.log`

Status key: `PASS`, `PARTIAL`, `DEFERRED`

| ID | Action under test | Input / key | Status | Evidence / notes |
|---|---|---|---|---|
| T01 | Help table | `/help` | PASS | Command table rendered with slash commands and `!<cmd>`. |
| T02 | Regular message path | `Reply with EXACT: audit-ok` | PASS | Agent returned `audit-ok`. |
| T03 | Thoughts toggle ON/OFF | `/thoughts` twice | PASS | Notifications observed for thought panel toggle (OFF then ON). |
| T04 | Skills catalog | `/skills` | PASS | Skills panel rendered (catalog content shown). |
| T05 | Skills search | `/skills search execute` | PASS | Search command executed; notification showed no matches for query. |
| T06 | Skills load | `/skills execute-phase` | PARTIAL | Command path works; no exact skill with that name in this runtime catalog. |
| T07 | Skills loaded list | `/skills loaded` | PASS | Loaded skills panel rendered as `(none)`. |
| T08 | Skills clear | `/skills clear` | PASS | Notification and panel confirmed skills cleared. |
| T09 | Bang shell command | `!pwd` | PASS | Shell panel rendered with cwd and stdout `/home/fabian/tunacode`. |
| T10 | `/cancel` cancels running shell | `!sleep 30` then `/cancel` | PARTIAL | `/cancel` usage path verified; cancel-during-running-shell was inconclusive via tmux automation. |
| T11 | `Esc` cancels running shell | `!sleep 30` then `Esc` | PARTIAL | ESC eventually freed shell runner (subsequent shell commands succeeded); cancellation toast was inconsistent in detached tmux capture. |
| T12 | `Esc` cancels active request | long prompt then `Esc` | PASS | `Cancelled` notification shown during active request. |
| T13 | Compact command | `/compact` | PASS | Compaction completed: `9 messages`, `~594 tokens reclaimed`. |
| T14 | Debug toggle | `/debug` twice | PASS | Notifications for `Debug mode: ON` then `OFF`; debug log file message shown when ON. |
| T15 | Theme direct set | `/theme tunacode` | PASS | Notification: `Theme: tunacode`. |
| T16 | Model direct set | `/model minimax:MiniMax-M2.5` | PASS | Notification: `Model: minimax:MiniMax-M2.5`. |
| T17 | Clear command | `/clear` | PASS | Notification: `Cleared agent state (messages preserved for /resume)`. |
| T18 | Context panel toggle key | `Ctrl+e` twice | PARTIAL | Keybinding fired; terminal width constraint notification (`requires at least 80 columns`). |
| T19 | Resume flow entry | `/resume` | PASS | Session picker opened; selecting current session loaded successfully (`Session loaded`). |
| T20 | Update flow entry | `/update` | PASS | Update check ran: `Already on latest version (0.1.93)`. |
| T21 | Exit command | `/exit` | DEFERRED | Keep session alive unless explicitly requested. |
| T22 | Legacy exit | `exit` | DEFERRED | Keep session alive unless explicitly requested. |

---

## 3) Safety notes
- `/exit` and `exit` intentionally deferred to avoid killing active session during audit.
- `/update` can install packages; only flow-entry check should be done unless explicitly approved.
- `/resume delete` mutates persisted sessions; avoid destructive subcommands without explicit instruction.
