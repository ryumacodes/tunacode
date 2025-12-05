"""Model picker modal screens for TunaCode."""

from __future__ import annotations

from textual import events
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Input, OptionList, Static
from textual.widgets.option_list import Option

from tunacode.configuration.models import get_models_for_provider, get_providers


class ProviderPickerScreen(Screen[str | None]):
    """Modal screen for provider selection (step 1 of model picker)."""

    CSS = """
    ProviderPickerScreen {
        align: center middle;
    }

    #provider-container {
        width: 50;
        height: auto;
        max-height: 28;
        border: solid $primary;
        background: $surface;
        padding: 1 2;
    }

    #provider-title {
        text-style: bold;
        color: $accent;
        text-align: center;
        margin-bottom: 1;
    }

    #provider-filter {
        height: 3;
        margin-bottom: 1;
    }

    #provider-list {
        height: auto;
        max-height: 18;
    }
    """

    BINDINGS = [
        ("escape", "cancel", "Cancel"),
    ]

    def __init__(self, current_model: str) -> None:
        super().__init__()
        self._current_model = current_model
        self._current_provider = current_model.split(":")[0] if ":" in current_model else ""
        self._all_providers: list[tuple[str, str]] = []
        self._filter_query: str = ""

    def compose(self) -> ComposeResult:
        self._all_providers = get_providers()

        with Vertical(id="provider-container"):
            yield Static("Select Provider", id="provider-title")
            yield Input(placeholder="Filter providers...", id="provider-filter")
            yield OptionList(id="provider-list")

        self.call_after_refresh(self._rebuild_options)

    def _rebuild_options(self) -> None:
        """Rebuild OptionList with filtered items."""
        option_list = self.query_one("#provider-list", OptionList)
        option_list.clear_options()

        query = self._filter_query.lower()
        highlight_index = 0
        matched_count = 0

        for display_name, provider_id in self._all_providers:
            if query and query not in display_name.lower():
                continue
            option_list.add_option(Option(display_name, id=provider_id))
            if provider_id == self._current_provider:
                highlight_index = matched_count
            matched_count += 1

        if matched_count > 0:
            option_list.highlighted = highlight_index

    def on_input_changed(self, event: Input.Changed) -> None:
        """Filter options as user types."""
        if event.input.id != "provider-filter":
            return
        self._filter_query = event.value
        self._rebuild_options()

    def on_key(self, event: events.Key) -> None:
        """Handle focus transitions between Input and OptionList."""
        filter_input = self.query_one("#provider-filter", Input)
        option_list = self.query_one("#provider-list", OptionList)

        if event.key == "down" and self.focused == filter_input:
            self.set_focus(option_list)
            event.stop()
        elif event.key == "up" and self.focused == option_list:
            if option_list.highlighted == 0:
                self.set_focus(filter_input)
                event.stop()
        elif event.key == "escape" and self._filter_query:
            filter_input.value = ""
            self._filter_query = ""
            self._rebuild_options()
            event.stop()

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        """Confirm selection and dismiss with provider ID."""
        if event.option and event.option.id:
            self.dismiss(str(event.option.id))

    def action_cancel(self) -> None:
        """Cancel selection."""
        self.dismiss(None)


class ModelPickerScreen(Screen[str | None]):
    """Modal screen for model selection (step 2 of model picker)."""

    CSS = """
    ModelPickerScreen {
        align: center middle;
    }

    #model-container {
        width: 60;
        height: auto;
        max-height: 28;
        border: solid $primary;
        background: $surface;
        padding: 1 2;
    }

    #model-title {
        text-style: bold;
        color: $accent;
        text-align: center;
        margin-bottom: 1;
    }

    #model-filter {
        height: 3;
        margin-bottom: 1;
    }

    #model-list {
        height: auto;
        max-height: 18;
    }
    """

    BINDINGS = [
        ("escape", "cancel", "Cancel"),
    ]

    def __init__(self, provider_id: str, current_model: str) -> None:
        super().__init__()
        self._provider_id = provider_id
        self._current_model = current_model
        current_model_id = current_model.split(":", 1)[1] if ":" in current_model else ""
        self._current_model_id = current_model_id
        self._all_models: list[tuple[str, str]] = []
        self._filter_query: str = ""

    def compose(self) -> ComposeResult:
        self._all_models = get_models_for_provider(self._provider_id)

        with Vertical(id="model-container"):
            yield Static(f"Select Model ({self._provider_id})", id="model-title")
            yield Input(placeholder="Filter models...", id="model-filter")
            yield OptionList(id="model-list")

        self.call_after_refresh(self._rebuild_options)

    def _rebuild_options(self) -> None:
        """Rebuild OptionList with filtered items and pricing."""
        from tunacode.pricing import format_pricing_display, get_model_pricing

        option_list = self.query_one("#model-list", OptionList)
        option_list.clear_options()

        query = self._filter_query.lower()
        highlight_index = 0
        matched_count = 0

        for display_name, model_id in self._all_models:
            if query and query not in display_name.lower():
                continue

            full_model = f"{self._provider_id}:{model_id}"
            pricing = get_model_pricing(full_model)
            if pricing is not None:
                label = f"{display_name}  {format_pricing_display(pricing)}"
            else:
                label = display_name

            option_list.add_option(Option(label, id=model_id))
            if model_id == self._current_model_id:
                highlight_index = matched_count
            matched_count += 1

        if matched_count > 0:
            option_list.highlighted = highlight_index

    def on_input_changed(self, event: Input.Changed) -> None:
        """Filter options as user types."""
        if event.input.id != "model-filter":
            return
        self._filter_query = event.value
        self._rebuild_options()

    def on_key(self, event: events.Key) -> None:
        """Handle focus transitions between Input and OptionList."""
        filter_input = self.query_one("#model-filter", Input)
        option_list = self.query_one("#model-list", OptionList)

        if event.key == "down" and self.focused == filter_input:
            self.set_focus(option_list)
            event.stop()
        elif event.key == "up" and self.focused == option_list:
            if option_list.highlighted == 0:
                self.set_focus(filter_input)
                event.stop()
        elif event.key == "escape" and self._filter_query:
            filter_input.value = ""
            self._filter_query = ""
            self._rebuild_options()
            event.stop()

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        """Confirm selection and dismiss with full model string."""
        if event.option and event.option.id:
            full_model = f"{self._provider_id}:{event.option.id}"
            self.dismiss(full_model)

    def action_cancel(self) -> None:
        """Cancel selection."""
        self.dismiss(None)
