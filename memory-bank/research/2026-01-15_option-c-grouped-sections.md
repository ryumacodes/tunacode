# Research – Option C: LSP-Style Grouped Sections

**Date:** 2026-01-15
**Owner:** user + agent
**Phase:** Research / Future Exploration
**Status:** DOCUMENTED (not approved for implementation)

## Concept

Group related outputs under collapsible section headers. Tools, LSP diagnostics, and agent responses each get their own visual section. Inspired by the LSP panel in the dream mockup.

## Visual Target

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                        OPTION C: GROUPED SECTIONS                            ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  ┌─ you 8:45 PM ─────────────────────────────────────────────────────────┐   ║
║  │ tell me about the prompting system                                    │   ║
║  └───────────────────────────────────────────────────────────────────────┘   ║
║                                                                              ║
║  ═══ Tools (4) ══════════════════════════════════════ 1.1s total ════════    ║
║                                                                              ║
║    ✓ glob           **/*prompt*              12 files        0.2s            ║
║    ✓ read_file      engine.py                120 lines       0.1s            ║
║    ✓ read_file      builder.py               85 lines        0.1s            ║
║    ✓ grep           "compose_prompt"         8 matches       0.3s            ║
║                                                                              ║
║    ▶ expand details                                                          ║
║                                                                              ║
║  ═══ LSP ════════════════════════════ ⊘ 2 errors  ⚠ 3 warnings ══════════    ║
║                                                                              ║
║    ⊘ src/auth.py                                                             ║
║      L160: Undefined name `MAX_CONTENT_SIZE`                                 ║
║      L163: Undefined name `MAX_CONTENT_SIZE`                                 ║
║                                                                              ║
║    ⚠ src/auth.py                                                             ║
║      L6: Import block is un-sorted or un-formatted                           ║
║      L137: Line too long (107 > 100)                                         ║
║                                                                              ║
║    ⚠ src/utils.py                                                            ║
║      L42: Missing type annotation                                            ║
║                                                                              ║
║  ═══ Agent ══════════════════════════════════════════════════════════════    ║
║                                                                              ║
║    The prompting system is a modular composition engine that builds          ║
║    system prompts from reusable sections. It's located in:                   ║
║                                                                              ║
║    - `src/tunacode/core/prompting/engine.py` - Main engine                   ║
║    - `src/tunacode/core/prompting/builder.py` - Prompt builder               ║
║    - `src/tunacode/core/prompting/sections/` - Reusable sections             ║
║                                                                              ║
║    The key function is `compose_prompt()` which...                           ║
║                                                                              ║
║    ──────────                                                                ║
║    openrouter:z-ai/glm-4.7 · 132 tokens · 4.0s                               ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

## Expanded Tools Section

When user clicks "▶ expand details":

```
═══ Tools (4) ══════════════════════════════════════ 1.1s total ════════

  — glob ————————————————————————————————————— 12 files · 0.2s —
    ↳ **/*prompt*

    src/tunacode/core/prompting/engine.py
    src/tunacode/core/prompting/builder.py
    src/tunacode/core/prompting/sections/
    [3/12]

  — read_file ——————————————————————————————— 120 lines · 0.1s —
    ↳ src/tunacode/core/prompting/engine.py

    1 │ """Core Prompting Engine"""
    2 │ from typing import Protocol
    [2/120]

  — read_file ———————————————————————————————— 85 lines · 0.1s —
    ↳ src/tunacode/core/prompting/builder.py

    1 │ """Prompt Builder"""
    2 │ from .engine import PromptSection
    [2/85]

  — grep ———————————————————————————— 8 matches · 3 files · 0.3s —
    ↳ pattern: "compose_prompt"

    engine.py:45  │ def compose_prompt(self, context: Context)
    engine.py:89  │     return self.compose_prompt(ctx)
    builder.py:12 │ from .engine import compose_prompt
    [3/8]

  ▼ collapse

═══ LSP ════════════════════════════ ⊘ 2 errors  ⚠ 3 warnings ══════════
```

## Section Types

### Tools Section
```
═══ Tools ({count}) ══════════════════════════════ {total_time} total ════════

  ✓ {tool}    {context}           {result}        {time}
  ✓ {tool}    {context}           {result}        {time}
  ⚙ {tool}    {context}           running...

  ▶ expand details
```

### LSP Section
```
═══ LSP ════════════════════════════ ⊘ {errors} errors  ⚠ {warnings} warnings ══════════

  ⊘ {filepath}
    L{line}: {message}
    L{line}: {message}

  ⚠ {filepath}
    L{line}: {message}
```

### Agent Section
```
═══ Agent ══════════════════════════════════════════════════════════════

  {streaming or final response content}

  ──────────
  {model} · {tokens} tokens · {time}s
```

## Comparison with Option B

| Aspect | Option B (Slim Panels) | Option C (Grouped Sections) |
|--------|------------------------|----------------------------|
| **Layout** | Sequential panels | Grouped by type |
| **Density** | Medium | High (collapsed) / Low (expanded) |
| **Scanning** | Scroll through all | Jump to section |
| **Tool detail** | Always visible | Collapsed by default |
| **LSP** | Not integrated | First-class section |
| **Complexity** | Low | Medium-High |
| **Interaction** | Passive | Expand/collapse |

## Architecture Changes Required

### New Components

1. **SectionContainer** - Collapsible section with header
2. **ToolsSummaryWidget** - Compact tool list with expand
3. **LSPDiagnosticsWidget** - Error/warning display
4. **AgentResponseSection** - Streaming response area

### Data Flow Changes

```
Current:
  Tool executes → ToolResultDisplay → RichLog.write(panel)

Option C:
  Tool executes → ToolResultDisplay → ToolsSection.add(result)
                                    → ToolsSection.update_summary()
                                    → (on expand) render full details
```

### State Management

Need to track:
- Which sections are expanded/collapsed
- Tool results buffer (for expand)
- LSP diagnostics accumulator
- Section ordering

## Implementation Complexity

| Component | Effort | Risk |
|-----------|--------|------|
| Section headers | Low | Low |
| Tool summary row | Medium | Low |
| Expand/collapse | Medium | Medium |
| LSP integration | High | Medium |
| State management | Medium | Medium |
| Keyboard navigation | Medium | Low |

**Total estimate:** Medium-High complexity

## When to Consider Option C

- After Option B is stable
- If users want LSP diagnostics integration
- If tool density becomes overwhelming even with slim panels
- If users request collapsible sections

## Hybrid Approach

Could combine B + C:
- Use slim panels (Option B) as the expanded format
- Add section grouping (Option C) around them
- Best of both worlds

```
═══ Tools (4) ══════════════════════════════════════ 1.1s total ════════

  — glob ————————————————————————————————————— 12 files · 0.2s —
    ↳ **/*prompt*
    src/tunacode/core/prompting/engine.py
    [1/12]

  — read_file ——————————————————————————————— 120 lines · 0.1s —
    ↳ engine.py
    1 │ """Core Prompting Engine"""
    [1/120]

═══ LSP ════════════════════════════ ⊘ 2 errors  ⚠ 3 warnings ══════════
  ...
```

## Visual Elements

### Section Header
```
═══ {Name} ═══════════════════════════════════ {stats} ════════
    ╔═╗                                        right-aligned
    double line for prominence
```

### Tool Summary Row (collapsed)
```
  ✓ glob           **/*prompt*              12 files        0.2s
  │   │                │                        │             │
  │   │                │                        │             └─ duration
  │   │                │                        └─ result summary
  │   │                └─ context (pattern/file/command)
  │   └─ tool name (fixed width)
  └─ status icon (✓ ⚙ ✗)
```

### LSP Diagnostic Row
```
  ⊘ src/auth.py
    L160: Undefined name `MAX_CONTENT_SIZE`
    │  │
    │  └─ message
    └─ line number
```

## References

- Dream mockup: `tunacode-cli-lsp.webp` (LSP section inspiration)
- Option B plan: `memory-bank/plan/2026-01-15_slim-panels-ui-update.md`
- Current renderers: `src/tunacode/ui/renderers/tools/`
