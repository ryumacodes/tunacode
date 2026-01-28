#!/usr/bin/env python3
"""Generate a layer-level dependency report from the current codebase."""

from __future__ import annotations

from collections import defaultdict, deque
from datetime import datetime
from pathlib import Path

import grimp

PACKAGE = "tunacode"
OUTPUT_DIR = Path(__file__).parent.parent / "docs" / "architecture" / "dependencies"
REPORT_PATH = OUTPUT_DIR / "DEPENDENCY_LAYERS.md"
LAYERS_DOT_PATH = OUTPUT_DIR / "DEPENDENCY_LAYERS.dot"
LAYER_GRAPH_PATH = OUTPUT_DIR / "DEPENDENCY_LAYERS.png"


def get_layer(module: str) -> str | None:
    parts = module.split(".")
    if len(parts) < 2 or parts[0] != PACKAGE:
        return None
    return parts[1]


def topo_sort(layers: set[str], edges: dict[tuple[str, str], int]) -> list[str]:
    outgoing: dict[str, set[str]] = defaultdict(set)
    indegree: dict[str, int] = {layer: 0 for layer in layers}

    for (src, dst), count in edges.items():
        if count == 0 or src == dst:
            continue
        if dst not in outgoing[src]:
            outgoing[src].add(dst)
            indegree[dst] += 1

    queue = deque(sorted([layer for layer, deg in indegree.items() if deg == 0]))
    ordered: list[str] = []

    while queue:
        layer = queue.popleft()
        ordered.append(layer)
        for dst in sorted(outgoing.get(layer, set())):
            indegree[dst] -= 1
            if indegree[dst] == 0:
                queue.append(dst)

    if len(ordered) != len(layers):
        return sorted(layers)

    return ordered


def write_layers_dot(layers: list[str], edges: dict[tuple[str, str], int]) -> None:
    lines = [
        "digraph tunacode_layers {",
        "  rankdir=TB;",
        "  node [shape=box, style=filled, fontname=Arial];",
        "",
    ]

    for layer in layers:
        lines.append(f'  {layer} [label="{layer}"];')
    lines.append("")

    for (src, dst), count in sorted(edges.items()):
        if src == dst:
            continue
        lines.append(f'  {src} -> {dst} [label="{count}"];')

    lines.append("}")
    LAYERS_DOT_PATH.write_text("\n".join(lines) + "\n")

    # Also generate PNG if graphviz is available
    try:
        import subprocess

        subprocess.run(
            ["dot", "-Tpng", str(LAYERS_DOT_PATH), "-o", str(LAYER_GRAPH_PATH)],
            check=True,
            capture_output=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        # graphviz not installed, skip PNG generation
        pass


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    graph = grimp.build_graph(PACKAGE)
    modules = set(graph.modules)

    layers = {layer for module in modules if (layer := get_layer(module))}
    edges: dict[tuple[str, str], int] = defaultdict(int)

    for module in modules:
        src_layer = get_layer(module)
        if not src_layer:
            continue
        for imported in graph.find_modules_directly_imported_by(module):
            dst_layer = get_layer(imported)
            if not dst_layer or dst_layer == src_layer:
                continue
            edges[(src_layer, dst_layer)] += 1

    ordered_layers = topo_sort(layers, edges)
    has_cycle = set(ordered_layers) != layers or any(src == dst for (src, dst) in edges)

    today = datetime.now().strftime("%Y-%m-%d")
    report_lines = [
        "# Dependency Layers",
        "",
        f"Generated: {today}",
        "",
        "## Layer Order (topological)",
        "",
    ]

    if has_cycle:
        report_lines.append(
            "Note: cycles detected or ambiguous ordering; listing layers alphabetically."
        )
        report_lines.append("")

    report_lines.append("```")
    report_lines.extend(ordered_layers)
    report_lines.append("```")
    report_lines.append("")

    report_lines.append("## Layer-to-Layer Imports")
    report_lines.append("")
    report_lines.append("| From | To | Count |")
    report_lines.append("|------|----|-------|")

    for (src, dst), count in sorted(edges.items()):
        report_lines.append(f"| {src} | {dst} | {count} |")

    if not edges:
        report_lines.append("| (none) | (none) | 0 |")

    REPORT_PATH.write_text("\n".join(report_lines) + "\n")
    write_layers_dot(ordered_layers, edges)


if __name__ == "__main__":
    main()
