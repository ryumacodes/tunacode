"""Tests for bash tool timeout validation and prompt contract."""

import pytest

from tunacode.exceptions import ToolRetryError

from tunacode.tools.bash import bash
from tunacode.tools.cache_accessors.xml_prompts_cache import clear_xml_prompts_cache
from tunacode.tools.xml_helper import load_prompt_from_xml


class TestBashTimeoutValidation:
    async def test_rejects_zero_timeout(self) -> None:
        with pytest.raises(ToolRetryError, match="between 1 and 300 seconds"):
            await bash(command="printf ok", timeout=0)

    async def test_rejects_millisecond_timeout_value(self) -> None:
        with pytest.raises(ToolRetryError, match="between 1 and 300 seconds"):
            await bash(command="printf ok", timeout=60000)

    async def test_accepts_minimum_timeout(self) -> None:
        result = await bash(command="printf ok", timeout=1)
        assert "Exit Code: 0" in result

    async def test_accepts_maximum_timeout(self) -> None:
        result = await bash(command="printf ok", timeout=300)
        assert "Exit Code: 0" in result


class TestBashPromptContract:
    def test_bash_prompt_documents_seconds_not_milliseconds(self) -> None:
        clear_xml_prompts_cache()
        prompt = load_prompt_from_xml("bash")

        assert isinstance(prompt, str)
        prompt_lower = prompt.lower()
        assert "timeout in seconds" in prompt_lower
        assert "default 30" in prompt_lower
        assert "1-300" in prompt_lower
        assert "milliseconds" not in prompt_lower
