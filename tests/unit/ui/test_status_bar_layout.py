"""Layout tests for the bottom StatusBar widget."""

from textual.widgets import Static

from tunacode.core.session import StateManager

from tunacode.ui.app import TextualReplApp
from tunacode.ui.widgets.status_bar import StatusBar

MIN_STATUS_BAR_CONTENT_HEIGHT = 1


def _status_right_text(status_bar: StatusBar) -> str:
    right_status = status_bar.query_one("#status-right", Static)
    renderable = right_status.renderable
    if hasattr(renderable, "plain"):
        return str(renderable.plain)
    return str(renderable)


async def test_status_bar_content_region_is_visible() -> None:
    """StatusBar must reserve a content row in addition to its top bevel border."""
    app = TextualReplApp(state_manager=StateManager())

    async with app.run_test(headless=True):
        status_bar = app.query_one(StatusBar)
        assert status_bar.content_region.height >= MIN_STATUS_BAR_CONTENT_HEIGHT


async def test_status_bar_keeps_running_state_visible_until_all_tools_complete() -> None:
    app = TextualReplApp(state_manager=StateManager())

    async with app.run_test(headless=True):
        status_bar = app.query_one(StatusBar)
        status_bar.update_running_action("read_file")
        status_bar.update_running_action("bash")
        assert _status_right_text(status_bar) == "running: bash +1"

        status_bar.complete_running_action("read_file")
        status_bar.update_last_action("read_file")
        assert _status_right_text(status_bar) == "running: bash"

        status_bar.complete_running_action("bash")
        status_bar.update_last_action("bash")
        assert _status_right_text(status_bar) == "last: bash"
