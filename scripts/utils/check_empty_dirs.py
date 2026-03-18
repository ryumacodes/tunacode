#!/usr/bin/env python3
"""Check for empty directories or __init__.py-only directories in src/.

Run: uv run python scripts/utils/check_empty_dirs.py
Exit code: 0 if clean, 1 if issues found.
"""

import sys
from pathlib import Path


def main() -> int:
    src_root = Path(__file__).resolve().parents[2] / "src" / "tunacode"

    if not src_root.exists():
        print(f"Error: {src_root} does not exist")
        return 1

    issues = []

    for dir_path in sorted(src_root.rglob("*")):
        if dir_path.is_dir() and dir_path.name != "__pycache__":
            # Count non-special files
            files = [f for f in dir_path.iterdir() if f.is_file()]
            subdirs = [d for d in dir_path.iterdir() if d.is_dir() and d.name != "__pycache__"]

            # Check if empty or only __init__.py
            if len(files) == 0 and len(subdirs) == 0:
                issues.append(f"Empty directory: {dir_path.relative_to(src_root)}")
            elif len(files) == 1 and len(subdirs) == 0 and files[0].name == "__init__.py":
                issues.append(f"Directory with only __init__.py: {dir_path.relative_to(src_root)}")

    if issues:
        print("❌ Found empty or __init__.py-only directories:")
        for issue in issues:
            print(f"  - {issue}")
        print("\nRemove empty directories or add meaningful content.")
        return 1

    print("✅ No empty directories found.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
