"""LSP status lookup helpers."""

from pathlib import Path

from tunacode.lsp.servers import get_server_command
from tunacode.types import UserConfig

LSP_STATUS_CHECK_PATH = Path("status_check.py")
SETTINGS_KEY = "settings"
LSP_SETTINGS_KEY = "lsp"
LSP_ENABLED_KEY = "enabled"
LSP_SERVER_NAME_MAP: dict[str, str] = {
    "ruff": "ruff",
    "pyright-langserver": "pyright",
    "pylsp": "pylsp",
    "typescript-language-server": "tsserver",
    "gopls": "gopls",
    "rust-analyzer": "rust-analyzer",
}


LspStatus = tuple[bool, str | None]


def get_lsp_status(user_config: UserConfig) -> LspStatus:
    """Return (enabled, server_name_or_none) based on config and availability."""
    settings = user_config.get(SETTINGS_KEY, {})
    lsp_config = settings.get(LSP_SETTINGS_KEY, {})
    is_enabled = bool(lsp_config.get(LSP_ENABLED_KEY, False))

    if not is_enabled:
        return False, None

    command = get_server_command(LSP_STATUS_CHECK_PATH)
    if command is None:
        return True, None

    server_binary = command[0]
    server_name = LSP_SERVER_NAME_MAP.get(server_binary, server_binary)
    return True, server_name
