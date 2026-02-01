"""Shared test fixtures for tools tests."""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest


@pytest.fixture
def mock_no_xml_prompt():
    """Patch XML loading to return None."""
    with patch("tunacode.tools.decorators.load_prompt_from_xml", return_value=None):
        yield


@pytest.fixture
def mock_xml_prompt():
    """Patch XML loading to return a test prompt."""
    with patch("tunacode.tools.decorators.load_prompt_from_xml", return_value="Test XML prompt"):
        yield


# =============================================================================
# Test Isolation Fixtures
# =============================================================================


@pytest.fixture(autouse=True)
def isolate_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """Isolate tests from environment pollution.

    Removes env vars that could affect test behavior.
    """
    sensitive_vars = [
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY",
        "GEMINI_API_KEY",
        "OPENROUTER_API_KEY",
        "TUNACODE_CONFIG",
    ]
    for var in sensitive_vars:
        monkeypatch.delenv(var, raising=False)


@pytest.fixture
def isolated_tmp_dir() -> Path:
    """Provide a fresh temp directory for each test."""
    with tempfile.TemporaryDirectory(prefix="tunacode_test_") as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def isolated_cwd(isolated_tmp_dir: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Run test with isolated current working directory."""
    monkeypatch.chdir(isolated_tmp_dir)
    return isolated_tmp_dir
