"""
Characterization tests for TunaCode UI async UI updates.
Covers: async output functions and async-safe UI flows.
"""

import pytest
from unittest.mock import patch, MagicMock

import tunacode.ui.output as output_mod

@pytest.mark.asyncio
async def test_async_print_calls_console_print():
    with patch("tunacode.ui.output.console.print") as mock_print:
        with patch("tunacode.ui.output.run_in_terminal") as mock_run:
            async def fake_run(fn):
                fn()
            mock_run.side_effect = fake_run
            await output_mod.print("Hello", style="bold")
            mock_print.assert_called_once_with("Hello", style="bold")

@pytest.mark.asyncio
async def test_async_info_formats_and_prints():
    with patch("tunacode.ui.output.print") as mock_print:
        await output_mod.info("Test info")
        mock_print.assert_called_once()