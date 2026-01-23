#!/usr/bin/env python3
"""Check naming conventions for Python files in the repository.

Enforces:
- snake_case for functions, methods, variables, parameters
- PascalCase for classes, type aliases, enums
- UPPER_CASE for constants
- snake_case for module/file names
- Private members start with single underscore
"""

import ast
import re
import sys
from collections.abc import Iterator
from pathlib import Path

SNAKE_CASE = re.compile(r"^[a-z_][a-z0-9_]*$")
UPPER_CASE = re.compile(r"^[A-Z_][A-Z0-9_]*$")
PASCAL_CASE = re.compile(r"^[A-Z][a-zA-Z0-9]*$")
PRIVATE_PREFIX = re.compile(r"^_[a-z][a-z0-9_]*$")
DUNDER = re.compile(r"^__[a-z_][a-z0-9_]*__$")

# Patterns that should be ignored
IGNORE_PATTERNS = {
    # Standard dunder methods
    r"^__[a-z_]+__$",
    # pytest fixtures and test patterns
    r"^test_.*",
    r".*_fixture$",
    # Type checking imports
    r"^TYPE_CHECKING$",
    # Common patterns
    r"^T$",  # Generic type variable
    r"^P$",  # ParamSpec
    r"^R$",  # Return type
}

# Known exceptions - things that legitimately don't follow conventions
EXCEPTIONS = {
    "T",  # Generic TypeVar
    "P",  # ParamSpec
    "R",  # Return type
    "TYPE_CHECKING",  # typing module
    "NotImplemented",  # Python builtin
}

VIOLATION_PREFIX = "❌"
SUCCESS_PREFIX = "✅"


class NamingViolation:
    """Represents a naming convention violation."""

    def __init__(
        self,
        filepath: Path,
        lineno: int,
        name: str,
        expected: str,
        actual: str,
    ) -> None:
        self.filepath = filepath
        self.lineno = lineno
        self.name = name
        self.expected = expected
        self.actual = actual

    def __str__(self) -> str:
        return (
            f"{self.filepath}:{self.lineno}: "
            f"'{self.name}' should be {self.expected}, not {self.actual}"
        )


def should_ignore(name: str) -> bool:
    """Check if a name should be ignored."""
    if name in EXCEPTIONS:
        return True
    return any(re.match(pattern, name) for pattern in IGNORE_PATTERNS)


def is_constant(node: ast.AST) -> bool:
    """Determine if an assignment is a constant.

    Constants are:
    - Module-level assignments
    - Assignments with all-caps names
    - Assignments in TYPE_CHECKING blocks
    """
    # If it's all uppercase, treat as constant
    return isinstance(node, ast.Name) and bool(UPPER_CASE.match(node.id))


def check_function_name(node: ast.FunctionDef, filepath: Path) -> Iterator[NamingViolation]:
    """Check function/method naming conventions."""
    name = node.name

    if should_ignore(name):
        return

    # Private methods/functions
    if name.startswith("_") and not DUNDER.match(name):
        if not PRIVATE_PREFIX.match(name):
            yield NamingViolation(
                filepath,
                node.lineno,
                name,
                "snake_case with leading underscore",
                "invalid private name",
            )
    # Dunder methods are OK
    elif DUNDER.match(name):
        return
    # Public methods/functions
    elif not SNAKE_CASE.match(name):
        yield NamingViolation(filepath, node.lineno, name, "snake_case", "not snake_case")


def check_class_name(node: ast.ClassDef, filepath: Path) -> Iterator[NamingViolation]:
    """Check class naming conventions."""
    name = node.name

    if should_ignore(name):
        return

    # Private classes
    if name.startswith("_"):
        private_pascal = re.compile(r"^_[A-Z][a-zA-Z0-9]*$")
        if not private_pascal.match(name):
            yield NamingViolation(
                filepath,
                node.lineno,
                name,
                "PascalCase with leading underscore",
                "invalid private class",
            )
    # Public classes
    elif not PASCAL_CASE.match(name):
        yield NamingViolation(filepath, node.lineno, name, "PascalCase", "not PascalCase")


def check_parameter_names(
    node: ast.FunctionDef | ast.AsyncFunctionDef, filepath: Path
) -> Iterator[NamingViolation]:
    """Check parameter naming conventions."""
    for arg in node.args.args:
        name = arg.arg
        if should_ignore(name) or name == "self" or name == "cls":
            continue

        if not SNAKE_CASE.match(name):
            yield NamingViolation(filepath, node.lineno, name, "snake_case", "not snake_case")


def is_type_alias(node: ast.Assign | ast.AnnAssign) -> bool:
    """Determine if assignment is a type alias.

    Type aliases are:
    - Simple assignments like: ModelName = str
    - Type unions like: FilePath = str | Path
    - Generic types like: Validator = Callable[[str], bool]
    - Assignments to typing constructs
    """
    if isinstance(node, ast.Assign):
        # Check if the value is a type-related construct
        value = node.value
        if isinstance(value, ast.Name):
            # Simple type alias like: ModelName = str
            return True
        if isinstance(value, ast.BinOp) and isinstance(value.op, ast.BitOr):
            # Union types like: FilePath = str | Path
            return True
        if isinstance(value, ast.Subscript):
            # Generic types like: list[str], dict[str, Any]
            return True
        if isinstance(value, (ast.Tuple, ast.List)):
            # Type tuples
            return True

    return False


def check_module_level_names(
    node: ast.Assign | ast.AnnAssign, filepath: Path
) -> Iterator[NamingViolation]:
    """Check module-level variable and constant naming."""
    targets = node.targets if isinstance(node, ast.Assign) else [node.target]

    for target in targets:
        if isinstance(target, ast.Name):
            name = target.id

            if should_ignore(name):
                continue

            # Type aliases are PascalCase (both annotated and simple assignments)
            if isinstance(node, ast.AnnAssign) and node.annotation:
                # Annotated type aliases or typed constants
                if PASCAL_CASE.match(name):
                    continue
                # Allow snake_case for annotated variables
                if SNAKE_CASE.match(name):
                    continue
                # Allow UPPER_CASE for typed constants
                if UPPER_CASE.match(name):
                    continue
            elif isinstance(node, ast.Assign) and is_type_alias(node):
                # Simple type aliases: ModelName = str
                if PASCAL_CASE.match(name):
                    continue

            # Constants should be UPPER_CASE
            if UPPER_CASE.match(name):
                continue

            # Private module variables with underscore are OK
            if name.startswith("_") and PRIVATE_PREFIX.match(name):
                continue

            # Otherwise should be snake_case
            if not SNAKE_CASE.match(name):
                yield NamingViolation(
                    filepath,
                    node.lineno,
                    name,
                    "UPPER_CASE (constants) or snake_case (variables)",
                    "invalid module-level name",
                )


def check_file(filepath: Path) -> list[NamingViolation]:
    """Check a single Python file for naming violations."""
    violations: list[NamingViolation] = []

    # Check filename is snake_case
    if filepath.name != "__init__.py":
        stem = filepath.stem
        if not SNAKE_CASE.match(stem):
            violations.append(
                NamingViolation(
                    filepath,
                    0,
                    filepath.name,
                    "snake_case.py",
                    "filename not snake_case",
                )
            )

    try:
        content = filepath.read_text(encoding="utf-8")
        tree = ast.parse(content, filename=str(filepath))
    except Exception as e:
        print(f"{VIOLATION_PREFIX} Error parsing {filepath}: {e}", file=sys.stderr)
        return violations

    # Check module-level assignments first
    for node in tree.body:
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            violations.extend(check_module_level_names(node, filepath))

    # Walk all nodes for functions and classes
    for ast_node in ast.walk(tree):
        # Check function/method names
        if isinstance(ast_node, ast.FunctionDef):
            violations.extend(check_function_name(ast_node, filepath))
            violations.extend(check_parameter_names(ast_node, filepath))
        elif isinstance(ast_node, ast.AsyncFunctionDef):
            violations.extend(check_parameter_names(ast_node, filepath))

        # Check class names
        elif isinstance(ast_node, ast.ClassDef):
            violations.extend(check_class_name(ast_node, filepath))

    return violations


def main() -> int:
    """Check all Python files passed as arguments."""
    if len(sys.argv) < 2:
        print("Usage: check-naming-conventions.py <file1.py> [file2.py ...]")
        return 0

    files = [Path(f) for f in sys.argv[1:]]
    all_violations: list[NamingViolation] = []

    for filepath in files:
        if not filepath.exists():
            print(f"{VIOLATION_PREFIX} File not found: {filepath}", file=sys.stderr)
            continue

        violations = check_file(filepath)
        all_violations.extend(violations)

    # Report violations
    if all_violations:
        print(f"\n{VIOLATION_PREFIX} Naming convention violations found:\n")
        for violation in all_violations:
            print(f"  {violation}")
        print(f"\n{len(all_violations)} violation(s) found")
        return 1

    print(f"{SUCCESS_PREFIX} All naming conventions followed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
