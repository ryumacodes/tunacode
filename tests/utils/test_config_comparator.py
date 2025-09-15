"""
Tests for configuration comparison functionality.
"""

import pytest

from tunacode.configuration.defaults import DEFAULT_USER_CONFIG
from tunacode.utils.config_comparator import (
    ConfigAnalysis,
    ConfigComparator,
    ConfigDifference,
    create_config_report,
    load_and_analyze_config,
)


class TestConfigComparator:
    """Test suite for ConfigComparator class."""

    def test_analyze_empty_config(self):
        """Test analysis of empty user configuration."""
        comparator = ConfigComparator()
        analysis = comparator.analyze_config({})

        assert analysis.total_keys > 0
        assert len(analysis.missing_keys) > 0
        assert analysis.custom_percentage == 0

    def test_analyze_default_config(self):
        """Test analysis of default configuration (should show no differences)."""
        comparator = ConfigComparator()
        analysis = comparator.analyze_config(DEFAULT_USER_CONFIG.copy())

        assert len(analysis.custom_keys) == 0
        assert len(analysis.missing_keys) == 0
        assert len(analysis.extra_keys) == 0
        assert len(analysis.type_mismatches) == 0
        assert analysis.custom_percentage == 0

    def test_analyze_custom_config(self):
        """Test analysis of configuration with custom values."""
        custom_config = {
            "default_model": "custom:model",
            "env": {
                "ANTHROPIC_API_KEY": "test-key",
                "CUSTOM_ENV_VAR": "custom-value",  # Extra key
            },
            "settings": {
                "max_retries": 5,  # Custom value
                "custom_setting": "custom",  # Extra key
            },
        }

        comparator = ConfigComparator()
        analysis = comparator.analyze_config(custom_config)

        assert len(analysis.custom_keys) >= 2  # default_model and max_retries
        assert len(analysis.extra_keys) >= 2  # CUSTOM_ENV_VAR and custom_setting
        assert analysis.custom_percentage > 0

    def test_type_mismatch_detection(self):
        """Test detection of type mismatches."""
        mismatch_config = {
            "settings": {
                "max_retries": "invalid",  # Should be int
                "enable_streaming": "true",  # Should be bool
            }
        }

        comparator = ConfigComparator()
        analysis = comparator.analyze_config(mismatch_config)

        assert len(analysis.type_mismatches) >= 2
        assert any("max_retries" in key for key in analysis.type_mismatches)
        assert any("enable_streaming" in key for key in analysis.type_mismatches)

    def test_missing_keys_detection(self):
        """Test detection of missing configuration keys."""
        partial_config = {
            "default_model": "test:model"
            # Missing env, settings, mcpServers sections
        }

        comparator = ConfigComparator()
        analysis = comparator.analyze_config(partial_config)

        assert len(analysis.missing_keys) > 0
        assert any("env" in key for key in analysis.missing_keys)
        assert any("settings" in key for key in analysis.missing_keys)

    def test_get_summary_stats(self):
        """Test summary statistics generation."""
        custom_config = {"default_model": "custom:model", "settings": {"max_retries": 5}}

        comparator = ConfigComparator()
        analysis = comparator.analyze_config(custom_config)
        stats = comparator.get_summary_stats(analysis)

        assert isinstance(stats["total_keys_analyzed"], int)
        assert isinstance(stats["custom_keys_count"], int)
        assert isinstance(stats["custom_percentage"], float)
        assert "has_issues" in stats

    def test_get_section_analysis(self):
        """Test section-specific analysis."""
        custom_config = {"default_model": "custom:model", "settings": {"max_retries": 5}}

        comparator = ConfigComparator()
        analysis = comparator.analyze_config(custom_config)

        # Test root section analysis
        root_diffs = comparator.get_section_analysis(analysis, "root")
        assert any("default_model" in diff.key_path for diff in root_diffs)

        # Test settings section analysis
        settings_diffs = comparator.get_section_analysis(analysis, "settings")
        assert any("max_retries" in diff.key_path for diff in settings_diffs)

    def test_is_config_healthy(self):
        """Test configuration health assessment."""
        # Healthy config (no type mismatches)
        healthy_config = {"default_model": "custom:model", "settings": {"max_retries": 5}}

        comparator = ConfigComparator()
        analysis = comparator.analyze_config(healthy_config)
        assert comparator.is_config_healthy(analysis)

        # Unhealthy config (type mismatches)
        unhealthy_config = {"settings": {"max_retries": "invalid"}}

        analysis = comparator.analyze_config(unhealthy_config)
        assert not comparator.is_config_healthy(analysis)

    def test_get_recommendations(self):
        """Test recommendation generation."""
        custom_config = {
            "default_model": "custom:model",
            "settings": {
                "max_retries": "invalid"  # Type mismatch
            },
        }

        comparator = ConfigComparator()
        analysis = comparator.analyze_config(custom_config)
        recommendations = comparator.get_recommendations(analysis)

        assert len(recommendations) > 0
        assert any("type mismatch" in rec.lower() for rec in recommendations)


class TestConfigAnalysis:
    """Test suite for ConfigAnalysis dataclass."""

    def test_config_analysis_structure(self):
        """Test that ConfigAnalysis has required fields."""
        custom_config = {"default_model": "test:model"}
        comparator = ConfigComparator()
        analysis = comparator.analyze_config(custom_config)

        assert hasattr(analysis, "user_config")
        assert hasattr(analysis, "default_config")
        assert hasattr(analysis, "differences")
        assert hasattr(analysis, "custom_keys")
        assert hasattr(analysis, "missing_keys")
        assert hasattr(analysis, "extra_keys")
        assert hasattr(analysis, "type_mismatches")
        assert hasattr(analysis, "sections_analyzed")
        assert hasattr(analysis, "total_keys")
        assert hasattr(analysis, "custom_percentage")


class TestConfigDifference:
    """Test suite for ConfigDifference dataclass."""

    def test_config_difference_structure(self):
        """Test that ConfigDifference has required fields."""
        diff = ConfigDifference(
            key_path="test.key",
            user_value="custom",
            default_value="default",
            difference_type="custom",
            section="test",
            description="Test difference",
        )

        assert diff.key_path == "test.key"
        assert diff.user_value == "custom"
        assert diff.default_value == "default"
        assert diff.difference_type == "custom"
        assert diff.section == "test"
        assert diff.description == "Test difference"


class TestUtilityFunctions:
    """Test suite for utility functions."""

    def test_create_config_report(self):
        """Test report generation."""
        custom_config = {"default_model": "custom:model", "settings": {"max_retries": 5}}

        comparator = ConfigComparator()
        analysis = comparator.analyze_config(custom_config)
        report = create_config_report(analysis)

        assert isinstance(report, str)
        assert "Configuration Analysis Report" in report
        assert "Custom keys:" in report
        assert "Total keys analyzed:" in report

    def test_load_and_analyze_config_with_valid_config(self, tmp_path):
        """Test loading and analyzing config from file."""
        config_data = {"default_model": "test:model", "settings": {"max_retries": 5}}

        config_file = tmp_path / "test_config.json"
        import json

        with open(config_file, "w") as f:
            json.dump(config_data, f)

        analysis = load_and_analyze_config(config_file)

        assert isinstance(analysis, ConfigAnalysis)
        assert len(analysis.custom_keys) > 0

    def test_load_and_analyze_config_with_invalid_file(self):
        """Test error handling for invalid config file."""
        with pytest.raises(ValueError):
            load_and_analyze_config("/nonexistent/path/config.json")

    def test_nested_configuration_analysis(self):
        """Test analysis of deeply nested configuration structures."""
        nested_config = {
            "settings": {
                "ripgrep": {
                    "timeout": 20,  # Custom value
                    "custom_nested": {"deep_key": "deep_value"},
                }
            }
        }

        comparator = ConfigComparator()
        analysis = comparator.analyze_config(nested_config)

        # Should detect custom timeout and extra nested keys
        assert any("timeout" in key for key in analysis.custom_keys)
        assert any("custom_nested" in key for key in analysis.extra_keys)
