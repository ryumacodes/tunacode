"""Session state management.

The UI layer interacts with session state via :class:`~tunacode.core.session.StateManager`.
"""

from tunacode.core.session.state import SessionState, StateManager  # noqa: F401

__all__: list[str] = ["SessionState", "StateManager"]
