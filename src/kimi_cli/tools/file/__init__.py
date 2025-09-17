class FileOpsWindow:
    """Maintains a window of file operations."""

    pass


from .read import ReadFile  # noqa: E402
from .write import WriteFile  # noqa: E402

__all__ = ("ReadFile", "WriteFile")
