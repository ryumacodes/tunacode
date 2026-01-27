"""File autocomplete dropdown widget for @ mentions."""

from __future__ import annotations

from textual.widgets import Input
from textual_autocomplete import AutoComplete, DropdownItem, TargetState

from tunacode.core.file_filter import FileFilter


class FileAutoComplete(AutoComplete):
    """Real-time @ file autocomplete dropdown."""

    def __init__(self, target: Input) -> None:
        self._filter = FileFilter()
        super().__init__(target)

    def get_search_string(self, target_state: TargetState) -> str:
        """Extract ONLY the part after @ symbol."""
        text = target_state.text
        cursor = target_state.cursor_position
        at_pos = text.rfind("@", 0, cursor)
        if at_pos == -1:
            return ""
        prefix_region = text[at_pos + 1 : cursor]
        if " " in prefix_region:
            return ""
        return prefix_region

    def get_candidates(self, target_state: TargetState) -> list[DropdownItem]:
        """Return file candidates for current search."""
        search = self.get_search_string(target_state)
        at_pos = target_state.text.rfind("@", 0, target_state.cursor_position)
        if at_pos == -1:
            return []
        candidates = self._filter.complete(search)
        return [DropdownItem(main=f"@{path}") for path in candidates]

    def apply_completion(self, value: str, state: TargetState) -> None:
        """Replace @path region with completed value."""
        text = state.text
        cursor = state.cursor_position
        at_pos = text.rfind("@", 0, cursor)
        if at_pos != -1:
            new_text = text[:at_pos] + value + text[cursor:]
            self.target.value = new_text
            self.target.cursor_position = at_pos + len(value)
