#!/usr/bin/env python3
"""Generate DEPENDENCY_MAP.md from actual codebase imports using grimp."""

from collections import defaultdict
from datetime import datetime
from pathlib import Path

import grimp

# Layer hierarchy (high to low)
LAYERS = ["ui", "core", "tools", "indexing", "lsp"]
UTILS_LEVEL = ["utils", "types", "configuration", "constants"]

# Valid import directions (from -> to)
# Higher layers can import from lower layers
# Any layer can import from utils-level
LAYER_ORDER = {layer: i for i, layer in enumerate(LAYERS)}


LAYER_COLORS = {
    "ui": "#ff6b6b",
    "core": "#4d96ff",
    "tools": "#6bcb77",
    "utils": "#ffd93d",
    "types": "#9d4edd",
    "configuration": "#adb5bd",
    "indexing": "#ff922b",
    "lsp": "#e599f7",
    "other": "#cccccc",
}


def generate_dot(g, output_path: Path) -> None:
    """Generate a GraphViz DOT file from the import graph."""
    lines = [
        "digraph tunacode_deps {",
        "  rankdir=LR;",
        "  node [shape=box, style=rounded, fontname=Arial];",
        "",
    ]

    # Group modules by layer
    modules_by_layer: dict[str, list[str]] = defaultdict(list)
    for module in g.modules:
        layer = get_layer(module) or "other"
        modules_by_layer[layer].append(module)

    # Create subgraphs for each layer
    for layer in list(LAYERS) + UTILS_LEVEL + ["other"]:
        if layer not in modules_by_layer:
            continue
        color = LAYER_COLORS.get(layer, "#cccccc")
        lines.append(f"  subgraph cluster_{layer} {{")
        lines.append(f'    label="{layer}";')
        lines.append("    style=filled;")
        lines.append(f'    color="{color}";')
        lines.append(f'    fontcolor="{color}";')

        for module in sorted(modules_by_layer[layer]):
            node_id = module.replace(".", "_")
            lines.append(f'    {node_id} [label="{module}"];')
        lines.append("  }")
        lines.append("")

    # Add edges
    lines.append("  // Edges")
    for module in g.modules:
        node_id = module.replace(".", "_")
        for imported in g.find_modules_directly_imported_by(module):
            if imported in g.modules:  # Only internal imports
                imported_id = imported.replace(".", "_")
                lines.append(f"  {node_id} -> {imported_id};")

    lines.append("}")

    output_path.write_text("\n".join(lines) + "\n")


def get_layer(module: str) -> str | None:
    """Extract layer from module path like tunacode.ui.app -> ui."""
    parts = module.split(".")
    if len(parts) < 2:
        return None
    layer = parts[1]
    if layer in LAYERS or layer in UTILS_LEVEL or layer in ["exceptions"]:
        return layer
    return None


def is_valid_import(from_layer: str, to_layer: str) -> bool:
    """Check if import direction is valid.

    Rules:
    - ui can only import from: core, utils-level
    - core can only import from: tools, indexing, utils-level
    - tools can only import from: indexing, lsp, utils-level
    - indexing/lsp can only import from: utils-level
    """
    # Utils-level can be imported by anyone
    if to_layer in UTILS_LEVEL or to_layer == "exceptions":
        return True

    # Within same layer is fine
    if from_layer == to_layer:
        return True

    # Define what each layer is ALLOWED to import
    allowed = {
        "ui": {"core"},  # UI only goes through core
        "core": {"tools", "indexing"},  # Core orchestrates tools
        "tools": {"indexing", "lsp"},  # Tools use infra
        "indexing": set(),  # Infra is leaf
        "lsp": set(),
    }

    if from_layer in allowed:
        return to_layer in allowed[from_layer]

    return True  # Unknown layers - don't flag


def main() -> None:
    g = grimp.build_graph("tunacode")

    # Count imports between layers
    import_counts: dict[tuple[str, str], int] = defaultdict(int)
    violations: list[tuple[str, str, str, str]] = []

    for module in g.modules:
        from_layer = get_layer(module)
        if not from_layer:
            continue

        for imported in g.find_modules_directly_imported_by(module):
            to_layer = get_layer(imported)
            if to_layer and to_layer != from_layer:
                import_counts[(from_layer, to_layer)] += 1

                if not is_valid_import(from_layer, to_layer):
                    violations.append((from_layer, to_layer, module, imported))

    # Generate markdown
    today = datetime.now().strftime("%Y-%m-%d")

    output = f"""# Dependency Map

> **Baseline frozen: {today}**
> Generated with [grimp](https://github.com/python-grimp/grimp)

## Layer Hierarchy (high to low)

```
ui          → outer layer (TUI)
core        → business logic
tools       → agent tools
indexing    → code indexing infrastructure
lsp         → language server protocol
─────────────────────────────────
utils       ┐
types       │ utils-level (importable from anywhere)
configuration│
constants   ┘
```

## Current State

![Dependency Graph](layers.png)

### Import Counts (grimp)

| From | To | Count | Status |
|------|----|-------|--------|
"""

    # Group by validity
    valid_imports = []
    invalid_imports = []

    for (from_l, to_l), count in sorted(import_counts.items()):
        if is_valid_import(from_l, to_l):
            valid_imports.append((from_l, to_l, count))
        else:
            invalid_imports.append((from_l, to_l, count))

    # Output valid imports first
    for from_l, to_l, count in valid_imports:
        output += f"| {from_l} → {to_l} | {count} | ✅ valid |\n"

    # Then invalid
    for from_l, to_l, count in invalid_imports:
        output += f"| {from_l} → {to_l} | {count} | ❌ violation |\n"

    # Violations section
    output += """
### Violations

"""

    if violations:
        output += f"**{len(violations)} violations found.** "
        output += "UI must not import directly from tools/lsp.\n\n"
        output += "| From Layer | To Layer | Importer | Imported |\n"
        output += "|------------|----------|----------|----------|\n"

        for from_l, to_l, importer, imported in sorted(violations):
            # Shorten module names for readability
            short_importer = importer.replace("tunacode.", "")
            short_imported = imported.replace("tunacode.", "")
            output += f"| {from_l} | {to_l} | `{short_importer}` | `{short_imported}` |\n"
    else:
        output += "**None.** All dependencies flow in valid directions.\n"

    output += """
## Rules

1. **Outward flow**: ui → core → tools → infrastructure
2. **Utils-level**: `utils/`, `types/`, `configuration/`, `constants.py` importable anywhere
3. **No backward imports**: tools cannot import from core, core cannot import from ui

## Verification

```bash
uv run python scripts/generate-dependency-map.py
```

## UI Layer Detail

Starting point for clean mapping. The UI layer imports:

"""

    # Get UI-specific imports
    ui_imports: dict[str, int] = defaultdict(int)
    for module in g.modules:
        if not module.startswith("tunacode.ui"):
            continue
        for imported in g.find_modules_directly_imported_by(module):
            to_layer = get_layer(imported)
            if to_layer and to_layer != "ui":
                ui_imports[to_layer] += 1

    for layer in [
        "core",
        "tools",
        "configuration",
        "constants",
        "utils",
        "types",
        "lsp",
        "exceptions",
    ]:
        if layer in ui_imports:
            status = "⚠️" if layer in ["tools", "lsp"] else ""
            output += f"- **{layer} ({ui_imports[layer]})**: {status}\n"

    if "tools" in ui_imports or "lsp" in ui_imports:
        output += "\n⚠️ = violation (UI should delegate to core, not import directly)\n"

    # Write markdown
    output_path = Path(__file__).parent.parent / "docs" / "architecture" / "DEPENDENCY_MAP.md"
    output_path.write_text(output)
    print(f"Written to {output_path}")

    # Generate fresh deps.dot
    dot_path = Path(__file__).parent.parent / "deps.dot"
    generate_dot(g, dot_path)
    print(f"Written to {dot_path}")

    # Summary
    print(f"\nViolations: {len(violations)}")
    for _from_l, _to_l, importer, imported in violations:
        print(f"  {importer} -> {imported}")


if __name__ == "__main__":
    main()
