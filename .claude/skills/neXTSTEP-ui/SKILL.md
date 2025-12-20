# NeXTSTEP-UI Skill

This skill provides design guidelines for creating and modifying tool panel renderers in Tunacode. All UI changes should follow these principles to maintain visual uniformity.

## Core Design Philosophy

From CLAUDE.md:
- **Uniformity**: Consistent, predictable experience across all interactions
- **User Informed**: Keep user constantly aware of agent state, actions, and reasoning
- **Aesthetic**: Professional, clean, retro-modern look echoing NeXTSTEP clarity

## 4-Zone Panel Layout

Every tool panel MUST follow this standardized architecture:

```
┌──────────────────────────────────────────────────────────────────┐
│  ZONE 1 (HEADER)                                                 │
│  tool_name [status]                                              │ ← tool name + status badge
├──────────────────────────────────────────────────────────────────┤
│  ZONE 2 (CONTEXT)                                                │
│  key1: value1    key2: value2    key3: value3                    │ ← input parameters
├──────────────────────────────────────────────────────────────────┤
│  ZONE 3 (PRIMARY VIEWPORT)                                       │
│  [Primary Content - The "Hero"]                                  │
│  • Text output, diffs, tables, results                           │
│  • Bounded to TOOL_VIEWPORT_LINES (10 lines)                     │
├──────────────────────────────────────────────────────────────────┤
│  ZONE 4 (STATUS)                                                 │
│  123ms • [12/50 lines] • (truncated)                             │ ← metrics & metadata
└──────────────────────────────────────────────────────────────────┘
  09:41:32 AM                                                       ← subtitle (timestamp)
```

### Zone Requirements

**Zone 1 (Header)**: Primary identifier + summary
- Tool-specific identifier (filename, command, pattern)
- Summary counts or status in `dim` style
- Example: `"*.py"   45 files`

**Zone 2 (Context)**: Key parameters
- Display relevant execution parameters
- Format: `key: value` pairs separated by double spaces
- Use `dim` for labels, `dim bold` for values
- Example: `recursive: on  hidden: off  sort: modified`

**Zone 3 (Viewport)**: Primary content
- Main output (file content, command output, search results)
- Fixed height: `TOOL_VIEWPORT_LINES = 10` lines
- Pad with empty lines if content is shorter
- Truncate if content is longer, show truncation in Zone 4

**Zone 4 (Status)**: Metrics and metadata
- Truncation info: `[shown/total]`
- Duration: `123ms`
- Additional metrics as appropriate
- All in `dim` style

## Viewport Sizing Constants

From `src/tunacode/constants.py`:

```python
LINES_RESERVED_FOR_HEADER_FOOTER = 4   # Header, params, separators, status
TOOL_VIEWPORT_LINES = 10               # Fixed viewport height
MIN_VIEWPORT_LINES = TOOL_VIEWPORT_LINES  # Min equals max for consistency
TOOL_PANEL_WIDTH = 100                 # Fixed width for uniform panels
MAX_PANEL_LINE_WIDTH = 200             # Individual line truncation
```

## UI Color Palette

From `UI_COLORS` in `constants.py`:

| Color | Hex | Usage |
|-------|-----|-------|
| background | `#1a1a1a` | Near black |
| surface | `#252525` | Panel background |
| border | `#ff6b9d` | Magenta borders |
| text | `#e0e0e0` | Primary text (light gray) |
| muted | `#808080` | Secondary text, parameters |
| primary | `#00d7d7` | Cyan (model, tokens) |
| accent | `#ff6b9d` | Magenta (brand, research) |
| success | `#4ec9b0` | Green (completion) |
| warning | `#c3e88d` | Yellow/lime |
| error | `#f44747` | Red |

### Border Color Guidelines
- **success**: Completed operations, successful results
- **error**: Failed operations, error states
- **accent**: Research/search operations (research_codebase)
- **warning**: Partial success, non-zero exit codes (bash)

## Standard Renderer Pattern

All tool renderers follow this structure:

### 1. Dataclass for Parsed Data
```python
@dataclass
class ToolNameData:
    """Parsed tool result for structured display."""
    field1: str
    field2: int
    # ... extracted fields
```

### 2. Parse Function
```python
def parse_result(args: dict[str, Any] | None, result: str) -> ToolNameData | None:
    """Extract structured data from tool output."""
    # Parse result string into dataclass
    # Return None if parsing fails
```

### 3. Truncation Helper
```python
def _truncate_line(line: str) -> str:
    """Truncate a single line if too wide."""
    if len(line) > MAX_PANEL_LINE_WIDTH:
        return line[: MAX_PANEL_LINE_WIDTH - 3] + "..."
    return line
```

### 4. Main Render Function
```python
def render_tool_name(
    args: dict[str, Any] | None,
    result: str,
    duration_ms: float | None = None,
) -> RenderableType | None:
    """Render tool with NeXTSTEP zoned layout."""
    data = parse_result(args, result)
    if not data:
        return None

    # Zone 1: Header
    header = Text()
    header.append(data.identifier, style="bold")
    header.append(f"   {data.count} items", style="dim")

    # Zone 2: Parameters
    params = Text()
    params.append("key:", style="dim")
    params.append(f" {value}", style="dim bold")

    separator = Text(BOX_HORIZONTAL * SEPARATOR_WIDTH, style="dim")

    # Zone 3: Viewport with padding
    viewport_lines: list[str] = []
    # ... populate viewport_lines
    while len(viewport_lines) < MIN_VIEWPORT_LINES:
        viewport_lines.append("")
    viewport = Text("\n".join(viewport_lines))

    # Zone 4: Status
    status_items: list[str] = []
    if shown < total:
        status_items.append(f"[{shown}/{total}]")
    if duration_ms:
        status_items.append(f"{duration_ms:.0f}ms")
    status = Text("  ".join(status_items), style="dim")

    # Compose all zones
    content = Group(
        header, Text("\n"),
        params, Text("\n"),
        separator, Text("\n"),
        viewport, Text("\n"),
        separator, Text("\n"),
        status,
    )

    timestamp = datetime.now().strftime("%H:%M:%S")

    return Panel(
        content,
        title=f"[{UI_COLORS['success']}]tool_name[/] [done]",
        subtitle=f"[{UI_COLORS['muted']}]{timestamp}[/]",
        border_style=Style(color=UI_COLORS["success"]),
        padding=(0, 1),
        expand=False,
        width=TOOL_PANEL_WIDTH,
    )
```

## Module Constants

Every renderer should define:
```python
BOX_HORIZONTAL = "\u2500"  # Unicode box-drawing character
SEPARATOR_WIDTH = 52       # Standard separator line width
```

## Checklist for New Renderers

- [ ] Create dataclass for parsed data
- [ ] Implement parse_result() function
- [ ] Implement _truncate_line() helper
- [ ] Implement render_tool_name() with 4 zones
- [ ] Use TOOL_VIEWPORT_LINES for viewport height
- [ ] Pad viewport to MIN_VIEWPORT_LINES
- [ ] Use TOOL_PANEL_WIDTH for panel width
- [ ] Add renderer to `tool_panel_smart()` router in `panels.py`
- [ ] Export from `tools/__init__.py`
- [ ] Run `ruff check --fix .`

## Files Reference

| File | Purpose |
|------|---------|
| `src/tunacode/constants.py` | All UI constants |
| `src/tunacode/ui/renderers/panels.py` | Panel rendering base, tool_panel_smart() |
| `src/tunacode/ui/renderers/tools/*.py` | Tool-specific renderers |
| `src/tunacode/ui/styles.py` | Style definitions |
