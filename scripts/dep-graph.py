#!/usr/bin/env python
"""Generate dependency graph visualization using grimp.

Usage:
  python scripts/dep-graph.py [--layers] > deps.dot
  dot -Tpng deps.dot -o deps.png

Flags:
  --layers    Show only layer-level dependencies (simpler graph)
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from grimp import build_graph

# Layer colors for graphviz
LAYER_COLORS = {
    "ui": "#ff6b6b",  # red
    "core": "#4d96ff",  # blue
    "tools": "#6bcb77",  # green
    "utils": "#ffd93d",  # yellow
    "types": "#9d4edd",  # purple
    "configuration": "#adb5bd",  # gray
    "indexing": "#ff922b",  # orange
    "lsp": "#e599f7",  # pink
}


def get_layer(module: str) -> str:
    """Get the layer name for a module."""
    for layer in LAYER_COLORS:
        if module.startswith(f"tunacode.{layer}"):
            return layer
    return "other"


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--layers", action="store_true", help="Show only layer-level deps")
    args = parser.parse_args()

    # Build the dependency graph
    graph = build_graph("tunacode")

    if args.layers:
        generate_layer_graph(graph)
    else:
        generate_full_graph(graph)


def generate_layer_graph(graph):
    """Generate simplified layer-to-layer graph."""
    # Build layer adjacency
    layer_edges: dict[tuple[str, str], int] = {}

    for module in graph.modules:
        src_layer = get_layer(module)
        if src_layer == "other":
            continue
        for imported in graph.find_modules_directly_imported_by(module):
            if not imported.startswith("tunacode"):
                continue
            dst_layer = get_layer(imported)
            if dst_layer == "other":
                continue
            if src_layer == dst_layer:
                continue
            key = (src_layer, dst_layer)
            layer_edges[key] = layer_edges.get(key, 0) + 1

    # Output Graphviz DOT format
    print("digraph tunacode_layers {")
    print("  rankdir=TB;")
    print('  node [shape=box, style=filled, fontname="Arial"];')
    print()

    # Add nodes
    for layer, color in LAYER_COLORS.items():
        print(f'  {layer} [label="{layer}", fillcolor="{color}"];')
    print()

    # Add edges with counts
    for (src, dst), count in sorted(layer_edges.items()):
        print(f'  {src} -> {dst} [label="{count}", penwidth={min(count / 5 + 1, 5)}];')

    print("}")


def generate_full_graph(graph):
    """Generate full module-level graph (can be very large)."""
    print("digraph tunacode_deps {")
    print("  rankdir=LR;")
    print("  node [shape=box, style=rounded, fontname=Arial];")
    print()

    # Group modules by layer
    layers: dict[str, list[str]] = {layer: [] for layer in LAYER_COLORS}
    layers["other"] = []

    for module in graph.modules:
        layer = get_layer(module)
        layers[layer].append(module)

    # Create subgraphs for each layer
    for layer, modules in layers.items():
        if not modules:
            continue
        color = LAYER_COLORS.get(layer, "#cccccc")
        print(f"  subgraph cluster_{layer} {{")
        print(f'    label="{layer}";')
        print("    style=filled;")
        print(f'    color="{color}";')
        print(f'    fontcolor="{color}";')
        for module in modules:
            safe_name = module.replace(".", "_")
            print(f'    {safe_name} [label="{module}"];')
        print("  }")
        print()

    # Add edges (imports)
    print("  // Edges")
    for module in graph.modules:
        for imported in graph.find_modules_directly_imported_by(module):
            # Only show tunacode internal imports
            if not imported.startswith("tunacode"):
                continue
            src = module.replace(".", "_")
            dst = imported.replace(".", "_")
            print(f"  {src} -> {dst};")

    print("}")


if __name__ == "__main__":
    main()
