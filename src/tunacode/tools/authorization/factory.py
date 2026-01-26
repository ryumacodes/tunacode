from __future__ import annotations

from .policy import AuthorizationPolicy
from .rules import (
    AuthorizationRule,
    ReadOnlyToolRule,
    TemplateAllowedToolsRule,
    ToolIgnoreListRule,
    YoloModeRule,
)


def create_default_authorization_policy() -> AuthorizationPolicy:
    rules: list[AuthorizationRule] = [
        ReadOnlyToolRule(),
        TemplateAllowedToolsRule(),
        YoloModeRule(),
        ToolIgnoreListRule(),
    ]
    return AuthorizationPolicy(rules)
