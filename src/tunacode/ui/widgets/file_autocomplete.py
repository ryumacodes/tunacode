"""File autocomplete dropdown widget for @ mentions."""

from __future__ import annotations

from textual.widgets import Input
from textual_autocomplete import AutoComplete, DropdownItem, TargetState

from tunacode.utils.ui.file_filter import FileFilter


class FileAutoComplete(AutoComplete):
    """Real-time @ file autocomplete dropdown."""

    def __init__(self, target: Input) -> None:
        self._filter = FileFilter()
        super().__init__(target, candidates=self._get_candidates)

    def _get_candidates(self, state: TargetState) -> list[DropdownItem]:
        """Generate candidates when @ is detected."""
        text = state.text
        cursor = state.cursor_position

        # Find @ before cursor
        at_pos = text.rfind("@", 0, cursor)
        if at_pos == -1:
            return []

        # Check no space between @ and cursor
        prefix_region = text[at_pos + 1 : cursor]
        if " " in prefix_region:
            return []

        # Get filtered completions
        candidates = self._filter.complete(prefix_region)

        return [DropdownItem(main=f"@{path}") for path in candidates]
