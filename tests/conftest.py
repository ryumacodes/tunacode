"""Shared test fixtures for tools tests."""

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
