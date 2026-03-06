from __future__ import annotations

import pytest
from rich.table import Table

from tunacode.core.session import StateManager

from tunacode.ui.app import TextualReplApp
from tunacode.ui.widgets.command_autocomplete import CommandAutoComplete


async def _type_text(pilot, text: str) -> None:
    for character in text:
        key = "space" if character == " " else character
        await pilot.press(key)


@pytest.mark.parametrize("command_name", ["help", "compact"])
async def test_command_autocomplete_hides_exact_matches(command_name: str) -> None:
    app = TextualReplApp(state_manager=StateManager())

    async with app.run_test(headless=True) as pilot:
        autocomplete = app.query_one(CommandAutoComplete)

        await _type_text(pilot, f"/{command_name}")
        await pilot.pause()

        assert app.editor.value == f"/{command_name}"
        assert autocomplete.option_list.option_count == 1
        assert autocomplete.display is False


async def test_exact_match_enter_submits_slash_command() -> None:
    app = TextualReplApp(state_manager=StateManager())

    async with app.run_test(headless=True) as pilot:
        autocomplete = app.query_one(CommandAutoComplete)
        initial_message_count = len(app.chat_container.children)

        await _type_text(pilot, "/help")
        await pilot.pause()

        assert autocomplete.display is False

        await pilot.press("enter")
        await pilot.pause()

        assert app.editor.value == ""
        assert len(app.chat_container.children) == initial_message_count + 1
        assert isinstance(app.chat_container.children[-1].renderable, Table)
