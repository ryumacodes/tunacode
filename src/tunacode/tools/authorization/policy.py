from __future__ import annotations

from tunacode.types import ToolName

from .context import AuthContext
from .rules import AuthorizationRule


class AuthorizationPolicy:
    """Evaluate authorization rules to decide if confirmation is required."""

    def __init__(self, rules: list[AuthorizationRule]):
        self._rules = sorted(rules, key=lambda rule: rule.priority())

    def should_confirm(self, tool_name: ToolName, context: AuthContext) -> bool:
        for rule in self._rules:
            if rule.should_allow_without_confirmation(tool_name, context):
                return False
        return True
