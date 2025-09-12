"""
Tests for config file permissions and write access (T102).

Covers:
- Directory creation on first save
- Permission errors surfaced as ConfigurationError
- Updating existing config file
"""

import builtins
import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from tunacode.utils import user_configuration


@pytest.fixture()
def temp_paths(monkeypatch):
    """Provide a temporary config dir/file via ApplicationSettings."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        config_dir = base / "subdir" / "config"
        config_file = config_dir / "tunacode.json"

        # Patch ApplicationSettings to point at our temp paths
        monkeypatch.setattr(
            "tunacode.utils.user_configuration.ApplicationSettings",
            lambda: MagicMock(paths=MagicMock(config_dir=config_dir, config_file=config_file)),
        )
        yield config_dir, config_file


def _mock_state_manager(initial_config=None):
    sm = MagicMock()
    sm.session = MagicMock()
    sm.session.user_config = {} if initial_config is None else dict(initial_config)
    return sm


def test_save_config_creates_directory_if_missing(temp_paths):
    config_dir, config_file = temp_paths
    sm = _mock_state_manager({"default_model": "openai:gpt-4"})

    assert not config_dir.exists()
    ok = user_configuration.save_config(sm)
    assert ok is True
    assert config_dir.exists()
    assert config_file.exists()

    data = json.loads(config_file.read_text())
    assert data["default_model"] == "openai:gpt-4"


def test_save_config_updates_existing_file(temp_paths):
    config_dir, config_file = temp_paths
    config_dir.mkdir(parents=True, exist_ok=True)
    config_file.write_text(json.dumps({"default_model": "openai:gpt-3.5"}))

    sm = _mock_state_manager({"default_model": "anthropic:claude-3-haiku"})
    ok = user_configuration.save_config(sm)
    assert ok is True

    data = json.loads(config_file.read_text())
    assert data["default_model"] == "anthropic:claude-3-haiku"


def test_save_config_permission_denied_raises_configuration_error(temp_paths, monkeypatch):
    config_dir, config_file = temp_paths
    sm = _mock_state_manager({"default_model": "google:gemini-pro"})

    # Make directory creation succeed but simulate open() raising PermissionError
    orig_open = builtins.open

    def fake_open(path, mode="r", *args, **kwargs):
        if str(path) == str(config_file) and "w" in mode:
            raise PermissionError("mock permission denied")
        return orig_open(path, mode, *args, **kwargs)  # pragma: no cover

    monkeypatch.setattr("builtins.open", fake_open)

    with pytest.raises(user_configuration.ConfigurationError):
        user_configuration.save_config(sm)


def test_load_config_invalid_json_raises_configuration_error(temp_paths):
    config_dir, config_file = temp_paths
    config_dir.mkdir(parents=True, exist_ok=True)
    config_file.write_text("{ invalid json }")

    with pytest.raises(user_configuration.ConfigurationError):
        user_configuration.load_config()
