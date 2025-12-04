# Research – @ File Picker with Smart Filtering

**Date:** 2025-12-04
**Last Updated:** 2025-12-04
**Owner:** Claude Agent
**Phase:** Research
**Git Commit:** 0efa9dd
**Branch:** textual_repl

## Goal

Implement elegant @ file autocomplete with:
- **Trigger:** Dropdown appears immediately on `@` keystroke
- **Filter:** Type more characters to narrow results
- **Select:** Tab autocompletes highlighted item from list
- **Filtering:** Gitignore-style to exclude .venv, node_modules, __pycache__, etc.

## User Flow

```
1. User types: "check @"
2. Dropdown appears immediately with filtered files:
   ┌─────────────────────────┐
   │ src/                    │
   │ tests/                  │
   │ pyproject.toml          │
   └─────────────────────────┘
3. User continues typing: "check @src/tuna"
4. Dropdown filters in real-time:
   ┌─────────────────────────┐
   │ src/tunacode/           │
   │ src/tunacode/ui/        │
   │ src/tunacode/core/      │
   └─────────────────────────┘
5. User presses Tab
6. Highlighted item inserted: "check @src/tunacode/"
```

---

## Current Implementation

| File | Purpose |
|------|---------|
| `src/tunacode/ui/widgets/editor.py:37-56` | `action_complete()` - Tab completion |
| `src/tunacode/ui/widgets/editor.py:70-97` | `_current_token()` - extracts @prefix |
| `src/tunacode/utils/ui/completion.py:8-26` | `textual_complete_paths()` - filesystem matching |
| `src/tunacode/ui/app.py:170-171` | Handler - logs to RichLog |

**Gaps:**
- No real-time dropdown on `@` keystroke
- No gitignore filtering

---

## Dependencies

```bash
uv add pathspec              # Gitignore-style filtering
uv add textual-autocomplete  # Inline dropdown widget
```

---

## Implementation

### 1. File Filter (`src/tunacode/utils/ui/file_filter.py`)

```python
from __future__ import annotations
import os
from pathlib import Path
import pathspec

DEFAULT_IGNORES = [
    ".git/",
    ".venv/", "venv/", "env/",
    "node_modules/",
    "__pycache__/", "*.pyc", "*.pyo",
    "*.egg-info/",
    ".DS_Store", "Thumbs.db",
    ".idea/", ".vscode/",
    "build/", "dist/", "target/",
    ".env",
]


class FileFilter:
    """Gitignore-aware file filtering."""

    def __init__(self, root: Path | None = None):
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
```

### 2. Autocomplete Widget (`src/tunacode/ui/widgets/file_autocomplete.py`)

```python
from __future__ import annotations
from textual.widgets import TextArea
from textual_autocomplete import AutoComplete, DropdownItem, TargetState
from tunacode.utils.ui.file_filter import FileFilter


class FileAutoComplete(AutoComplete):
    """Real-time @ file autocomplete dropdown."""

    def __init__(self, target: TextArea) -> None:
        self._filter = FileFilter()
        super().__init__(target, candidates=self._get_candidates)

    def _get_candidates(self, state: TargetState) -> list[DropdownItem]:
        """Generate candidates when @ is detected."""
        text = state.text
        cursor = state.cursor_position

        # Find @ before cursor
        at_pos = text.rfind("@", 0, cursor)
        if at_pos == -1:
            return []  # No dropdown

        # Extract prefix after @
        prefix = text[at_pos + 1:cursor]

        # Get filtered completions
        candidates = self._filter.complete(prefix)

        return [
            DropdownItem(
                main=f"@{path}",
                right_meta="dir" if path.endswith("/") else "",
            )
            for path in candidates
        ]
```

### 3. Wire Up in App (`src/tunacode/ui/app.py`)

```python
from tunacode.ui.widgets.file_autocomplete import FileAutoComplete

class TextualReplApp(App):
    def compose(self) -> ComposeResult:
        yield Header()
        yield RichLog(...)
        yield self.editor
        yield FileAutoComplete(self.editor)  # Dropdown appears on @
        yield Footer()
```

### 4. Update Editor Bindings (`src/tunacode/ui/widgets/editor.py`)

```python
BINDINGS = [
    Binding("tab", "complete", "Autocomplete", show=False),
    Binding("enter", "submit", "Submit", show=False),
    Binding("ctrl+o", "insert_newline", "Newline", show=False),
]

def action_complete(self) -> None:
    """Tab pressed - accept autocomplete selection."""
    # textual-autocomplete handles Tab to select highlighted item
    pass
```

---

## File Structure

```
src/tunacode/
├── utils/ui/
│   ├── completion.py          # Existing (can simplify)
│   └── file_filter.py         # NEW: gitignore-aware filter
└── ui/widgets/
    ├── editor.py              # Update bindings
    └── file_autocomplete.py   # NEW: AutoComplete wrapper
```

---

## Behavior

| Action | Result |
|--------|--------|
| Type `@` | Dropdown appears with root-level files |
| Type `@src/` | Dropdown shows src/ contents |
| Arrow keys | Navigate dropdown |
| Tab | Insert highlighted item, close dropdown |
| Escape | Close dropdown |
| Space or continue typing | Filter/update dropdown |

## Default Ignore Patterns

```
.git/           # Version control
.venv/          # Python virtualenvs
venv/
env/
node_modules/   # Node packages
__pycache__/    # Python bytecode
*.egg-info/     # Python packaging
.DS_Store       # macOS
.idea/          # JetBrains
.vscode/        # VSCode
build/          # Build artifacts
dist/
.env            # Secrets
```

Plus anything in project's `.gitignore`.

---

## References

- `src/tunacode/ui/widgets/editor.py` - Editor widget
- [textual-autocomplete](https://github.com/darrenburns/textual-autocomplete) - Dropdown widget
- [pathspec](https://python-path-specification.readthedocs.io/) - Gitignore matching
