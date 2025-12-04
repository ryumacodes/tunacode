from __future__ import annotations

from pathlib import Path

import pathspec

DEFAULT_IGNORES = [
    ".git/",
    ".venv/",
    "venv/",
    "env/",
    "node_modules/",
    "__pycache__/",
    "*.pyc",
    "*.pyo",
    "*.egg-info/",
    ".DS_Store",
    "Thumbs.db",
    ".idea/",
    ".vscode/",
    "build/",
    "dist/",
    "target/",
    ".env",
]


class FileFilter:
    """Gitignore-aware file filtering."""

    def __init__(self, root: Path | None = None) -> None:
        self.root = root or Path(".")
        self._spec = self._build_spec()

    def _build_spec(self) -> pathspec.PathSpec:
        patterns = list(DEFAULT_IGNORES)
        gitignore = self.root / ".gitignore"
        if gitignore.exists():
            patterns.extend(gitignore.read_text().splitlines())
        return pathspec.PathSpec.from_lines("gitwildmatch", patterns)

    def is_ignored(self, path: Path) -> bool:
        try:
            rel = path.relative_to(self.root)
            return self._spec.match_file(str(rel))
        except ValueError:
            return False

    def complete(self, prefix: str = "", limit: int = 20) -> list[str]:
        """Return filtered file paths matching prefix."""
        results: list[str] = []

        if not prefix:
            search_path = self.root
            name_prefix = ""
        else:
            search_path = self.root / prefix
            if not search_path.exists():
                search_path = search_path.parent
                name_prefix = Path(prefix).name
            else:
                name_prefix = ""

        if not search_path.exists():
            return []

        for entry in sorted(search_path.iterdir()):
            if self.is_ignored(entry):
                continue
            if name_prefix and not entry.name.startswith(name_prefix):
                continue

            rel = entry.relative_to(self.root)
            display = f"{rel}/" if entry.is_dir() else str(rel)
            results.append(display)

            if len(results) >= limit:
                break

        return results
