#!/usr/bin/env python3
"""
Quality Gates Runner - Minimal output for code agents.

Exits 0 if all gates pass, non-zero with failure details if any fail.
"""

import subprocess
import sys

LAYERS = [
    "ui",
    "core",
    "tools",
    "utils",
    "configuration",
    "constants",
    "exceptions",
    "infrastructure",
    "types",
]


def run_cmd(cmd: list[str]) -> tuple[bool, str]:
    result = subprocess.run(cmd, capture_output=True, text=True)
    passed = result.returncode == 0
    output = (result.stdout + result.stderr).strip()
    return passed, output


def gate_0_shims() -> tuple[bool, str]:
    passed, output = run_cmd(["grep", "-r", "__all__", "src/tunacode", "--include=*.py"])
    if passed and output:
        return False, f"Found __all__ exports:\n{output[:500]}"
    return True, ""


def gate_1_coupling() -> tuple[bool, str]:
    return run_cmd(["uv", "run", "ruff", "check", "src/", "--select=C90,F"])


def gate_2_deps() -> tuple[bool, str]:
    try:
        from grimp import build_graph

        g = build_graph("tunacode")
        illegal = g.find_illegal_dependencies_for_layers(layers=LAYERS, containers={"tunacode"})
        if illegal:
            lines = []
            for d in list(illegal)[:10]:
                lines.append(f"  {d.importer} -> {d.imported}")
            return False, "Illegal layer dependencies:\n" + "\n".join(lines)
        return True, ""
    except Exception as e:
        return False, str(e)


def gate_3_types() -> tuple[bool, str]:
    return run_cmd(["uv", "run", "mypy", "src/", "--no-error-summary", "--no-pretty"])


def gate_6_security() -> tuple[bool, str]:
    return run_cmd(["uv", "run", "bandit", "-r", "src/", "-q", "-c", "pyproject.toml"])


GATES = [
    ("Gate 0: Shims", gate_0_shims),
    ("Gate 1: Coupling", gate_1_coupling),
    ("Gate 2: Deps", gate_2_deps),
    ("Gate 3: Types", gate_3_types),
    ("Gate 6: Security", gate_6_security),
]


def main():
    failures = []

    for name, gate_fn in GATES:
        passed, output = gate_fn()
        if not passed:
            failures.append(f"{name} FAILED\n{output}")

    if failures:
        print("QUALITY GATES FAILED\n")
        print("\n---\n".join(failures))
        sys.exit(1)
    else:
        print("ALL GATES PASSED")
        sys.exit(0)


if __name__ == "__main__":
    main()
