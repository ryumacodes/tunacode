"""Prompting engine for resolving {{placeholder}} syntax in prompts."""

import os
import platform
import re
from collections.abc import Callable
from datetime import datetime


class PromptingEngine:
    """Resolves {{placeholder}} syntax in prompt templates.

    Built-in placeholders:
        - {{CWD}}: Current working directory
        - {{OS}}: Operating system name
        - {{DATE}}: Current date in ISO format

    Unknown placeholders are left unchanged.
    """

    PLACEHOLDER_PATTERN = re.compile(r"\{\{(.+?)\}\}")

    def __init__(self) -> None:
        self._providers: dict[str, Callable[[], str]] = {}
        self._register_builtins()

    def _register_builtins(self) -> None:
        """Register built-in placeholder providers."""
        self._providers["CWD"] = os.getcwd
        self._providers["OS"] = platform.system
        self._providers["DATE"] = lambda: datetime.now().isoformat()

    def register(self, name: str, provider: Callable[[], str]) -> None:
        """Register a custom placeholder provider.

        Args:
            name: Placeholder name (without braces)
            provider: Callable that returns the replacement string
        """
        self._providers[name] = provider

    def resolve(self, template: str) -> str:
        """Resolve all placeholders in the template.

        Args:
            template: String containing {{placeholder}} syntax

        Returns:
            Template with resolved placeholders. Unknown placeholders
            are left unchanged.
        """
        if not template:
            return template

        def replace_match(match: re.Match[str]) -> str:
            name = match.group(1).strip()
            provider = self._providers.get(name)
            if provider is None:
                return match.group(0)
            return provider()

        return self.PLACEHOLDER_PATTERN.sub(replace_match, template)


# Module-level singleton for convenience
_engine: PromptingEngine | None = None


def get_prompting_engine() -> PromptingEngine:
    """Get the singleton prompting engine instance."""
    global _engine
    if _engine is None:
        _engine = PromptingEngine()
    return _engine


def resolve_prompt(template: str) -> str:
    """Convenience function to resolve placeholders using the singleton engine."""
    return get_prompting_engine().resolve(template)


def compose_prompt(template: str, sections: dict[str, str]) -> str:
    """Compose a prompt by replacing section placeholders with content.

    This handles the first layer of placeholder resolution (section composition).
    Use resolve_prompt() afterward for dynamic values like {{CWD}}.

    Args:
        template: Template string with {{SECTION_NAME}} placeholders
        sections: Dict mapping section names to their content

    Returns:
        Template with section placeholders replaced
    """
    result = template
    for name, content in sections.items():
        result = result.replace(f"{{{{{name}}}}}", content)
    return result
