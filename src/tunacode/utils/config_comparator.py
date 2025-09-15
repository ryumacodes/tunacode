"""
Module: tunacode.utils.config_comparator

Configuration comparison utility for analyzing user configurations against defaults.
Provides detailed analysis of customizations, defaults, and configuration state.
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union

from tunacode.configuration.defaults import DEFAULT_USER_CONFIG
from tunacode.types import UserConfig


@dataclass
class ConfigDifference:
    """Represents a difference between user config and defaults."""

    key_path: str
    user_value: Any
    default_value: Any
    difference_type: str  # "custom", "missing", "extra", "type_mismatch"
    section: str
    description: str


@dataclass
class ConfigAnalysis:
    """Complete analysis of configuration state."""

    user_config: UserConfig
    default_config: UserConfig
    differences: List[ConfigDifference]
    custom_keys: Set[str]
    missing_keys: Set[str]
    extra_keys: Set[str]
    type_mismatches: Set[str]
    sections_analyzed: Set[str]
    total_keys: int
    custom_percentage: float


class ConfigComparator:
    """Compares user configuration against defaults to identify customizations."""

    def __init__(self, default_config: Optional[UserConfig] = None):
        """Initialize comparator with default configuration."""
        self.default_config = default_config or DEFAULT_USER_CONFIG

    def _get_key_description(self, key_path: str, difference_type: str) -> str:
        """Get a descriptive explanation for a configuration key difference."""
        try:
            from tunacode.configuration.key_descriptions import get_key_description

            desc = get_key_description(key_path)

            if desc:
                if difference_type == "custom":
                    return f"Custom: {desc.description}"
                elif difference_type == "missing":
                    return f"Missing: {desc.description}"
                elif difference_type == "extra":
                    return f"Extra: {desc.description}"
                elif difference_type == "type_mismatch":
                    return f"Type mismatch: {desc.description}"

        except ImportError:
            pass  # Fall back to basic descriptions

        # Fallback descriptions
        if difference_type == "custom":
            return f"Custom value: {key_path}"
        elif difference_type == "missing":
            return f"Missing configuration key: {key_path}"
        elif difference_type == "extra":
            return f"Extra configuration key: {key_path}"
        elif difference_type == "type_mismatch":
            return f"Type mismatch for: {key_path}"

        return f"Configuration difference: {key_path}"

    def analyze_config(self, user_config: UserConfig) -> ConfigAnalysis:
        """Perform complete analysis of user configuration."""
        differences: list[ConfigDifference] = []
        custom_keys: set[str] = set()
        missing_keys: set[str] = set()
        extra_keys: set[str] = set()
        type_mismatches: set[str] = set()

        # Analyze each section recursively
        self._analyze_recursive(
            user_config=user_config,
            default_config=self.default_config,
            current_path="",
            differences=differences,
            custom_keys=custom_keys,
            missing_keys=missing_keys,
            extra_keys=extra_keys,
            type_mismatches=type_mismatches,
        )

        # Calculate statistics
        sections_analyzed: set[str] = set()
        self._collect_sections(user_config, sections_analyzed)
        self._collect_sections(self.default_config, sections_analyzed)

        total_keys = len(custom_keys) + len(missing_keys) + len(extra_keys) + len(type_mismatches)
        custom_percentage = (len(custom_keys) / total_keys * 100) if total_keys > 0 else 0

        return ConfigAnalysis(
            user_config=user_config,
            default_config=self.default_config,
            differences=differences,
            custom_keys=custom_keys,
            missing_keys=missing_keys,
            extra_keys=extra_keys,
            type_mismatches=type_mismatches,
            sections_analyzed=sections_analyzed,
            total_keys=total_keys,
            custom_percentage=custom_percentage,
        )

    def _analyze_recursive(
        self,
        user_config: Dict[str, Any],
        default_config: Dict[str, Any],
        current_path: str,
        differences: List[ConfigDifference],
        custom_keys: Set[str],
        missing_keys: Set[str],
        extra_keys: Set[str],
        type_mismatches: Set[str],
    ) -> None:
        """Recursively analyze configuration differences."""

        # Check for missing keys (present in default but not in user)
        for key, default_value in default_config.items():
            full_key = f"{current_path}.{key}" if current_path else key

            if key not in user_config:
                missing_keys.add(full_key)
                differences.append(
                    ConfigDifference(
                        key_path=full_key,
                        user_value=None,
                        default_value=default_value,
                        difference_type="missing",
                        section=current_path or "root",
                        description=self._get_key_description(full_key, "missing"),
                    )
                )
                continue

            user_value = user_config[key]

            # Recursively analyze nested dictionaries
            if isinstance(default_value, dict) and isinstance(user_value, dict):
                self._analyze_recursive(
                    user_config=user_value,
                    default_config=default_value,
                    current_path=full_key,
                    differences=differences,
                    custom_keys=custom_keys,
                    missing_keys=missing_keys,
                    extra_keys=extra_keys,
                    type_mismatches=type_mismatches,
                )
                continue

            # Check for type mismatches
            if not isinstance(user_value, type(default_value)):
                type_mismatches.add(full_key)
                differences.append(
                    ConfigDifference(
                        key_path=full_key,
                        user_value=user_value,
                        default_value=default_value,
                        difference_type="type_mismatch",
                        section=current_path or "root",
                        description=self._get_key_description(full_key, "type_mismatch"),
                    )
                )
                continue

            # Check for custom values
            if user_value != default_value:
                custom_keys.add(full_key)
                differences.append(
                    ConfigDifference(
                        key_path=full_key,
                        user_value=user_value,
                        default_value=default_value,
                        difference_type="custom",
                        section=current_path or "root",
                        description=self._get_key_description(full_key, "custom"),
                    )
                )

        # Check for extra keys (present in user but not in default)
        for key, user_value in user_config.items():
            if key not in default_config:
                full_key = f"{current_path}.{key}" if current_path else key
                extra_keys.add(full_key)
                differences.append(
                    ConfigDifference(
                        key_path=full_key,
                        user_value=user_value,
                        default_value=None,
                        difference_type="extra",
                        section=current_path or "root",
                        description=self._get_key_description(full_key, "extra"),
                    )
                )

    def _collect_sections(self, config: Dict[str, Any], sections: Set[str]) -> None:
        """Collect all section names from configuration."""
        for key, value in config.items():
            if isinstance(value, dict):
                sections.add(key)
                self._collect_sections(value, sections)

    def get_summary_stats(self, analysis: ConfigAnalysis) -> Dict[str, Any]:
        """Get summary statistics for the configuration analysis."""
        return {
            "total_keys_analyzed": analysis.total_keys,
            "custom_keys_count": len(analysis.custom_keys),
            "missing_keys_count": len(analysis.missing_keys),
            "extra_keys_count": len(analysis.extra_keys),
            "type_mismatches_count": len(analysis.type_mismatches),
            "custom_percentage": analysis.custom_percentage,
            "sections_analyzed": len(analysis.sections_analyzed),
            "has_issues": bool(analysis.missing_keys or analysis.type_mismatches),
        }

    def get_section_analysis(
        self, analysis: ConfigAnalysis, section: str
    ) -> List[ConfigDifference]:
        """Get differences for a specific section."""
        return [diff for diff in analysis.differences if diff.section == section]

    def is_config_healthy(self, analysis: ConfigAnalysis) -> bool:
        """Check if configuration is healthy (no critical issues)."""
        # Type mismatches are considered critical
        if analysis.type_mismatches:
            return False

        # Missing keys might be acceptable depending on the context
        # For now, we'll consider missing keys as warnings, not errors
        return True

    def get_recommendations(self, analysis: ConfigAnalysis) -> List[str]:
        """Get recommendations based on configuration analysis."""
        recommendations = []

        if analysis.type_mismatches:
            recommendations.append(
                f"Fix {len(analysis.type_mismatches)} type mismatch(es) in configuration"
            )

        if analysis.missing_keys:
            recommendations.append(
                f"Consider adding {len(analysis.missing_keys)} missing configuration key(s)"
            )

        if analysis.custom_percentage > 80:
            recommendations.append(
                "High customization detected - consider documenting your configuration"
            )

        if analysis.extra_keys:
            recommendations.append(
                f"Found {len(analysis.extra_keys)} unrecognized configuration key(s)"
            )

        return recommendations


def load_and_analyze_config(config_path: Optional[Union[str, Path]] = None) -> ConfigAnalysis:
    """Load configuration from file and analyze it."""
    from tunacode.utils.user_configuration import load_config

    if config_path:
        try:
            with open(config_path, "r") as f:
                user_config = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            raise ValueError(f"Failed to load config from {config_path}: {e}")
    else:
        user_config = load_config()
        if user_config is None:
            raise ValueError("No user configuration found")

    comparator = ConfigComparator()
    return comparator.analyze_config(user_config)


def create_config_report(analysis: ConfigAnalysis) -> str:
    """Create a human-readable report of configuration analysis."""
    stats = ConfigComparator().get_summary_stats(analysis)

    report = [
        "Configuration Analysis Report",
        "=" * 50,
        f"Total keys analyzed: {stats['total_keys_analyzed']}",
        f"Custom keys: {stats['custom_keys_count']} ({stats['custom_percentage']:.1f}%)",
        f"Missing keys: {stats['missing_keys_count']}",
        f"Extra keys: {stats['extra_keys_count']}",
        f"Type mismatches: {stats['type_mismatches_count']}",
        f"Sections analyzed: {stats['sections_analyzed']}",
        f"Configuration healthy: {'Yes' if stats['has_issues'] else 'No'}",
        "",
    ]

    if analysis.custom_keys:
        report.append("Custom Values:")
        for key in sorted(analysis.custom_keys):
            report.append(f"  ✓ {key}")
        report.append("")

    if analysis.missing_keys:
        report.append("Missing Keys:")
        for key in sorted(analysis.missing_keys):
            report.append(f"  ⚠ {key}")
        report.append("")

    if analysis.type_mismatches:
        report.append("Type Mismatches:")
        for key in sorted(analysis.type_mismatches):
            report.append(f"  ✗ {key}")
        report.append("")

    recommendations = ConfigComparator().get_recommendations(analysis)
    if recommendations:
        report.append("Recommendations:")
        for rec in recommendations:
            report.append(f"  • {rec}")

    return "\n".join(report)
