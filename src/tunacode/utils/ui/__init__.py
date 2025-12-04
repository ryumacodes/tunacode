"""UI utilities: completion helpers and data structures."""

from tunacode.utils.ui.completion import replace_token, textual_complete_paths
from tunacode.utils.ui.file_filter import FileFilter
from tunacode.utils.ui.helpers import DotDict

__all__ = [
    "DotDict",
    "FileFilter",
    "replace_token",
    "textual_complete_paths",
]
