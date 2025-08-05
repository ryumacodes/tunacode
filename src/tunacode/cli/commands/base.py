"""Base classes and infrastructure for TunaCode CLI commands."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import List

from ...types import CommandArgs, CommandContext, CommandResult


class CommandCategory(Enum):
    """Categories for organizing commands."""

    SYSTEM = "system"
    NAVIGATION = "navigation"
    DEVELOPMENT = "development"
    MODEL = "model"
    DEBUG = "debug"


class Command(ABC):
    """Base class for all commands."""

    @property
    @abstractmethod
    def name(self) -> str:
        """The primary name of the command."""
        pass

    @property
    @abstractmethod
    def aliases(self) -> CommandArgs:
        """Alternative names/aliases for the command."""
        pass

    @property
    def description(self) -> str:
        """Description of what the command does."""
        return ""

    @property
    def category(self) -> CommandCategory:
        """Category this command belongs to."""
        return CommandCategory.SYSTEM

    @abstractmethod
    async def execute(self, _args: CommandArgs, context: CommandContext) -> CommandResult:
        """
        Execute the command.

        Args:
            _args: Command arguments (excluding the command name)
            context: Execution context with state and config

        Returns:
            Command-specific return value
        """
        pass


@dataclass
class CommandSpec:
    """Specification for a command's metadata."""

    name: str
    aliases: List[str]
    description: str
    category: CommandCategory = CommandCategory.SYSTEM


class SimpleCommand(Command):
    """Base class for simple commands without complex logic.

    This class provides a standard implementation for commands that don't
    require special initialization or complex behavior. It reads all
    properties from a class-level CommandSpec attribute.
    """

    spec: CommandSpec

    @property
    def name(self) -> str:
        """The primary name of the command."""
        return self.__class__.spec.name

    @property
    def aliases(self) -> CommandArgs:
        """Alternative names/aliases for the command."""
        return self.__class__.spec.aliases

    @property
    def description(self) -> str:
        """Description of what the command does."""
        return self.__class__.spec.description

    @property
    def category(self) -> CommandCategory:
        """Category this command belongs to."""
        return self.__class__.spec.category
