"""UI-facing API surface for the TunaCode core layer.

This package contains thin facades that the UI layer imports to access
configuration, constants, and other services without depending directly on
lower-level implementation modules.

Dependency direction: ui -> core.ui_api -> (configuration/tools/infrastructure)
"""

__all__: list[str] = []
