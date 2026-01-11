---
title: "Research – Shell Panel Standardization per NeXTSTEP UI Guidelines"
date: "2026-01-10"
owner: "claude"
phase: "Research"
tags: [shell, ui, nextstep, panel, bash-mode, input-output]
---

# Research – Shell Panel Standardization per NeXTSTEP UI Guidelines

**Date:** 2026-01-10
**Owner:** claude
**Phase:** Research

## Goal

Research the current `!shell` tool input/output implementation and identify gaps according to NeXTSTEP UI guidelines. The user reports that shell mode indication is minimal (just a "little line" in status bar) and output is "vomited out" without proper structure.

## Context

User wants to standardize the `!shell` command interface according to the NeXTSTEP UI handbook. Current issues identified:
- Users are not adequately informed when they enter shell mode
- Shell output lacks structured presentation
- Inconsistency between `!shell` (direct commands) and agent `bash` tool (which uses proper panels)

## Findings

### Relevant Files & Why They Matter

| File | Purpose |
|------|---------|
| `src/tunacode/ui/widgets/editor.py:32-33,96-110,173-185` | `!` prefix detection, bash-mode class toggle, status bar mode update |
| `src/tunacode/ui/shell_runner.py:20-27,94-129` | `ShellRunnerHost` protocol, subprocess execution, raw `Text` output to RichLog |
| `src/tunacode/ui/app.py:481-491` | Shell output interface: `write_shell_output()`, `start_shell_command()`, status callbacks |
| `src/tunacode/ui/widgets/status_bar.py:90-98` | `set_mode()` prepends `[bash mode]` to status left zone |
| `src/tunacode/ui/renderers/tools/bash.py` | **Reference**: 4-zone NeXTSTEP panel for agent bash commands |
| `src/tunacode/ui/renderers/tools/base.py:375-441` | **Reference**: Template method for 4-zone panel pattern |
| `src/tunacode/ui/styles/layout.tcss:96-98` | CSS rule: `Editor.bash-mode` gets green/success border |
| `src/tunacode/ui/styles/theme-nextstep.tcss:70-72` | CSS rule: Double cyan border for bash-mode in NeXTSTEP theme |
| `.claude/skills/neXTSTEP-ui/SKILL.md` | **Design principles**: modes must be visually apparent, 4-zone layout hierarchy |

### Current Architecture: Two-Path System

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         SHELL OUTPUT SYSTEM                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Path 1: User-initiated `!shell` commands                 │
│  ───────────────────────────────────────────────────────                   │
│  User types "!ls -la"                                                     │
│       → editor.py: on_key() detects "!" prefix                            │
│       → editor.py: _update_bash_mode() adds "bash-mode" CSS class         │
│       → status_bar.py: set_mode("bash mode") updates status text          │
│       → commands/__init__.py: handle_command() strips "!" and routes       │
│       → shell_runner.py: ShellRunner.start() creates subprocess           │
│       → shell_runner.py:126 write_shell_output(Text(output))              │
│       → app.py:485 rich_log.write(renderable) ← **PLAIN TEXT, NO PANEL** │
│                                                                          │
│  Path 2: Agent-initiated bash tool calls (via tool_panel_smart)         │
│  ───────────────────────────────────────────────────────                   │
│  Agent calls bash tool with structured result                             │
│       → panels.py: tool_panel_smart() routes to render_bash()             │
│       → bash.py: BashRenderer with 4-zone NeXTSTEP layout                 │
│       ├── Zone 1: Header (command + "ok"/"exit N" status)                │
│       ├── Zone 2: Parameters (cwd, timeout)                              │
│       ├── Zone 3: Viewport (stdout/stderr with syntax highlighting)      │
│       └── Zone 4: Status (line counts, duration)                         │
│       → app.py:377 rich_log.write(panel, expand=True) ← **FULL PANEL**   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Key Gaps Identified

#### Gap 1: Mode Indication is Subtle (NeXTSTEP Violation)

**NeXTSTEP Principle:** *Modes must be visually apparent at all times*

**Current Behavior:**
- Status bar text: `[bash mode] main ● ~/proj` (small text, left zone)
- Editor border: Green solid (dracula) or double cyan (NeXTSTEP theme)
- `mode-active` CSS class: **Added to status left zone but NO styling defined**

**Issue:** The mode indication relies on users noticing a small status bar change and border color change. Per NeXTSTEP anti-patterns, this qualifies as a **"hidden mode"** — users may not realize different rules apply.

**Reference:** `src/tunacode/ui/widgets/status_bar.py:90-98`
```python
def set_mode(self, mode: str | None) -> None:
    """Show mode indicator in status bar."""
    left = self.query_one("#status-left", Static)
    if mode:
        left.add_class("mode-active")  # ← No CSS styling for this class
        left.update(f"[{mode}] {self._location_text}")
```

#### Gap 2: Shell Output is Unstructured (NeXTSTEP Violation)

**NeXTSTEP Principle:** *Information hierarchy with zones - header, viewport, status*

**Current Behavior (`!shell` path):**
- Raw `Text()` object written directly to `RichLog`
- No panel, no border, no zones
- No syntax highlighting
- No metadata (command, exit code, duration)

**Reference:** `src/tunacode/ui/shell_runner.py:124-126`
```python
output = (stdout or b"").decode(SHELL_OUTPUT_ENCODING, errors="replace").rstrip()
if output:
    self.host.write_shell_output(Text(output))  # ← Plain text, no structure
```

**Comparison:**

| Feature | `!shell` (user) | `bash` tool (agent) |
|---------|-----------------|---------------------|
| Panel wrapper | ❌ None | ✅ Yes |
| Header (command + status) | ❌ None | ✅ Yes |
| Parameters zone | ❌ None | ✅ cwd, timeout |
| Viewport syntax highlighting | ❌ None | ✅ Smart lexer |
| Status zone (metrics) | ❌ None | ✅ Lines, duration |
| Border color coding | ❌ None | ✅ Green/warning |
| Timestamp | ❌ None | ✅ Yes |

#### Gap 3: Inconsistent User Experience

Users see two completely different output formats depending on whether they type `!ls` directly or the agent calls the bash tool:
- Direct command: plain text vomited into log
- Agent command: beautiful structured panel

This violates **NeXTSTEP consistency principle**: *Objects that look the same should act the same. Objects that act the same should look the same.*

## Key Patterns / Solutions Found

### Pattern 1: 4-Zone NeXTSTEP Panel Layout (Already Implemented)

**Location:** `src/tunacode/ui/renderers/tools/base.py:375-441`

The `BaseToolRenderer.render()` template method implements the standard 4-zone layout:

```
┌─────────────────────────────────────────────────┐
│ tool_name [status]              timestamp       │  ← Panel title/subtitle
├─────────────────────────────────────────────────┤
│ $ command                              ok       │  ← Zone 1: Header
│ cwd: /path    timeout: 30s                      │  ← Zone 2: Parameters
├─────────────────────────────────────────────────┤
│ stdout:                                        │
│ [formatted output with syntax highlighting]    │  ← Zone 3: Viewport
│                                                 │
├─────────────────────────────────────────────────┤
│ stdout: 42 lines   1.2s                        │  ← Zone 4: Status
└─────────────────────────────────────────────────┘
```

**Implementation pattern for reuse:**
```python
class BaseToolRenderer[G](Generic[G]):
    def parse_result(self, args, result) -> G | None
    def build_header(self, data, duration_ms) -> Text      # Zone 1
    def build_params(self, data) -> Text | None             # Zone 2
    def build_viewport(self, data) -> RenderableType        # Zone 3
    def build_status(self, data, duration_ms) -> Text       # Zone 4
```

### Pattern 2: ShellRunnerHost Protocol (Extension Point)

**Location:** `src/tunacode/ui/shell_runner.py:20-27`

The protocol defines the contract between shell execution and UI. Can be extended to support panel output:

```python
class ShellRunnerHost(Protocol):
    def notify(self, message: str, severity: str = "information") -> None: ...
    def write_shell_output(self, renderable: Text) -> None: ...  # ← Currently Text only
    def shell_status_running(self) -> None: ...
    def shell_status_last(self) -> None: ...
```

**Proposed extension:** Add `write_shell_panel(self, panel: Panel) -> None` method.

### Pattern 3: BashToolRenderer (Reference Implementation)

**Location:** `src/tunacode/ui/renderers/tools/bash.py`

Shows how to structure shell command output with:
- `BashData` dataclass for parsed result (lines 26-36)
- `parse_result()` regex patterns for structured parsing (lines 42-98)
- `_detect_output_type()` for smart syntax highlighting (lines 125-146)
- Zone builders following 4-zone pattern (lines 100-230)

## Knowledge Gaps

### Missing Context for Implementation

1. **Should `!shell` output match the agent `bash` tool exactly?**
   - Or should it be a simplified variant for user commands?
   - Does the user need cwd/timeout parameters visible for their own commands?

2. **Should shell panel be a separate dedicated screen or inline panel?**
   - NeXTSTEP panels are "secondary windows that support main window's task"
   - Current agent tool panels are inline (RichLog)
   - Shell could merit a dedicated modal screen for persistent shell sessions

3. **How should shell mode be made more apparent?**
   - Options: larger indicator, header bar, persistent overlay, dedicated shell screen
   - NeXTSCREEN guidelines suggest avoiding modes, but if necessary: visible, user-chosen, easy to exit

4. **Should `!shell` support interactive sessions?**
   - Current: one-shot commands with 30s timeout
   - Potential: persistent shell session with readline, tab completion, job control

## Proposed Direction

Based on NeXTSTEP principles and existing patterns:

1. **Standardize output format:** Make `!shell` use the same 4-zone panel layout as the agent `bash` tool
2. **Enhance mode indication:** Add a persistent visual indicator (header bar or prominent overlay) when in shell mode
3. **Unify code paths:** Share the `BashRenderer` or create a `ShellPanelRenderer` variant
4. **Follow NeXTSTEP modal tool guidelines:** Since shell is a modal tool, ensure:
   - Mode is visible (beyond just border + status text)
   - Mode is user-chosen (already true via `!` prefix)
   - Exit is obvious and immediate (already true via Esc)

## References

### Code References (with line numbers)

- **Shell input detection:** `src/tunacode/ui/widgets/editor.py:96-110,173-185`
- **Shell execution:** `src/tunacode/ui/shell_runner.py:94-129`
- **Shell output interface:** `src/tunacode/ui/app.py:481-491`
- **Status bar mode:** `src/tunacode/ui/widgets/status_bar.py:90-98`
- **Bash tool panel renderer:** `src/tunacode/ui/renderers/tools/bash.py:1-242`
- **Base 4-zone pattern:** `src/tunacode/ui/renderers/tools/base.py:375-441`
- **Panel routing:** `src/tunacode/ui/renderers/panels.py:476-523`

### Documentation References

- **NeXTSTEP UI Skill:** `.claude/skills/neXTSTEP-ui/SKILL.md`
- **Visual Reference:** `.claude/skills/neXTSTEP-ui/doomed_nextstep_reference.png`
- **Full Guidelines PDF:** `.claude/skills/neXTSTEP-ui/NeXTSTEP_User_Interface_Guidelines_Release_3_Nov93.pdf`

### Design Principles Applied

| Principle | Current State | Required State |
|-----------|---------------|----------------|
| **Consistency** | Two different output formats | Single unified panel format |
| **User Informed** | Subtle status text + border | Prominent mode indicator |
| **Modes Apparent** | Small status bar change | Clear visual mode signal |
| **Information Hierarchy** | Flat output | 4-zone structured layout |
| **Visual Feedback** | Minimal | Full panel with metadata |

## Additional Search

```bash
grep -ri "shell\|bash\|mode" .claude/
# See existing thoughts/ patterns on shell and mode handling
```

Potential areas to check:
- `.claude/metadata/` - dependency graphs, error patterns
- `.claude/patterns/` - canonical shell interaction patterns
- `.claude/debug_history/` - any shell-related bug fixes
