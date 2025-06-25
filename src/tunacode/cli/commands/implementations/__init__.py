"""Command implementations for TunaCode CLI."""

# Import all command classes for easy access
from .conversation import CompactCommand
from .debug import (
    DumpCommand,
    FixCommand,
    IterationsCommand,
    ParseToolsCommand,
    ThoughtsCommand,
    YoloCommand,
)
from .development import BranchCommand, InitCommand
from .model import ModelCommand
from .system import ClearCommand, HelpCommand, RefreshConfigCommand, UpdateCommand

__all__ = [
    # System commands
    "HelpCommand",
    "ClearCommand",
    "RefreshConfigCommand",
    "UpdateCommand",
    # Debug commands
    "YoloCommand",
    "DumpCommand",
    "ThoughtsCommand",
    "IterationsCommand",
    "FixCommand",
    "ParseToolsCommand",
    # Development commands
    "BranchCommand",
    "InitCommand",
    # Model commands
    "ModelCommand",
    # Conversation commands
    "CompactCommand",
]
