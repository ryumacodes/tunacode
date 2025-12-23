"""Language server command mapping.

Maps file extensions to their corresponding language server commands.
"""

from pathlib import Path
from shutil import which

# Extension to (language_id, server_commands) mapping
# server_commands is a list of possible commands to try in order
SERVER_CONFIG: dict[str, tuple[str, list[list[str]]]] = {
    ".py": (
        "python",
        [
            ["ruff", "server"],
        ],
    ),
    ".pyi": (
        "python",
        [
            ["ruff", "server"],
        ],
    ),
    ".ts": (
        "typescript",
        [
            ["typescript-language-server", "--stdio"],
        ],
    ),
    ".tsx": (
        "typescriptreact",
        [
            ["typescript-language-server", "--stdio"],
        ],
    ),
    ".js": (
        "javascript",
        [
            ["typescript-language-server", "--stdio"],
        ],
    ),
    ".jsx": (
        "javascriptreact",
        [
            ["typescript-language-server", "--stdio"],
        ],
    ),
    ".go": (
        "go",
        [
            ["gopls"],
        ],
    ),
    ".rs": (
        "rust",
        [
            ["rust-analyzer"],
        ],
    ),
}


def get_language_id(path: Path) -> str | None:
    """Get the LSP language ID for a file.

    Args:
        path: Path to the file

    Returns:
        Language ID string or None if unsupported
    """
    ext = path.suffix.lower()
    config = SERVER_CONFIG.get(ext)
    return config[0] if config else None


def get_server_command(path: Path) -> list[str] | None:
    """Get the server command for a file based on its extension.

    Checks if the server binary exists before returning.

    Args:
        path: Path to the file

    Returns:
        Server command list or None if no server available
    """
    ext = path.suffix.lower()
    config = SERVER_CONFIG.get(ext)

    if config is None:
        return None

    _, command_options = config

    for command in command_options:
        binary = command[0]
        if which(binary) is not None:
            return command

    return None
