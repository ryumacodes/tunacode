"""Slash command autocomplete dropdown widget."""

from __future__ import annotations

from textual.widgets import Input
from textual_autocomplete import AutoComplete, DropdownItem, TargetState

from tunacode.ui.commands import COMMANDS

COMMAND_PREFIX = "/"
COMMAND_ARGUMENT_SEPARATOR = " "
COMMAND_DESCRIPTION_SEPARATOR = " - "

# Pre-compute sorted command items at module load.
_COMMAND_ITEMS: list[tuple[str, str]] = sorted(
    [(name, cmd.description) for name, cmd in COMMANDS.items()]
)


def _get_command_search_prefix(text: str, cursor_position: int) -> str | None:
    """Return the command fragment before the cursor, or None outside command name editing."""
    if not text.startswith(COMMAND_PREFIX):
        return None

    command_region = text[len(COMMAND_PREFIX) : cursor_position]
    if COMMAND_ARGUMENT_SEPARATOR in command_region:
        return None

    return command_region


def _is_exact_command_match(command_prefix: str) -> bool:
    """Return True when the typed prefix already names a full slash command."""
    if not command_prefix:
        return False

    return command_prefix.lower() in COMMANDS


class CommandAutoComplete(AutoComplete):
    """Real-time / command autocomplete dropdown."""

    def __init__(self, target: Input) -> None:
        super().__init__(target)

    def get_search_string(self, target_state: TargetState) -> str:
        """Extract text after / symbol at start of input."""
        command_prefix = _get_command_search_prefix(
            target_state.text,
            target_state.cursor_position,
        )
        if command_prefix is None:
            return ""

        return command_prefix

    def should_show_dropdown(self, search_string: str) -> bool:  # noqa: ARG002
        """Show dropdown only while typing a partial command name."""
        del search_string
        if self.option_list.option_count == 0:
            return False

        target_state = self._get_target_state()
        command_prefix = _get_command_search_prefix(
            target_state.text,
            target_state.cursor_position,
        )
        if command_prefix is None:
            return False

        return not _is_exact_command_match(command_prefix)

    def get_candidates(self, target_state: TargetState) -> list[DropdownItem]:
        """Return command candidates for current search."""
        if not target_state.text.startswith(COMMAND_PREFIX):
            return []

        search = self.get_search_string(target_state).lower()
        return [
            DropdownItem(main=f"{COMMAND_PREFIX}{name}{COMMAND_DESCRIPTION_SEPARATOR}{desc}")
            for name, desc in _COMMAND_ITEMS
            if name.startswith(search)
        ]

    def apply_completion(self, value: str, state: TargetState) -> None:
        """Replace /command region with completed value, always add trailing space."""
        command = value.split(COMMAND_DESCRIPTION_SEPARATOR, 1)[0]
        trailing = state.text[state.cursor_position :].lstrip()
        new_text = command + COMMAND_ARGUMENT_SEPARATOR + trailing
        self.target.value = new_text
        self.target.cursor_position = len(command) + len(COMMAND_ARGUMENT_SEPARATOR)
