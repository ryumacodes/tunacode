"""Shared syntax highlighting utilities for tool renderers.

Provides language detection from file extensions and consistent
syntax highlighting across all tool viewports.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from rich.syntax import Syntax
from rich.text import Text

if TYPE_CHECKING:
    from rich.console import RenderableType

# NeXTSTEP-consistent theme used across all renderers
SYNTAX_THEME = "monokai"

# Map file extensions to pygments lexer names
EXTENSION_LEXERS: dict[str, str] = {
    # Python
    ".py": "python",
    ".pyi": "python",
    ".pyw": "python",
    # JavaScript/TypeScript
    ".js": "javascript",
    ".mjs": "javascript",
    ".cjs": "javascript",
    ".jsx": "jsx",
    ".ts": "typescript",
    ".tsx": "tsx",
    # Rust
    ".rs": "rust",
    # Go
    ".go": "go",
    # Java/Kotlin
    ".java": "java",
    ".kt": "kotlin",
    ".kts": "kotlin",
    # C/C++
    ".c": "c",
    ".h": "c",
    ".cpp": "cpp",
    ".cc": "cpp",
    ".cxx": "cpp",
    ".hpp": "cpp",
    ".hxx": "cpp",
    # C#
    ".cs": "csharp",
    # Ruby
    ".rb": "ruby",
    ".rake": "ruby",
    # Shell
    ".sh": "bash",
    ".bash": "bash",
    ".zsh": "zsh",
    ".fish": "fish",
    # Data formats
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".toml": "toml",
    ".xml": "xml",
    ".csv": "text",
    # Markup
    ".md": "markdown",
    ".markdown": "markdown",
    ".rst": "rst",
    ".html": "html",
    ".htm": "html",
    ".css": "css",
    ".scss": "scss",
    ".sass": "sass",
    ".less": "less",
    # Database
    ".sql": "sql",
    # Config
    ".ini": "ini",
    ".cfg": "ini",
    ".conf": "nginx",
    ".env": "bash",
    # Docker
    "Dockerfile": "docker",
    ".dockerfile": "docker",
    # Make
    "Makefile": "make",
    ".mk": "make",
    # Misc
    ".lua": "lua",
    ".vim": "vim",
    ".php": "php",
    ".swift": "swift",
    ".r": "r",
    ".R": "r",
    ".pl": "perl",
    ".pm": "perl",
    ".ex": "elixir",
    ".exs": "elixir",
    ".erl": "erlang",
    ".hs": "haskell",
    ".scala": "scala",
    ".clj": "clojure",
    ".lisp": "lisp",
    ".el": "lisp",
    ".tex": "latex",
    ".proto": "protobuf",
    ".graphql": "graphql",
    ".gql": "graphql",
}


def get_lexer(filepath: str) -> str:
    """Map file extension to pygments lexer name.

    Args:
        filepath: Path to the file (can be relative or absolute)

    Returns:
        Lexer name for syntax highlighting, or "text" if unknown
    """
    path = Path(filepath)
    name = path.name

    # Check for exact filename matches first (Dockerfile, Makefile)
    if name in EXTENSION_LEXERS:
        return EXTENSION_LEXERS[name]

    # Check file extension
    ext = path.suffix.lower()
    return EXTENSION_LEXERS.get(ext, "text")


def get_color(lexer: str) -> str:
    """Map pygments lexer name to color.

    Args:
        lexer: lexer name for syntax highlighting

    Returns:
        Color by type, or "" if unknown
    """
    if lexer == "python":
        return "bright_blue"
    if lexer in ("javascript", "typescript", "jsx", "tsx"):
        return "yellow"
    if lexer in ("json", "yaml", "toml"):
        return "green"
    if lexer in ("markdown", "rst"):
        return "cyan"
    if lexer in ("bash", "zsh"):
        return "magenta"
    return ""


def syntax_or_text(
    content: str,
    filepath: str | None = None,
    lexer: str | None = None,
    line_numbers: bool = False,
    word_wrap: bool = True,
    start_line: int = 1,
    code_width: int | None = None,
) -> RenderableType:
    """Return Syntax if lexer known, else plain Text.

    Provides consistent syntax highlighting across all tool renderers.
    Falls back gracefully to plain text for unknown file types.

    Args:
        content: The code/text content to render
        filepath: Optional path to detect language from extension
        lexer: Optional explicit lexer override (takes precedence over filepath)
        line_numbers: Whether to show line numbers (default: False)
        word_wrap: Whether to wrap long lines (default: True)
        start_line: Starting line number for line_numbers display

    Returns:
        Syntax object for code, or Text for plain content
    """
    if lexer is None and filepath:
        lexer = get_lexer(filepath)

    # Use Syntax for known languages
    if lexer and lexer != "text":
        return Syntax(
            content,
            lexer,
            theme=SYNTAX_THEME,
            word_wrap=word_wrap,
            line_numbers=line_numbers,
            start_line=start_line,
            code_width=code_width,
        )

    # Fall back to plain text
    return Text(content)


# Shebang keyword -> lexer mapping (checked with `in` against the shebang line)
_SHEBANG_LEXERS: tuple[tuple[str, str], ...] = (
    ("python", "python"),
    ("bash", "bash"),
    ("sh", "bash"),
    ("node", "javascript"),
    ("ruby", "ruby"),
    ("perl", "perl"),
)

# Content marker -> lexer mapping (checked with `in` against full content)
_CONTENT_MARKER_LEXERS: tuple[tuple[tuple[str, ...], str], ...] = (
    (("def ", "class ", "import ", "from ", "if __name__"), "python"),
    (("function ", "const ", "let ", "var ", "=>", "export ", "import "), "javascript"),
)


def _detect_shebang(first_line: str) -> str | None:
    """Detect lexer from shebang line."""
    if not first_line.startswith("#!"):
        return None
    for keyword, lexer in _SHEBANG_LEXERS:
        if keyword in first_line:
            return lexer
    return None


def _detect_json(content: str) -> str | None:
    """Detect JSON content."""
    stripped = content.strip()
    if not (stripped.startswith("{") and stripped.endswith("}")):
        return None
    try:
        import json

        json.loads(stripped)
        return "json"
    except (json.JSONDecodeError, ValueError):
        return None


def _detect_by_markers(content: str) -> str | None:
    """Detect language by content markers."""
    for markers, lexer in _CONTENT_MARKER_LEXERS:
        if any(marker in content for marker in markers):
            return lexer
    return None


def detect_code_lexer(content: str) -> str | None:
    """Attempt to detect programming language from content heuristics.

    Used for bash output and other cases where we don't have a filepath.
    Returns None if no confident detection.

    Args:
        content: The content to analyze

    Returns:
        Lexer name if detected, None otherwise
    """
    if not content:
        return None

    first_line = content.split("\n")[0]
    return _detect_shebang(first_line) or _detect_json(content) or _detect_by_markers(content)
