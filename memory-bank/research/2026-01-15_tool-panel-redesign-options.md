# Research – Tool Panel Redesign Options

**Date:** 2026-01-15
**Owner:** agent + user
**Phase:** Research / Design Exploration

## Problem Statement

Current tool panels are:
- Too tall (4-zone layout with separators)
- Too much whitespace between zones
- All look the same (cyan borders everywhere)
- Hard to scan when scrolling rapidly

## Reference: Dream UI Mockup

From user's mockup (`tunacode-cli-lsp.webp`):

```
— update_file ————————————————————————— +3 -2 —
  ↳ tools/web_fetch.py

136 try:
137     head_response = await client.head(validated_url)
139 - if content_length and int(content_length) > MAX+SIZE:
139 + max_content_size = web_fetch_config.max_content_size_..

— LSP ——————————————————— ⊘ 2 errors □ ⓘ 2 warnings —
L160: Undefined name `MAX_CONTENT_SIZE`
L163: Undefined name `MAX_CONTENT_SIZE`

⚙ Analyzing LSP Diagnostics...
▓▓▓▓ ≋🐟
```

### What makes the mockup work:

| Element | Current | Dream |
|---------|---------|-------|
| Border style | Solid box all around | Horizontal line separators only |
| Header | Tool name centered, timestamp subtitle | Tool name left, stats right, one line |
| Zones | 4 zones with separators | 2 zones max (header + content) |
| Whitespace | Padding inside box | Minimal, content-dense |
| Status | Bottom zone with metrics | Inline in header (`+3 -2`) |
| Activity | Loading dots + streaming panel | One-liner with icon + animation |

---

## Option A: Compact Tool Lines (Minimal)

**Concept:** Tools become single-line status updates, not panels.

```
✓ glob("**/*.py") → 47 files                           0.2s
✓ read_file(src/main.py) → 120 lines                   0.1s
✓ grep("TODO") → 3 matches in 2 files                  0.3s
⚙ update_file(src/auth.py)...
```

**Pros:**
- Maximum density
- Easy to scan
- Tools don't interrupt flow

**Cons:**
- No content preview
- Lose the 4-zone detail
- Hard to debug tool failures

**Implementation:**
- New renderer mode: `compact=True`
- Skip viewport zone entirely
- One-line summary only

---

## Option B: Slim Panels (Balanced)

**Concept:** Keep panels but remove the ceremony. Two zones max.

```
— read_file ——————————————————————— 120 lines · 0.1s —
  ↳ src/tunacode/core/prompting/engine.py

  1 """Core Prompting Engine"""
  2 from typing import Protocol
  3 ...
  8 seams: [M, D]

[8/120 displayed]
```

**Pros:**
- Still shows content preview
- Much more compact than current
- Header carries the key info

**Cons:**
- Still takes vertical space
- Need to redesign all renderers

**Implementation:**
- Replace Panel() with custom layout
- Merge header + status into one line
- Remove internal separators
- Reduce padding to 0

---

## Option C: LSP-Style Grouped Sections

**Concept:** Group related outputs under section headers.

```
— Tools ———————————————————————————————————————————————
  ✓ glob       47 files     0.2s
  ✓ read_file  120 lines    0.1s
  ✓ grep       3 matches    0.3s

— LSP ——————————————————— ⊘ 2 errors □ ⓘ 2 warnings —
  L160: Undefined name `MAX_CONTENT_SIZE`
  L163: Undefined name `MAX_CONTENT_SIZE`

— Agent ———————————————————————————————————————————————
  I found the prompting system in...
```

**Pros:**
- Clear visual hierarchy
- Grouped by type
- Matches the mockup's LSP section

**Cons:**
- Major architectural change
- Tools no longer stream individually
- Need batching/grouping logic

**Implementation:**
- New "section" concept
- Accumulate tools, render as group
- LSP diagnostics get their own section

---

## Option D: Streaming Panel Shows Everything

**Concept:** The streaming panel becomes the main display. Tools are inline.

```
┌─────────────────────────────────────────────────────┐
│ I'll search for the prompting system...             │
│                                                     │
│ ✓ glob("**/*prompt*") → 12 files                    │
│ ✓ read_file(engine.py) → 120 lines                  │
│                                                     │
│ The prompting system is a modular composition       │
│ engine that...                                      │
│                                                     │
│ ⚙ Analyzing LSP Diagnostics...                      │
│ ▓▓▓▓ ≋🐟                                            │
└─────────────────────────────────────────────────────┘
```

**Pros:**
- Single visual focus
- Tools integrated with agent thought
- Matches how Claude Code works

**Cons:**
- Lose separate tool history
- Can't scroll back to see tool details
- Major UX change

**Implementation:**
- Merge RichLog + streaming panel
- Tools render inline with agent text
- Remove separate tool panels entirely

---

## Option E: Hybrid - Compact Tools + Detail Drawer

**Concept:** Tools show compact by default, click/key to expand.

```
— Tools (3) ——————————————————————— ▶ expand ————————
  ✓ glob  ✓ read_file  ✓ grep

— Agent ———————————————————————————————————————————————
  The prompting system is...
```

Expanded:
```
— Tools (3) ——————————————————————— ▼ collapse ———————
  ✓ glob("**/*prompt*")
    → 12 files: engine.py, builder.py, sections/...

  ✓ read_file(src/tunacode/core/prompting/engine.py)
    → 120 lines, Python
    1 """Core Prompting Engine"""
    2 from typing import Protocol
    ...
```

**Pros:**
- Best of both worlds
- User controls detail level
- Compact by default

**Cons:**
- Complex interaction model
- Need keyboard/mouse handling
- State management

---

## Recommendation

**Start with Option B (Slim Panels)** because:
1. Lowest risk - same data flow, just different rendering
2. Matches the mockup's aesthetic
3. Can iterate toward other options later

### Immediate changes:
1. Replace `Panel()` with line-based headers: `— tool_name ——— stats —`
2. Remove internal zone separators
3. Merge status into header line
4. Reduce padding to 0
5. Add activity line with fish animation

### Future enhancements:
- Add LSP section (Option C element)
- Add expand/collapse (Option E element)
- Consider inline tools in streaming (Option D element)

---

## Visual Comparison

### Current (Too Much)
```
┌──────────────── read_file ────────────────┐
│                                           │
│  src/tunacode/core/prompting/engine.py    │
│  ─────────────────────────────────────    │
│                                           │
│  1 """Core Prompting Engine"""            │
│  2 from typing import Protocol            │
│  3 ...                                    │
│  ─────────────────────────────────────    │
│  [8/120 displayed]  120 lines  0.1s       │
│                                           │
│                              20:46:02     │
└───────────────────────────────────────────┘
```

### Target (Just Right)
```
— read_file ——————————————————— 120 lines · 0.1s —
  ↳ src/tunacode/core/prompting/engine.py

  1 """Core Prompting Engine"""
  2 from typing import Protocol
  3 ...

[8/120]
```

**Vertical savings:** ~40% reduction

---

## Next Steps

1. [ ] Invoke neXTSTEP-ui skill for design validation
2. [ ] Prototype Option B in a single renderer (read_file)
3. [ ] Get user feedback on prototype
4. [ ] Roll out to all renderers if approved
5. [ ] Add LSP diagnostics section
6. [ ] Add activity line with fish animation

---

## References

- User mockup: `tunacode-cli-lsp.webp`
- Current renderers: `src/tunacode/ui/renderers/tools/`
- Base renderer: `src/tunacode/ui/renderers/tools/base.py`
- Panel styles: `src/tunacode/ui/styles/panels.tcss`
