import pytest

from tunacode.ui import output


@pytest.mark.asyncio
async def test_print_uses_console_when_no_sink(monkeypatch):
    calls: list[object] = []

    async def fake_run_in_terminal(func):
        calls.append(func)

    monkeypatch.setattr(output, "run_in_terminal", fake_run_in_terminal)
    output.clear_output_sink()

    await output.print("hello")

    output.clear_output_sink()
    assert len(calls) == 1


@pytest.mark.asyncio
async def test_print_routes_to_registered_sink(monkeypatch):
    captured: list[tuple[object, dict[str, object]]] = []

    async def fake_run_in_terminal(_func):
        raise AssertionError("run_in_terminal should not be invoked when a sink is set")

    def sink(message: object, options: dict[str, object]) -> None:
        captured.append((message, options))

    monkeypatch.setattr(output, "run_in_terminal", fake_run_in_terminal)
    output.register_output_sink(sink)

    try:
        await output.print("hello", style="bold")
    finally:
        output.clear_output_sink()

    assert captured == [("hello", {"style": "bold"})]
