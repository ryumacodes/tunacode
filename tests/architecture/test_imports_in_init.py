"""Ensure __all__ exports only items defined in __init__ modules."""

import ast
from pathlib import Path

from .test_import_order import SOURCE_ROOT as source_root


def _extract_names_from_node(node: ast.AST) -> list[str]:
    """Extract defined names from a single top-level AST node."""
    if isinstance(node, ast.Import | ast.ImportFrom):
        return [alias.asname or alias.name for alias in node.names]

    if isinstance(node, ast.Assign):
        return [t.id for t in node.targets if isinstance(t, ast.Name) and t.id != "__all__"]

    if isinstance(node, ast.AnnAssign):
        if isinstance(node.target, ast.Name) and node.target.id != "__all__":
            return [node.target.id]
        return []

    if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
        return [node.name]

    return []


def get_imports(init_file: Path) -> list[str]:
    """Get all objects except __all__."""
    with open(init_file) as f:
        root = ast.parse(f.read())

    objects: list[str] = []
    for node in ast.iter_child_nodes(root):
        objects.extend(_extract_names_from_node(node))
    return objects


def get_public_imports(init_file: Path) -> list[str]:
    """Get all public imports."""

    with open(init_file) as f:
        root = ast.parse(f.read())

    for node in ast.iter_child_nodes(root):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "__all__":
                    return [elt.value for elt in node.value.elts]
        elif (
            isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id == "__all__"
        ):
            return [elt.value for elt in node.value.elts]

    return []


def test_all_exported_imports() -> None:
    """Verify that all imports in __init__ files are equal to the public imports in __all__."""

    for init_file in source_root.rglob("__init__.py"):
        public_imports = get_public_imports(init_file)
        if not public_imports:
            continue
        imports = get_imports(init_file)
        assert set(public_imports).issubset(set(imports))
