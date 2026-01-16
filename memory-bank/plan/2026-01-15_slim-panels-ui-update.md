# Plan – Slim Panels UI Update (Option B)

**Date:** 2026-01-15
**Owner:** user + agent
**Phase:** Ready for Implementation
**Status:** APPROVED

## Goal

Transform tool panels from heavy boxed layouts to slim, line-based headers matching the dream mockup (`tunacode-cli-lsp.webp`). Target ~50% vertical space reduction with full-line background colors for semantic highlighting.

## Dream Mockup Reference

```
┌─ update_file ——————————————————————————————————── +3 -2 ─┐
│   ↳ tools/web_fetch.py                    (cyan, underlined) │
│                                                              │
│ 136 try:                                                     │
│ 137     head_response = await client.head(validated_url)     │
│ 138     content_length = head_response.headers.get("content- │
│ 139 - if content_length and int(content_length) > MAX+SIZE:  │ ██ RED BG
│ 139 + max_content_size = web_fetch_config.max_content_size_  │ ██ GREEN BG
│ 140 + if content_length and int(content_length) > max_conte  │ ██ GREEN BG
│ 141     raize ModelRetry(                                    │
└──────────────────────────────────────────────────────────────┘

┌─ LSP ————————————————————────── ⊘ 2 errors □ ⓘ 2 warnings ─┐
│                                                              │
│ L160: Undefined name `MAX_CONTENT_SIZE`                      │ ██ RED BG
│ L163: Undefined name `MAX_CONTENT_SIZE`                      │ ██ RED BG
│                                                              │
│ L6: Import block is un-sorted or un-formatted                │ ██ OLIVE BG
│ L137: Line too long (107 > 100)                              │ ██ OLIVE BG
└──────────────────────────────────────────────────────────────┘

⚙ Analyzing LSP Diagnostics...
▓▓▓▓ ≋🐟
```

## Design Principles (Updated from Mockup)

1. **NeXTSTEP slim borders** - Single-line box `┌─ ─┐ │ └─ ─┘`
2. **Header integrated into top border** - `┌─ tool_name ——————— stats ─┐`
3. **Stats in header** - Compact, right-aligned (`+3 -2` not `+3 -2 · 0.1s`)
4. **Link-style subtitle** - `↳ filepath` in cyan with underline
5. **FULL-LINE BACKGROUND COLORS** - Critical visual element:
   - `#4a2020` (dark red) for removed lines / errors
   - `#204a20` (dark green) for added lines / success
   - `#4a4a20` (dark olive) for warnings
6. **Minimal internal padding** - Content dense, no zone separators
7. **Activity line** - `⚙ {action}...` with fish animation `▓▓▓▓ ≋🐟`

## Visual Spec: Full-Line Backgrounds

This is THE key differentiator from the current design:

```python
# Rich styling for full-line backgrounds
DIFF_REMOVED_STYLE = Style(bgcolor="#4a2020")  # Dark red
DIFF_ADDED_STYLE = Style(bgcolor="#204a20")    # Dark green
LSP_ERROR_STYLE = Style(bgcolor="#4a2020")     # Dark red
LSP_WARNING_STYLE = Style(bgcolor="#4a4a20")   # Dark olive/yellow

# Apply to entire line, not just text
line = Text(content)
line.stylize(DIFF_REMOVED_STYLE, 0, len(content))
```

## Before / After

```
BEFORE (current - heavy):              AFTER (dream - slim NeXTSTEP):
┌─────── update_file ───────┐          ┌─ update_file ─────────── +3 -2 ─┐
│                           │          │   ↳ tools/web_fetch.py          │
│  tools/web_fetch.py       │          │                                 │
│  ─────────────────────    │          │ 137   head_response = await...  │
│                           │          │ 138   content_length = head...  │
│  137 head_response = ...  │          │ 139 - if content_length and...  │ ██RED
│  138 content_length = ... │          │ 139 + max_content_size = we...  │ ██GRN
│  139 - if content_len...  │          │ 140 + if content_length and...  │ ██GRN
│  139 + max_content_si...  │          └─────────────────────────────────┘
│  ─────────────────────    │
│  +3 -2  0.1s              │          Key differences:
│               20:46:02    │          - Header IN the border line
└───────────────────────────┘          - No internal separators
                                       - No timestamp clutter
12 lines → 9 lines                     - Full-line backgrounds
```

## Implementation Tasks

### Phase 1: Core Infrastructure

- [ ] **1.1** Create slim utilities in `renderers/tools/slim_base.py`
  ```python
  def slim_header(name: str, stats: str, width: int = 70) -> Text:
      """Build: — name ——————————————————————— stats —"""

  def slim_subtitle(context: str) -> Text:
      """Build: ↳ context (cyan, underlined)"""

  def slim_footer(shown: int, total: int) -> Text:
      """Build: [{shown}/{total}]"""
  ```

- [ ] **1.2** Define background color constants
  ```python
  # In constants.py or slim_base.py
  BG_REMOVED = "#4a2020"   # Dark red
  BG_ADDED = "#204a20"     # Dark green
  BG_ERROR = "#4a2020"     # Dark red (same as removed)
  BG_WARNING = "#4a4a20"   # Dark olive
  ```

- [ ] **1.3** Create full-line background utility
  ```python
  def styled_line(content: str, style: Style) -> Text:
      """Apply background color to entire line width."""
      text = Text(content)
      text.stylize(style, 0, len(content))
      return text
  ```

### Phase 2: Renderer Migration

- [ ] **2.1** `update_file.py` (Start here - matches mockup exactly)
  - Header: `— update_file ——————————————————————— +{added} -{removed} —`
  - Subtitle: `↳ {filepath}` (cyan, underlined)
  - Content: Line numbers + code
    - Removed lines: full red background `#4a2020`
    - Added lines: full green background `#204a20`
    - Context lines: normal background

- [ ] **2.2** `read_file.py`
  - Header: `— read_file ——————————————————————— {lines} lines —`
  - Subtitle: `↳ {filepath}` (cyan, underlined)
  - Content: Line-numbered code with syntax highlighting

- [ ] **2.3** `bash.py`
  - Header: `— bash ——————————————————————————————— {ok|exit N} —`
  - Subtitle: `↳ $ {command}`
  - Content: stdout normal, stderr with warning background

- [ ] **2.4** `grep.py`
  - Header: `— grep ———————————————— {matches} matches · {files} files —`
  - Subtitle: `↳ pattern: "{pattern}"`
  - Content: Match lines with file:line prefix

- [ ] **2.5** `glob.py`
  - Header: `— glob ——————————————————————————————— {count} files —`
  - Subtitle: `↳ {pattern}`
  - Content: File list

- [ ] **2.6** `list_dir.py`
  - Header: `— list_dir ————————————— {files} files · {dirs} dirs —`
  - Subtitle: `↳ {directory}`
  - Content: Tree view

- [ ] **2.7** `write_file.py`
  - Header: `— write_file —————————————————————————— {lines} lines —`
  - Subtitle: `↳ {filepath}` (cyan, underlined)
  - Content: Preview with success background tint

- [ ] **2.8** `web_fetch.py`
  - Header: `— web_fetch ——————————————————————————————— {status} —`
  - Subtitle: `↳ {url}`
  - Content: Response preview

### Phase 3: LSP Integration (Already exists, just restyle)

- [ ] **3.1** Update LSP display to match mockup
  - Header: `— LSP ——————————————— ⊘ {n} errors □ ⓘ {n} warnings —`
  - Errors: Full red background per line
  - Warnings: Full olive background per line
  - Format: `L{line}: {message}`

### Phase 4: Activity Line

- [ ] **4.1** Create activity indicator widget
  - Format: `⚙ {action}...`
  - Progress: `▓▓▓▓ ≋🐟` (fish animation!)
  - Replaces current `● ● ● ● ●` loading dots

### Phase 5: Cleanup

- [ ] **5.1** Remove Panel() usage from tool renderers
- [ ] **5.2** Update `panels.tcss` - remove box styles
- [ ] **5.3** Test with various terminal widths
- [ ] **5.4** Verify NeXTSTEP theme compatibility

## Color Palette

| Element | Hex | Usage |
|---------|-----|-------|
| Header line | `dim` | The `—————` dashes |
| Tool name | `bold` | `update_file` |
| Stats (success) | `green` | `+3` |
| Stats (removed) | `red` | `-2` |
| Subtitle | `cyan underline` | `↳ filepath` |
| BG Removed/Error | `#4a2020` | Full line background |
| BG Added/Success | `#204a20` | Full line background |
| BG Warning | `#4a4a20` | Full line background |
| Activity icon | `dim` | `⚙` |
| Fish | `cyan` | `🐟` |

## Header Format by Tool (Integrated into Border)

| Tool | Top Border Format |
|------|-------------------|
| update_file | `┌─ update_file ——————————————————— +{n} -{n} ─┐` |
| read_file | `┌─ read_file ————————————————————— {n} lines ─┐` |
| bash | `┌─ bash ———————————————————————————— {ok\|exit N} ─┐` |
| grep | `┌─ grep ——————————————— {n} matches · {n} files ─┐` |
| glob | `┌─ glob ——————————————————————————————— {n} files ─┐` |
| list_dir | `┌─ list_dir ——————————— {n} files · {n} dirs ─┐` |
| write_file | `┌─ write_file ————————————————————— {n} lines ─┐` |
| web_fetch | `┌─ web_fetch ——————————————————————— {status} ─┐` |
| LSP | `┌─ LSP ————————————— ⊘ {n} errors □ ⓘ {n} warnings ─┐` |

## Success Criteria

1. Matches dream mockup visual style exactly
2. NeXTSTEP slim borders with header integrated into top line
3. Full-line background colors for diffs/errors/warnings
4. Link-style subtitles (cyan + underline)
5. ~30% vertical space reduction (fewer internal separators)
6. Fish animation in activity line 🐟
7. Uses Rich Panel() with custom border title formatting

## Files to Modify

| File | Change |
|------|--------|
| `renderers/tools/slim_base.py` | NEW: Slim utilities |
| `renderers/tools/update_file.py` | Migrate first (matches mockup) |
| `renderers/tools/read_file.py` | Migrate to slim |
| `renderers/tools/bash.py` | Migrate to slim |
| `renderers/tools/grep.py` | Migrate to slim |
| `renderers/tools/glob.py` | Migrate to slim |
| `renderers/tools/list_dir.py` | Migrate to slim |
| `renderers/tools/write_file.py` | Migrate to slim |
| `renderers/tools/web_fetch.py` | Migrate to slim |
| `renderers/panels.py` | Update fallback |
| `styles/panels.tcss` | Remove box styles |
| `constants.py` | Add color constants |
| `app.py` | Update activity indicator |

## References

- **Dream mockup:** `tunacode-cli-lsp.webp`
- Research: `memory-bank/research/2026-01-15_tool-panel-redesign-options.md`
- Current base: `src/tunacode/ui/renderers/tools/base.py`
