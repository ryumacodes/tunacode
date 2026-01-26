"""Core facade for LSP status used by the UI."""

from tunacode.types import UserConfig

from tunacode.tools.lsp_status import get_lsp_status as _get_lsp_status

LspStatus = tuple[bool, str | None]


def get_lsp_status(user_config: UserConfig) -> LspStatus:
    """Return LSP status for UI without direct tool-layer imports."""
    return _get_lsp_status(user_config)
