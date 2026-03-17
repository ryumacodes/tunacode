#!/usr/bin/env python3
"""Detect defensive typing/serialization patterns in internal typed paths.

This script intentionally targets a narrow set of anti-patterns:
- Protocol stubs for model_dump that raise NotImplementedError.
- cast(Any, value).model_dump(...) calls.
- Re-validation via isinstance(var, dict) where var came from model_dump(...).
- Legacy error strings asserting model_dump "must return dict".
"""

from __future__ import annotations

import ast
import sys
from dataclasses import dataclass
from pathlib import Path

PROJECT_SRC_ROOT = Path("src/tunacode")

VIOLATION_PROTOCOL_MODEL_DUMP_STUB = "DS001"
VIOLATION_ANY_CAST_MODEL_DUMP = "DS002"
VIOLATION_MODEL_DUMP_DICT_REVALIDATION = "DS003"
VIOLATION_MODEL_DUMP_MUST_RETURN_DICT_STRING = "DS004"


@dataclass(frozen=True)
class Violation:
    code: str
    path: Path
    line: int
    message: str

    def format(self) -> str:
        return f"{self.path}:{self.line}: {self.code} {self.message}"


def _is_protocol_base(base: ast.expr) -> bool:
    if isinstance(base, ast.Name):
        return base.id == "Protocol"
    if isinstance(base, ast.Attribute):
        return base.attr == "Protocol"
    if isinstance(base, ast.Subscript):
        return _is_protocol_base(base.value)
    return False


def _is_not_implemented_error(expr: ast.expr | None) -> bool:
    if expr is None:
        return False
    if isinstance(expr, ast.Name):
        return expr.id == "NotImplementedError"
    if isinstance(expr, ast.Call):
        return isinstance(expr.func, ast.Name) and expr.func.id == "NotImplementedError"
    return False


def _has_model_dump_stub(function_node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    if function_node.name != "model_dump":
        return False

    for node in ast.walk(function_node):
        if isinstance(node, ast.Raise) and _is_not_implemented_error(node.exc):
            return True
    return False


def _is_model_dump_call(expr: ast.expr) -> bool:
    return (
        isinstance(expr, ast.Call)
        and isinstance(expr.func, ast.Attribute)
        and expr.func.attr == "model_dump"
    )


def _is_any_annotation(expr: ast.expr) -> bool:
    if isinstance(expr, ast.Name):
        return expr.id == "Any"
    if isinstance(expr, ast.Attribute):
        return expr.attr == "Any"
    return False


def _is_cast_any_call(expr: ast.expr) -> bool:
    if not isinstance(expr, ast.Call):
        return False
    if not isinstance(expr.func, ast.Name) or expr.func.id != "cast":
        return False
    if not expr.args:
        return False
    return _is_any_annotation(expr.args[0])


def _extract_name_targets(target: ast.expr) -> set[str]:
    if isinstance(target, ast.Name):
        return {target.id}
    if isinstance(target, ast.Tuple | ast.List):
        names: set[str] = set()
        for elt in target.elts:
            names.update(_extract_name_targets(elt))
        return names
    return set()


def _collect_model_dump_assigned_names(
    statements: list[ast.stmt],
) -> set[str]:
    names: set[str] = set()
    for statement in statements:
        if isinstance(statement, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
            continue

        for node in ast.walk(statement):
            if isinstance(node, ast.Assign) and _is_model_dump_call(node.value):
                for target in node.targets:
                    names.update(_extract_name_targets(target))
            if (
                isinstance(node, ast.AnnAssign)
                and node.value is not None
                and _is_model_dump_call(node.value)
            ):
                names.update(_extract_name_targets(node.target))
    return names


def _is_isinstance_dict_check(expr: ast.expr) -> str | None:
    if not isinstance(expr, ast.Call):
        return None
    if not isinstance(expr.func, ast.Name) or expr.func.id != "isinstance":
        return None
    if len(expr.args) != 2:
        return None

    candidate, expected = expr.args
    if not isinstance(candidate, ast.Name):
        return None

    if isinstance(expected, ast.Name) and expected.id == "dict":
        return candidate.id

    return None


def _contains_model_dump_must_return_dict_string(node: ast.AST) -> bool:
    if not isinstance(node, ast.Constant) or not isinstance(node.value, str):
        return False

    value = node.value
    return "model_dump(" in value and "must return dict" in value


class DefensiveSlopVisitor(ast.NodeVisitor):
    def __init__(self, path: Path) -> None:
        self.path = path
        self.violations: list[Violation] = []
        self._model_dump_name_stack: list[set[str]] = []

    def _add(self, code: str, node: ast.AST, message: str) -> None:
        self.violations.append(
            Violation(code=code, path=self.path, line=getattr(node, "lineno", 1), message=message)
        )

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        if any(_is_protocol_base(base) for base in node.bases):
            for item in node.body:
                if isinstance(
                    item, ast.FunctionDef | ast.AsyncFunctionDef
                ) and _has_model_dump_stub(item):
                    self._add(
                        VIOLATION_PROTOCOL_MODEL_DUMP_STUB,
                        item,
                        "Protocol model_dump stub with NotImplementedError is banned",
                    )
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        names = _collect_model_dump_assigned_names(node.body)
        self._model_dump_name_stack.append(names)
        self.generic_visit(node)
        self._model_dump_name_stack.pop()

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        names = _collect_model_dump_assigned_names(node.body)
        self._model_dump_name_stack.append(names)
        self.generic_visit(node)
        self._model_dump_name_stack.pop()

    def visit_Call(self, node: ast.Call) -> None:
        if (
            isinstance(node.func, ast.Attribute)
            and node.func.attr == "model_dump"
            and _is_cast_any_call(node.func.value)
        ):
            self._add(
                VIOLATION_ANY_CAST_MODEL_DUMP,
                node,
                "cast(Any, ...).model_dump(...) is banned in internal typed paths",
            )

        if self._model_dump_name_stack:
            checked_name = _is_isinstance_dict_check(node)
            if checked_name is not None and checked_name in self._model_dump_name_stack[-1]:
                self._add(
                    VIOLATION_MODEL_DUMP_DICT_REVALIDATION,
                    node,
                    "isinstance(..., dict) re-validation after model_dump(...) is banned",
                )

        self.generic_visit(node)

    def visit_Constant(self, node: ast.Constant) -> None:
        if _contains_model_dump_must_return_dict_string(node):
            self._add(
                VIOLATION_MODEL_DUMP_MUST_RETURN_DICT_STRING,
                node,
                "Legacy 'model_dump(...) must return dict' string is banned",
            )
        self.generic_visit(node)


def _iter_python_files_from_args(argv: list[str]) -> list[Path]:
    if argv:
        files: list[Path] = []
        for arg in argv:
            candidate = Path(arg)
            if candidate.suffix != ".py":
                continue
            if not candidate.exists():
                continue
            files.append(candidate)
        return files

    return sorted(PROJECT_SRC_ROOT.rglob("*.py"))


def _check_file(path: Path) -> list[Violation]:
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))
    visitor = DefensiveSlopVisitor(path)
    visitor.visit(tree)
    return visitor.violations


def main(argv: list[str]) -> int:
    files = _iter_python_files_from_args(argv)
    if not files:
        return 0

    violations: list[Violation] = []
    for path in files:
        violations.extend(_check_file(path))

    if violations:
        print("Defensive slop violations found:\n")
        for violation in sorted(violations, key=lambda v: (str(v.path), v.line, v.code)):
            print(f"  {violation.format()}")
        print(f"\nTotal: {len(violations)}")
        return 1

    print("No defensive slop patterns found")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
